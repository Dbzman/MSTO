# Market Sentiment Trading Orchestrator (MSTO)

A sophisticated trading system that monitors stock market movements, analyzes news sentiment, and executes trades based on multiple strategies.

## Features

- Real-time stock price monitoring
- News sentiment analysis using NLTK
- Event classification and impact estimation
- Multiple trading strategies support
- TradingView integration for execution
- Parallel strategy processing

## Project Structure

```
msto/
├── core/                   # Core functionality
│   ├── analytics.py       # Market analysis and sentiment
│   ├── data_sources.py    # Data fetching utilities
│   ├── execution.py       # Trade execution
│   └── orchestrator.py    # Main coordination logic
├── strategies/            # Trading strategies
│   ├── base.py           # Strategy base class
│   └── fundamental_event_driven.py
├── utils/                 # Utility modules
│   └── config.py         # Configuration management
└── cli.py                # Command-line interface

tests/
├── unit/                 # Unit tests
├── integration/          # Integration tests
└── conftest.py          # Test configuration
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/MSTO.git
cd MSTO
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e .
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.local .env
```

2. Edit `.env` with your configuration:
```env
ENV=dev
TRADING_MODE=paper
TRADINGVIEW_WEBHOOK_URL=your_webhook_url
NEWS_API_KEY=your_newsapi_key
DB_CONNECTION_STRING=your_db_connection
```

## Usage

Run the orchestrator with specific tickers:
```bash
msto --tickers AAPL MSFT GOOGL
```

Additional options:
```bash
msto --config custom_config.env --log-level DEBUG --tickers AAPL
```

## Development

1. Install development dependencies:
```bash
pip install -e ".[dev]"
```

2. Run tests:
```bash
pytest tests/
```

3. Run linting:
```bash
flake8 msto tests
```

## Adding New Strategies

1. Create a new strategy class in `msto/strategies/`
2. Inherit from `Strategy` base class
3. Implement the `process_data` method
4. Add strategy initialization to `cli.py`

Example:
```python
from msto.strategies.base import Strategy

class MyNewStrategy(Strategy):
    def process_data(self, data):
        # Implement strategy logic
        pass
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

See LICENSE file for details.
