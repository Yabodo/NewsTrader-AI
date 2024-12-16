# NewsTrader AI 🤖📈

An automated trading system that analyzes financial news using AI and executes trades based on sentiment analysis.

## Overview

NewsTrader AI combines the power of multiple AI models (Claude and Perplexity) to analyze financial news in real-time and execute automated trading decisions through Alpaca Markets. The system monitors RSS feeds for financial news, processes the content through AI analysis, and makes trading decisions based on the AI's interpretation.

## Features

- 🔄 Real-time RSS feed monitoring
- 🧠 Dual AI analysis pipeline (Perplexity + Claude)
- 📊 Automated trading execution via Alpaca Markets
- 📝 Trade logging and tracking in Airtable
- ⏰ Automatic position management (3-hour holding period)
- 🔐 Secure environment variable configuration

## System Architecture

The system consists of two main components:

1. **News Analyzer** (`news-analyzer.py`)
   - Monitors RSS feeds for new financial news
   - Processes articles through Perplexity AI for initial analysis
   - Uses Claude AI for trading decision generation
   - Stores results in Airtable

2. **News Trader** (`news-trader.py`)
   - Monitors Airtable for new trading signals
   - Executes trades through Alpaca Markets API
   - Manages positions and handles market timing
   - Records trading activity

## Prerequisites

- Python 3.8+
- Airtable account
- Alpaca Markets account
- Anthropic API key (Claude)
- Perplexity API key

## Installation

1. Clone the repository:

git clone https://github.com/yourusername/newstrader-ai.git
cd newstrader-ai

2. Install required packages:

pip install -r requirements.txt


3. Set up your environment variables in `.env`:

PERPLEXITY_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
AIRTABLE_API_KEY=your_key_here
AIRTABLE_BASE_ID=your_base_id
AIRTABLE_NEWS_TABLE=your_table_name
AIRTABLE_ORDERS_TABLE=your_table_name
ALPACA_API_KEY=your_key_here
ALPACA_API_SECRET=your_secret_here
ALPACA_BASE_URL=your_url_here
RSS_URL=your_rss_feed_url

## Usage

1. Start the news analyzer:

python news-analyzer.py

2. Start the trader:

python news-trader.py

## Trading Logic

- The system makes trading decisions based on AI analysis with five possible outcomes:
  - Strong Buy
  - Buy
  - Hold
  - Sell
  - Strong Sell
- Each trade is executed with a fixed notional value of $10,000
- Positions are automatically closed after 3 hours
- Trading only occurs during market hours

## Safety Features

- Market hours verification before trading
- Error handling for API failures
- Logging system for monitoring and debugging
- Position management safeguards

## Disclaimer

This is an experimental trading system. Use at your own risk. The creators are not responsible for any financial losses incurred through the use of this system.

## License

This project is licensed under the Proprietary License. All rights reserved. Unauthorized copying, distribution, or modification of this project is strictly prohibited.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.