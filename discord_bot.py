import os

import discord
from discord import app_commands

from data_manager import DataManager
from logger import Logger
from utils import fetch_product_data, get_current_time, get_product_name

from dotenv import load_dotenv

from watch_stock_cron import check_watch_stocks

load_dotenv()


class Bot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        Logger.info("Command tree synced")


client = Bot()
data_manager = DataManager()


@client.tree.command(name="watch", description="Get notified when a product is back in stock")
async def watch(interaction: discord.Interaction, product_url: str):
    Logger.info(f"Received watch request for: {product_url}")
    await interaction.response.defer(thinking=True)

    if data_manager.product_exists(product_url):
        Logger.warn(f"Product already being watched: {product_url}")
        embed = discord.Embed(
            title="🔔 Already Watching",
            description=f"Already watching [{get_product_name(product_url)}]({product_url})",
            color=0xffcc00  # Yellow for existing watch
        )
        await interaction.followup.send(embed=embed)
    else:
        data_manager.add_product_url(product_url)
        Logger.info(f"Started watching product: {product_url}")
        embed = discord.Embed(
            title="✅ Now Watching",
            description=f"Started watching [{get_product_name(product_url)}]({product_url}). Will notify you when it's back in stock.",
            color=0x00ff00
        )
        await interaction.followup.send(embed=embed)


@client.tree.command(name="get_watched", description="Get all watched product URLs")
async def get_watched(interaction: discord.Interaction):
    Logger.info("Fetching all watched products")
    await interaction.response.defer(thinking=True)

    watched_products = data_manager.get_all_product_urls()
    Logger.debug(f"Watched products retrieved: {watched_products}")
    if watched_products:
        response = "\n".join([f"{i + 1}. [{get_product_name(url)}]({url})" for i, url in enumerate(watched_products)])
        embed = discord.Embed(
            title="📋 Watched Products",
            description=response,
            color=0x00ccff
        )
    else:
        Logger.warn("No products are being watched")
        embed = discord.Embed(
            title="🚫 No Watched Products",
            description="🚫 No products are currently being watched.",
            color=0xff0000
        )

    await interaction.followup.send(embed=embed)


@client.tree.command(name="unwatch", description="Stop watching a product")
async def unwatch(interaction: discord.Interaction, product_url: str):
    Logger.info("Received unwatch request", product_url)
    await interaction.response.defer(thinking=True)

    product_name = get_product_name(product_url)
    if not data_manager.product_exists(product_url):
        Logger.warn("Tried to unwatch a product that's not being watched", product_url)
        embed = discord.Embed(
            title="🚫 Not Watching",
            description=f"[{product_name}]({product_url}) is not being watched.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)
    else:
        data_manager.remove_product_url(product_url)
        Logger.info('Stopped watching product', product_url)
        embed = discord.Embed(
            title="✅ Stopped Watching",
            description=f"Stopped watching [{product_name}]({product_url})",
            color=0x00ff00
        )
        await interaction.followup.send(embed=embed)


@client.tree.command(name="check_stock", description="Check the current stock level of a product")
async def check_stock(interaction: discord.Interaction, product_url: str):
    Logger.info('Checking stock for product', product_url)
    await interaction.response.send_message("🔍 Checking stock levels, please wait...")

    try:
        data = await fetch_product_data(product_url)
        embed = discord.Embed(title=data['name'], url=data['product_url'], color=0x00ff00)

        for option in data['options']:
            embed.add_field(
                name='Variant',
                value=f'[{option["name"]}]({option["url"]})',
                inline=True
            )
            embed.add_field(
                name='Stock',
                value=f"{option['stockLevel']} - {option['stockLevelStatus']}",
                inline=True
            )
            embed.add_field(
                name='\u200b',
                value='\u200b',
                inline=False
            )

        embed.set_footer(text=f"🕒 Time: {get_current_time()} (UK)")

        await interaction.edit_original_response(content=f"🔍 Stock Check Result for {data['name']}\n", embed=embed)
    except Exception as err:
        Logger.error(f'Error occurred while fetching stock details for {product_url}', err)

        embed = discord.Embed(
            title="Error",
            description="⚠️ Unable to retrieve product data. Please make sure the link is correct. [Contact Developer](https://chanpreet-portfolio.vercel.app/#connect)",
            color=0xff0000
        )
        await interaction.edit_original_response(embed=embed)
    finally:
        Logger.info('Finished checking stock for product', product_url)


@client.tree.command(name="clear_all", description="Clear all watched products")
async def clear_all(interaction: discord.Interaction):
    Logger.info("Received clear all request")
    await interaction.response.defer(thinking=True)

    watched_products = data_manager.get_all_product_urls()
    if not watched_products:
        Logger.warn("No products to clear")
        embed = discord.Embed(
            title="🚫 No Watched Products",
            description="There are no products currently being watched.",
            color=0xff0000
        )
    else:
        product_len = len(watched_products)
        data_manager.clear_all_products()
        Logger.info('Cleared all watched products')
        embed = discord.Embed(
            title="✅ All Watches Cleared",
            description=f"Stopped watching all {product_len} products.",
            color=0x00ff00
        )

    await interaction.followup.send(embed=embed)


@client.tree.command(name="set_channel", description="Set the channel for stock notifications")
@app_commands.checks.has_permissions(administrator=True)
async def set_channel(interaction: discord.Interaction):
    Logger.info(f"Setting notification channel: {interaction.channel.id}")
    data_manager.set_notification_channel(interaction.channel.id)

    embed = discord.Embed(
        title="✅ Notification Channel Set",
        description=f"This channel will now receive stock notifications.",
        color=0x00ff00
    )
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="check_all_stocks", description="Manually trigger stock check for all watched products")
async def check_all_stocks(interaction: discord.Interaction):
    Logger.info("Manually triggered stock check for all products")
    await interaction.response.defer(thinking=True)

    await check_watch_stocks(client)
    await interaction.followup.send("✅ Stock check completed for all watched products.")


@client.event
async def on_ready():
    Logger.debug(f'Logged in successfully! Bot is now online & ready to use: {client.user}')
    await client.tree.sync()


def init_bot():
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    client.run(discord_token)
