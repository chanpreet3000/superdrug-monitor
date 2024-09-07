import discord
from discord import app_commands

from logger import Logger
from utils import fetch_product_data, get_current_time


class Bot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


client = Bot()


@client.tree.command(name="watch", description="Get Notified when a product is in stock")
async def watch(interaction: discord.Interaction, product_url: str):
    await interaction.response.send_message(f"Watching product at: {product_url}")


@client.tree.command(name="check_stock", description="Check the current stock level of a product")
async def check_stock(interaction: discord.Interaction, product_url: str):
    Logger.info('Checking stock for product', product_url)
    await interaction.response.send_message("Checking stock levels, please wait...")

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

        await interaction.edit_original_response(content=f"🔍 **Stock Check Result for {data['name']}**", embed=embed)
    except Exception as err:
        Logger.error(f'Error occurred while fetching stock details for {product_url}', err)
        await interaction.followup.send("Unable to retrieve product data. Please try again later.")
    finally:
        Logger.info('Finished checking stock for product', product_url)


@client.event
async def on_ready():
    Logger.debug('Logged in successfully! Bot is now online & ready to use', client.user)
