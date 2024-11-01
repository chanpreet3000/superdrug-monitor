import asyncio
import os

import discord
from discord import app_commands
from discord.ext import tasks

from data_manager import DataManager
from Logger import Logger
from utils import fetch_product_data, get_product_name

from dotenv import load_dotenv

from watch_stock_cron import check_watch_stocks

load_dotenv()

watch_product_cron_delay_seconds = int(os.getenv('WATCH_PRODUCT_CRON_DELAY_SECONDS', 60 * 60))


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


@client.tree.command(name="sdm_watch", description="Get notified when a product is back in stock")
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


@client.tree.command(name="sdm_get_watched", description="Get all watched product URLs")
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
            description="No products are currently being watched.",
            color=0xff0000
        )

    await interaction.followup.send(embed=embed)


@client.tree.command(name="sdm_unwatch", description="Stop watching a product")
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


@client.tree.command(name="sdm_check_stock", description="Check the current stock level of a product")
async def check_stock(interaction: discord.Interaction, product_url: str):
    Logger.info('Checking stock for product', product_url)
    await interaction.response.send_message("🔍 Checking stock levels, please wait...")

    embed, _ = fetch_product_data(product_url)
    await interaction.edit_original_response(content=f"🔍 Stock Check Result Completed",
                                             embed=embed)
    Logger.info('Finished checking stock for product', product_url)


@client.tree.command(name="sdm_clear_all", description="Clear all watched products")
@app_commands.checks.has_permissions(administrator=True)
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


@client.tree.command(name="sdm_add_channel", description="Add a notification channel")
@app_commands.checks.has_permissions(administrator=True)
async def add_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    Logger.info(f"Received add channel request for: {channel.id}")
    await interaction.response.defer(thinking=True)

    total_channels = data_manager.add_notification_channel(channel.id)
    Logger.info(f"Added notification channel: {channel.id}. Total channels: {total_channels}")

    embed = discord.Embed(
        title="✅ Channel Added",
        description=f"Added {channel.mention} to the notification channels.",
        color=0x00ff00
    )
    await interaction.followup.send(embed=embed)


@client.tree.command(name="sdm_remove-channel", description="Remove a notification channel")
@app_commands.checks.has_permissions(administrator=True)
async def remove_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    Logger.info(f"Received remove channel request for: {channel.id}")
    await interaction.response.defer(thinking=True)

    data_manager.remove_notification_channel(channel.id)
    Logger.info(f"Removed notification channel: {channel.id}")

    embed = discord.Embed(
        title="✅ Channel Removed",
        description=f"Removed {channel.mention} from notification channels.",
        color=0x00ff00
    )
    await interaction.followup.send(embed=embed)


@client.tree.command(name="sdm_list_channels", description="List all channels receiving stock notifications")
@app_commands.checks.has_permissions(administrator=True)
async def list_channels(interaction: discord.Interaction):
    Logger.info("Listing all notification channels")
    channels = data_manager.get_notification_channels()

    if not channels:
        Logger.warn("No notification channels configured")
        embed = discord.Embed(
            title="📋 Notification Channels",
            description="No channels are currently set up for notifications.",
            color=0xff0000
        )
    else:
        channel_list = []
        for channel_id in channels:
            channel = client.get_channel(channel_id)
            if channel:
                channel_list.append(f"• {channel.mention} (ID: {channel_id})")
            else:
                channel_list.append(f"• Unknown Channel (ID: {channel_id})")
                Logger.warn(f"Could not find channel with ID {channel_id}")

        embed = discord.Embed(
            title="📋 Notification Channels",
            description="\n".join(channel_list),
            color=0x00ccff
        )

    await interaction.response.send_message(embed=embed)


@client.tree.command(name="sdm_check_all_stocks", description="Manually trigger stock check for all watched products")
async def check_all_stocks(interaction: discord.Interaction):
    Logger.info("Manually triggered stock check for all products")
    await interaction.response.defer(thinking=True)
    await asyncio.create_task(check_watch_stocks(client))
    await interaction.edit_original_response(content="🔍 Manually triggered stock check completed.")


@tasks.loop(seconds=watch_product_cron_delay_seconds)
async def watched_products_stock_cron():
    Logger.info("Starting scheduled stock check")
    await asyncio.create_task(check_watch_stocks(client))
    Logger.info(f"Scheduled stock check completed. Next run in {watch_product_cron_delay_seconds} seconds.")


@client.event
async def on_ready():
    Logger.info(f'Bot is now online and ready to use: {client.user}')
    watched_products_stock_cron.start()


def init_bot():
    Logger.info("Initializing Discord bot")
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    client.run(discord_token)
