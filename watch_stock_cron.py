import discord
from data_manager import DataManager
from Logger import Logger
from utils import fetch_product_data

data_manager = DataManager()


async def check_watch_stocks(client: discord.Client):
    watched_products = data_manager.get_all_product_urls().copy()
    Logger.info(f"Starting stock check for {len(watched_products)} watched products")

    for product_url in watched_products:
        Logger.info('Checking stock for', product_url)
        embed, product_data = fetch_product_data(product_url)
        if product_data is None:
            Logger.error(f"Failed to fetch product data for {product_url}")
            await notify_users(client, embed, '@here Failed to fetch product data. Removing from watch list.')
            data_manager.remove_product_url(product_url)
            continue

        in_stock = any(option.is_in_stock for option in product_data.options)
        if in_stock:
            Logger.info(f"Product is in stock: {product_url}")
            await notify_users(client, embed, '@here Product is now in stock!. Removing from watch list.')
            data_manager.remove_product_url(product_url)
        else:
            Logger.info(f"Product is not in stock: {product_url}")


async def notify_users(client: discord.Client, embed: discord.Embed, message: str):
    channel_ids = data_manager.get_notification_channels()

    if not channel_ids:
        Logger.warn("No notification channels configured")
        return

    for channel_id in channel_ids:
        channel = client.get_channel(int(channel_id))
        try:
            if channel:
                Logger.info(f"Sending notification to channel: {channel_id} with message {message}")
                await channel.send(message, embed=embed)
            else:
                Logger.error(f"Could not find channel with ID: {channel_id}")
        except Exception as err:
            Logger.error(f"Failed to send notification to channel {channel_id}: {err}")
