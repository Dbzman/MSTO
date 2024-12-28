import yfinance as yf
import requests
import datetime
import logging
import json
from config import NEWS_API_KEY, DROP_LOOKBACK_DAYS

def fetch_stock_data(ticker: str, start: datetime.datetime = None, end: datetime.datetime = None):
    if end is None:
        end = datetime.datetime.today()
    if start is None:
        days = DROP_LOOKBACK_DAYS
        start = end - datetime.timedelta(days=days)
    data = yf.download(ticker, start=start, end=end, interval="1d", progress=False, multi_level_index=False)
    return pre_process_stock_data(data)

def pre_process_stock_data(data):
    data["Returns"] = data["Close"].pct_change()
    return data

def fetch_news(company_name: str):
    days = DROP_LOOKBACK_DAYS
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=days)

    url = "https://newsapi.org/v2/everything"
    params = {
        'q': company_name,
        'from': start.isoformat(),
        'to': end.isoformat(),
        'language': 'en',
        'sortBy': 'relevancy',
        'apiKey': NEWS_API_KEY,
        'pageSize': 50
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('articles', [])
    except Exception as e:
        logging.error(json.dumps({"level": "ERROR", "message": "News fetch error", "error": str(e)}))
        return []

def get_fundamental_metrics(ticker: str):
    info = yf.Ticker(ticker).info
    return {
        "pe_ratio": info.get("trailingPE", None),
        "pb_ratio": info.get("priceToBook", None)
    }
