import datetime
import logging
import json
import concurrent.futures
import time
from typing import List, Dict, Set

from msto.utils.config import load_config
from msto.core.data_sources import fetch_stock_data, fetch_news, get_fundamental_metrics
from msto.core.analytics import detect_unusual_drop, sentiment_analysis, classify_events, estimate_impact
from msto.core.execution import TradingViewIntegration
from msto.core.health import start_health_server, update_health_status
from msto.strategies.base import Strategy

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, strategies: List[Strategy]):
        """
        Initialize orchestrator with multiple strategies (like multiple microservices).
        """
        self.strategies = strategies
        self.executor = TradingViewIntegration()
        self.config = load_config()
        self.drop_lookback_days = int(self.config["DROP_LOOKBACK_DAYS"])
        self.check_interval = int(self.config.get("CHECK_INTERVAL_SECONDS", 300))
        self.processed_signals: Dict[str, Set[str]] = {}
        self.max_signals_per_ticker = int(self.config.get("MAX_SIGNALS_PER_TICKER", 3))
        self.health_port = int(self.config.get("HEALTH_CHECK_PORT", 8080))
        self.health_server = None

    def start_monitoring(self, tickers: List[str]):
        """
        Start continuous monitoring of the given tickers.
        
        Args:
            tickers: List of stock tickers to monitor
        """
        # Start health check server
        self.health_server = start_health_server(self.health_port)
        update_health_status("starting")
        
        logger.info(json.dumps({
            "level": "INFO",
            "message": "Starting continuous monitoring",
            "tickers": tickers,
            "check_interval": self.check_interval
        }))
        
        try:
            update_health_status("healthy")
            while True:
                try:
                    self.process_all_tickers(tickers)
                    time.sleep(self.check_interval)
                except Exception as e:
                    logger.error(json.dumps({
                        "level": "ERROR",
                        "message": "Error in monitoring loop",
                        "error": str(e)
                    }))
                    update_health_status("unhealthy", str(e))
                    # Continue monitoring despite errors
                    time.sleep(self.check_interval)
                    
        except KeyboardInterrupt:
            logger.info(json.dumps({
                "level": "INFO",
                "message": "Monitoring stopped by user"
            }))
            update_health_status("stopping")
        finally:
            if self.health_server:
                self.health_server.shutdown()

    def process_all_tickers(self, tickers: List[str]):
        """Process all tickers in parallel."""
        max_workers = min(len(tickers), int(self.config.get("MAX_PARALLEL_TICKERS", 10)))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.process_ticker, ticker): ticker for ticker in tickers}
            for future in concurrent.futures.as_completed(futures):
                ticker = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(json.dumps({
                        "level": "ERROR",
                        "message": "Error processing ticker",
                        "ticker": ticker,
                        "error": str(e)
                    }))

    def process_ticker(self, ticker: str):
        """Process a single ticker and generate trading signals."""
        logger.info(json.dumps({
            "level": "INFO",
            "message": "Processing ticker",
            "ticker": ticker,
            "timestamp": datetime.datetime.now().isoformat()
        }))

        # Initialize signal tracking for this ticker if not exists
        if ticker not in self.processed_signals:
            self.processed_signals[ticker] = set()

        # Check if market is open (if configured)
        if self.config.get("MARKET_HOURS_ONLY", "true").lower() == "true":
            if not self._is_market_open():
                logger.debug(json.dumps({
                    "level": "DEBUG",
                    "message": "Market is closed",
                    "ticker": ticker
                }))
                return

        # Fetch and validate data
        data = fetch_stock_data(ticker, self.drop_lookback_days)
        if data.empty:
            logger.info(json.dumps({
                "level": "INFO",
                "message": "No data for ticker",
                "ticker": ticker
            }))
            return

        drop = detect_unusual_drop(data)
        if drop is None:
            logger.debug(json.dumps({
                "level": "DEBUG",
                "message": "No unusual drop detected",
                "ticker": ticker
            }))
            return

        # Gather market data
        today = datetime.date.today()
        from_date = today - datetime.timedelta(days=2)
        articles = fetch_news(ticker, from_date, today)

        avg_sent = sentiment_analysis(articles)
        event_type = classify_events(articles)
        fundamentals = get_fundamental_metrics(ticker)
        impact = estimate_impact(avg_sent, event_type)

        processed_data = {
            "ticker": ticker,
            "drop": drop,
            "avg_sentiment": avg_sent,
            "most_common_event": event_type,
            "fundamentals": fundamentals,
            "impact": impact,
            "timestamp": datetime.datetime.now().isoformat()
        }

        # Run strategies in parallel
        all_signals = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.strategies)) as executor:
            future_to_strategy = {executor.submit(s.process_data, processed_data): s for s in self.strategies}
            for future in concurrent.futures.as_completed(future_to_strategy):
                strategy_obj = future_to_strategy[future]
                try:
                    signals = future.result()
                    if signals:
                        # Filter out already processed signals
                        new_signals = []
                        for signal in signals:
                            signal_id = f"{signal['strategy']}_{signal['action']}_{signal['quantity']}"
                            if signal_id not in self.processed_signals[ticker]:
                                if len(self.processed_signals[ticker]) < self.max_signals_per_ticker:
                                    self.processed_signals[ticker].add(signal_id)
                                    new_signals.append(signal)
                                else:
                                    logger.warning(json.dumps({
                                        "level": "WARNING",
                                        "message": "Maximum signals reached for ticker",
                                        "ticker": ticker,
                                        "max_signals": self.max_signals_per_ticker
                                    }))
                        all_signals.extend(new_signals)
                except Exception as e:
                    logger.error(json.dumps({
                        "level": "ERROR",
                        "message": "Strategy processing error",
                        "strategy": strategy_obj.__class__.__name__,
                        "error": str(e)
                    }))

        # Execute new signals
        if all_signals:
            self.executor.execute_signals(all_signals)

    def reset_signal_tracking(self, ticker: str = None):
        """Reset signal tracking for a specific ticker or all tickers."""
        if ticker:
            self.processed_signals[ticker] = set()
        else:
            self.processed_signals.clear()

    def _is_market_open(self) -> bool:
        """Check if the market is currently open."""
        now = datetime.datetime.now()
        # Basic check for US market hours (9:30 AM - 4:00 PM ET)
        # TODO: Add proper market calendar integration
        if now.weekday() >= 5:  # Weekend
            return False
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        return market_open <= now <= market_close
