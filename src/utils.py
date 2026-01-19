import json
import os
import logging

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
PROCESSED_TWEETS_FILE = os.path.join(DATA_DIR, 'processed_tweets.json')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_processed_tweets():
    if not os.path.exists(PROCESSED_TWEETS_FILE):
        return []
    with open(PROCESSED_TWEETS_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_processed_tweets(tweet_ids):
    # Ensure unique and sorted
    unique_ids = sorted(list(set(tweet_ids)))
    # Keep only last 1000 to prevent infinite growth
    if len(unique_ids) > 1000:
        unique_ids = unique_ids[-1000:]
        
    with open(PROCESSED_TWEETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_ids, f, indent=2)

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
