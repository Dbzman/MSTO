from typing import Dict, List
from strategies.strategy import Strategy


class SimpleVolatilityStrategy(Strategy):
    def process_data(self, processed_data: Dict) -> List[Dict]:
        signals = []
        drop = processed_data.get('drop', 0)
        sentiment = processed_data.get('avg_sentiment', 0.0)
        ticker = processed_data.get('ticker', 'UNKNOWN')

        # Very simplistic logic
        if drop < -2 and sentiment < -0.5:
            signals.append({"symbol": ticker, "action": "BUY", "quantity": 10})
        return signals