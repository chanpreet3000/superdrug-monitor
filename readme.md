# Stock Watch Discord Bot

This Discord bot allows users to watch for stock availability of products and receive notifications when they become
available.

## Bot Commands

1. `/watch <product_url>`: Start watching a product for stock availability.
2. `/unwatch <product_url>`: Stop watching a specific product.
3. `/get_watched`: Get a list of all watched product URLs.
4. `/check_stock <product_url>`: Check the current stock level of a product.
5. `/clear_all`: Clear all watched products.
6. `/set_channel`: Set the current channel for stock notifications (admin only).
7. `/check_all_stocks`: Manually trigger stock check for all watched products.

## Installation on EC2 Instance (Ubuntu)

1. Connect to your EC2 instance:
   ```
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

2. Update and install required packages:
   ```
   sudo apt update
   sudo apt install python3-pip python3-venv
   ```

3. Clone the repository:
   ```
   git clone https://github.com/chanpreet3000/superdrug-monitor
   cd superdrug-monitor
   ```

4. Create and activate a virtual environment:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```

5. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

6. Create a `.env` file:
   ```
   nano .env
   ```
   Add the following content:
   ```
   DISCORD_BOT_TOKEN=your_discord_bot_token
   WATCH_PRODUCT_CRON_DELAY_SECONDS=3600
   ```
   Replace `your_discord_bot_token` with your actual Discord bot token.

7. Run the bot:
   ```
   xvfb-run python3 main.py
   ```

To keep the bot running after you close the SSH session, you can use a process manager like `screen` or `tmux`.

For example, using `screen`:

```
screen -S stockbot
pkill Xvfb
source .venv/bin/activate
xvfb-run python3 main.py
```

Then press `Ctrl+A` followed by `D` to detach from the screen session.

To reattach to the session later:

```
screen -r stockbot
```

Remember to set up proper security groups and firewall rules for your EC2 instance to allow incoming Discord bot
traffic.