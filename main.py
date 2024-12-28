import logging
from msto.core.orchestrator import Orchestrator
from msto.strategies.fundamental_event_driven import FundamentalEventDrivenStrategy
from msto.strategies.simple_volatility import SimpleVolatilityStrategy

def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    # Instantiate multiple strategies like separate microservices
    strategies = [
        SimpleVolatilityStrategy(),
        FundamentalEventDrivenStrategy()
    ]

    orchestrator = Orchestrator(strategies)
    tickers = ["AAPL", "MSFT"]
    for ticker in tickers:
        orchestrator.process_ticker(ticker)


if __name__ == "__main__":
    main()
