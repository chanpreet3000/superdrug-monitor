# Discord Stock Checker Bot

A Discord bot that allows users to watch and check stock levels for products.

## Features

- Watch products for stock updates
- List watched products
- Unwatch products
- Check current stock levels

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in a `.env` file:
   ```
   DISCORD_BOT_TOKEN=your_bot_token_here
   ```
4. Run the bot: `python main.py`

## Usage

Use Discord slash commands:
- `/watch <product_url>`
- `/get_watched`
- `/unwatch <product_url>`
- `/check_stock <product_url>`

## Dependencies

- discord.py
- playwright
- python-dotenv
- pytz