import numpy as np
from typing import List, Dict, Any
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from collections import Counter
import re

# Download required NLTK data
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

def detect_unusual_drop(data: pd.DataFrame) -> float:
    returns = data['Close'].pct_change() * 100
    if len(returns.dropna()) < 10:
        return None
    recent_return = returns.iloc[-1]
    mu = returns.mean()
    sigma = returns.std()
    threshold = mu - 2 * sigma
    if recent_return < threshold:
        return float(recent_return)
    return None

def sentiment_analysis(articles: List[Dict[str, Any]]) -> float:
    if not articles:
        return 0.0
    
    sia = SentimentIntensityAnalyzer()
    sentiments = []
    
    for article in articles:
        text = f"{article.get('title', '')} {article.get('description', '')}"
        if not text.strip():
            continue
        
        sentiment_scores = sia.polarity_scores(text)
        sentiments.append(sentiment_scores['compound'])
    
    return np.mean(sentiments) if sentiments else 0.0

def classify_events(articles: List[Dict[str, Any]]) -> str:
    if not articles:
        return "no_news"
    
    # Define event keywords
    event_patterns = {
        'earnings': r'earnings|revenue|profit|loss|quarterly|financial results',
        'merger_acquisition': r'merger|acquisition|takeover|deal|buyout',
        'management_change': r'CEO|executive|management|leadership|appointed|resigned',
        'product_launch': r'launch|release|announce|new product|innovation',
        'legal': r'lawsuit|legal|court|settlement|regulatory',
        'market_movement': r'market|stock|shares|trading|investors'
    }
    
    event_counts = Counter()
    
    for article in articles:
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        
        for event_type, pattern in event_patterns.items():
            if re.search(pattern, text):
                event_counts[event_type] += 1
    
    if not event_counts:
        return "other"
    
    return event_counts.most_common(1)[0][0]

def estimate_impact(sentiment: float, event_type: str) -> float:
    # Event type weights
    event_weights = {
        'earnings': 1.0,
        'merger_acquisition': 0.8,
        'management_change': 0.6,
        'product_launch': 0.5,
        'legal': 0.7,
        'market_movement': 0.4,
        'other': 0.3,
        'no_news': 0.1
    }
    
    # Calculate impact score (-1 to 1)
    event_weight = event_weights.get(event_type, 0.3)
    impact = sentiment * event_weight
    
    # Ensure the impact is within bounds
    return max(min(impact, 1.0), -1.0)
