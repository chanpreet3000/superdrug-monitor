from data_manager import DataManager
from logger import Logger
from utils import get_current_time, fetch_product_data
import discord

data_manager = DataManager()


async def check_watch_stocks(client):
    Logger.info("Checking stock for watched products")
    watched_products = data_manager.get_all_product_urls().copy()

    for product_url in watched_products:
        try:
            data = await fetch_product_data(product_url)
            in_stock = any(option['stockLevelStatus'] == 'In Stock' for option in data['options'])

            if in_stock:
                embed = create_stock_embed(data)
                await notify_users(client, embed)
                data_manager.remove_product_url(product_url)

        except Exception as err:
            Logger.error(f"Error checking stock for {product_url}", err)
            error_embed = discord.Embed(
                title="Error Checking Stock",
                description=f"An error occurred while checking stock for {product_url}\nError: {err}",
                color=0xff0000
            )
            await notify_users(client, error_embed)


def create_stock_embed(data):
    embed = discord.Embed(title=data['name'], url=data['product_url'], color=0x00ff00)
    embed.set_thumbnail(url=data['image'])

    for option in data['options']:
        if option['stockLevelStatus'] == 'In Stock':
            embed.add_field(
                name='Variant',
                value=f"[{option['name']}]({option['url']})",
                inline=True
            )
            embed.add_field(
                name='Stock',
                value=f"{option['stockLevel']} - {option['stockLevelStatus']}",
                inline=True
            )
            embed.add_field(name='\u200b', value='\u200b', inline=False)

    embed.set_footer(text=f"🕒 Time: {get_current_time()} (UK)")
    return embed


async def notify_users(client, embed):
    channel_id = data_manager.get_notification_channel()
    if channel_id:
        channel = client.get_channel(channel_id)
        if channel:
            await channel.send(content="@here Product is now in stock!", embed=embed)
