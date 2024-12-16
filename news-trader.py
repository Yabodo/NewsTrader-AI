import requests
from airtable import Airtable
import schedule
import time
import logging
from datetime import datetime, timedelta
from dateutil import parser
import pytz
import os
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Alpaca API credentials
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_API_SECRET = os.getenv('ALPACA_API_SECRET')
ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL')

# Airtable credentials
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_NEWS_TABLE = os.getenv('AIRTABLE_NEWS_TABLE')
AIRTABLE_ORDERS_TABLE = os.getenv('AIRTABLE_ORDERS_TABLE')

def get_latest_news():
    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_NEWS_TABLE, api_key=AIRTABLE_API_KEY)
    # Get records created in the last 5 minutes
    formula = f"NOT({{Processed}})"
    records = airtable.get_all(formula=formula)
    return records

def is_market_open():
    url = f"{ALPACA_BASE_URL}/v2/clock"
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_API_SECRET
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['is_open']
    else:
        logging.error(f"Failed to check market status: {response.text}")
        return False

def place_order(symbol, side, notional):
    url = f"{ALPACA_BASE_URL}/v2/orders"
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_API_SECRET,
        "Content-Type": "application/json"
    }
    data = {
        "symbol": symbol,
        "side": side,
        "type": "market",
        "time_in_force": "day",
        "notional": notional
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def record_order(symbol, order_size, summary, order_type, order_id):
    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_ORDERS_TABLE, api_key=AIRTABLE_API_KEY)
    record = {
        "Symbol": symbol,
        "Order size": order_size,
        "Summary": summary,
        "Type": order_type,
        "Order ID": order_id,
    }
    airtable.insert(record)

def mark_as_processed(record_id):
    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_NEWS_TABLE, api_key=AIRTABLE_API_KEY)
    airtable.update(record_id, {"Processed": True})

def close_position(symbol):
    url = f"{ALPACA_BASE_URL}/v2/positions/{symbol}"
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_API_SECRET
    }
    response = requests.delete(url, headers=headers)
    return response.status_code == 404

def check_and_close_positions():
    if not is_market_open():
        logging.info("Market is closed. Skipping position check and closure.")
        return

    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_ORDERS_TABLE, api_key=AIRTABLE_API_KEY)
    now = datetime.now(pytz.UTC)
    
    # Get all unclosed positions
    formula = "NOT({Closed})"
    records = airtable.get_all(formula=formula)
    
    for record in records:
        symbol = record['fields'].get('Symbol')
        created_time_str = record['fields'].get('Last Modified')
        
        if not created_time_str:
            logging.warning(f"Position for {symbol} has no creation time. Skipping.")
            continue
        
        created_time = parser.parse(created_time_str).astimezone(pytz.UTC)
        position_age = now - created_time
        
        if position_age >= timedelta(hours=3):
            if close_position(symbol):
                airtable.update(record['id'], {"Closed": True})
                logging.info(f"Closed position for {symbol}")
            else:
                logging.error(f"Failed to close position for {symbol}")

def process_feed():
    check_and_close_positions()
    news_records = get_latest_news()
    
    if not news_records:
        logging.info("No unprocessed records found.")
        return

    for record in news_records:
        symbol = record['fields'].get('Symbol')
        decision = record['fields'].get('Decision', [])
        summary = record['fields'].get('Summary', '')
        
        if not symbol or not decision:
            continue
        
        decision = decision[0].lower() if isinstance(decision, list) else decision.lower()
        
        logging.info(f"Processing decision {decision} for {symbol}.")
        if decision in ['buy', 'strong buy']:
            order_response = place_order(symbol, 'buy', 10000)
            if 'id' in order_response:
                record_order(symbol, 10000, summary, 'Buy', order_response['id'])
                logging.info(f"Bought {symbol} for $10000")
                mark_as_processed(record['id'])
            else:
                logging.error(f"Failed to buy {symbol}: {order_response}")
                if order_response.get('code') == 40310000 or order_response.get('code') == 42210000 or order_response.get('error') == "Market is closed":
                    logging.info(f"Marked {symbol} as processed")
                    mark_as_processed(record['id'])
        
        elif decision in ['sell', 'strong sell']:
            order_response = place_order(symbol, 'sell', 10000)
            if 'id' in order_response:
                record_order(symbol, 10000, summary, 'Sell', order_response['id'])
                logging.info(f"Sold {symbol} for $10000")
                mark_as_processed(record['id'])
            else:
                logging.error(f"Failed to sell {symbol}: {order_response}")
                if order_response.get('code') == 40310000 or order_response.get('code') == 42210000 or order_response.get('error') == "Market is closed":
                    logging.info(f"Marked {symbol} as processed")
                    mark_as_processed(record['id'])

def main():
    logging.info("Starting the airtable trading script")
    process_feed()  # Process immediately when starting
    schedule.every(1).minutes.do(process_feed)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()