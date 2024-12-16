import feedparser
import requests
from anthropic import Anthropic
import json
import os
from airtable import Airtable
import schedule
import time
import logging
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Replace these with your actual API keys and tokens
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

# RSS feed URL
RSS_URL = os.getenv('RSS_URL')

# Airtable details
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')

def get_rss_feed():
    feed = feedparser.parse(RSS_URL)
    return feed.entries[:25]  # Get the latest 5 entries

def perplexity_analysis(url):
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-sonar-large-128k-online",
        "messages": [
            {
                "role": "user",
                "content": f"url: {url}\nCreate a summary on which I could base my trades on."
            }
        ],
        "max_tokens": 3000
    }
    response = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

def anthropic_analysis(perplexity_content, title, description):
    print("Analyzing article")
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""

Perplexity object: {perplexity_content}

Title: {title}
Description: {description}
Symbols list: NASDAQ and SP500"""
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        system="Based on the news article, provide json with a trading 'decision' (strong buy, buy, strong sell, sell, or hold), symbol (maximum 1 related symbols from list, return nothing with hold decision if doesn't work with any of the stocks) and a brief 'explanation'. Return it all in json format. RETURN NOTHING ELSE!",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "{"
                    }
                ]
            }
        ],
        max_tokens=3000
    )
    print(response.content[0].text)
    return '{' + response.content[0].text

def parse_json(json_string):
    return json.loads(json_string)

def create_airtable_record(entry, perplexity_content, decision_data):
    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    record = {
        "Title": entry.title,
        "URL": entry.link,
        "Description": entry.description if hasattr(entry, 'description') else "",
        "Decision": decision_data.get("decision"),
        "Symbol": decision_data.get("symbol"),
        "Summary": decision_data.get("explanation"),
        "Perplexity": perplexity_content
    }
    airtable.insert(record)

def is_new_entry(entry):
    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    existing_records = airtable.search('URL', entry.link)
    return len(existing_records) == 0

def process_feed():
    logging.info("Starting feed processing")
    try:
        entries = get_rss_feed()
        for entry in entries:
            try:
                description = entry.description if hasattr(entry, 'description') else ""
                
                if is_new_entry(entry):
                    perplexity_content = perplexity_analysis(entry.link)
                    anthropic_response = anthropic_analysis(perplexity_content, entry.title, description)
                    decision_data = parse_json(anthropic_response)
                    create_airtable_record(entry, perplexity_content, decision_data)
                    logging.info(f"Processed new article: {entry.title}")
                else:
                    logging.info(f"Skipped existing article: {entry.title}")
            except Exception as e:
                logging.error(f"Error processing entry {entry.title}: {str(e)}")
    except Exception as e:
        logging.error(f"Error in process_feed: {str(e)}")
    logging.info("Finished feed processing")

def main():
    logging.info("Starting the news analysis script")
    process_feed()
    schedule.every(1).minutes.do(process_feed)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
