import datetime

import pandas
from msto.core.analytics import detect_unusual_drop
from msto.core.data_sources import fetch_stock_data
from msto.strategies.mean_reversion_strategy import MeanReversionStrategy

class Backtest:
    def __init__(self, strategy, ticker, start_date, end_date):
        self.strategy = strategy
        self.ticker = ticker
        self.start_date = pandas.to_datetime(start_date)
        self.end_date = pandas.to_datetime(end_date)
        self.results = []
        self.initial_cash = 100000  # Initial cash for the portfolio
        self.portfolio_value = self.initial_cash
        self.buy_and_hold_value = self.initial_cash

    def run(self):
        print(f"Running backtest for {self.ticker} from {self.start_date} to {self.end_date}")
        data = fetch_stock_data(self.ticker, self.start_date, self.end_date)
        initial_price = data.loc[self.start_date]['Close']
        shares_bought = self.initial_cash / initial_price

        for date, row in data.iterrows():
            if date < self.start_date or date > self.end_date:
                continue
            data_up_to_date = data.loc[:date]
            drop = detect_unusual_drop(data_up_to_date)
            signal = self.strategy.process_data({
                'ticker': self.ticker,
                'drop': drop,
                'avg_sentiment': 0,  # Placeholder for sentiment data
                'most_common_event': '',  # Placeholder for event data
                'fundamentals': {},  # Placeholder for fundamental data
                'impact': 0  # Placeholder for impact data
            })
            if signal:
                self.results.append((date, signal))
                # Example: Buy or sell based on the signal
                if signal[0]["action"] == 'BUY':
                    self.portfolio_value += row['Close'] * signal[0]["quantity"]
                elif signal == 'sell':
                    self.portfolio_value -= row['Close'] * shares_bought

        final_price = data.iloc[-1]['Close']
        self.buy_and_hold_value = shares_bought * final_price

    def get_results(self):
        return self.results

    def print_returns(self):
        strategy_return = (self.portfolio_value - self.initial_cash) / self.initial_cash * 100
        buy_and_hold_return = (self.buy_and_hold_value - self.initial_cash) / self.initial_cash * 100
        print(f"Strategy Return: {strategy_return:.2f}%")
        print(f"Buy and Hold Return: {buy_and_hold_return:.2f}%")

# Example usage
if __name__ == "__main__":
    print("Running backtest example")
    days = 365  # Example lookback period
    end = datetime.datetime.today().date()
    start = end - datetime.timedelta(days=days)
    strategy = MeanReversionStrategy()
    backtest = Backtest(strategy, 'TSLA', start, end)
    backtest.run()
    results = backtest.get_results()
    for result in results:
        print(result)
    backtest.print_returns()
