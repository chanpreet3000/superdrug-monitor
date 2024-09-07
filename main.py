import discord
from discord import app_commands
import os
from dotenv import load_dotenv
from logger import Logger

load_dotenv()


class Bot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


client = Bot()


@client.tree.command(name="watch", description="Watch a product's stock level")
async def watch(interaction: discord.Interaction, product_url: str):
    await interaction.response.send_message(f"Watching product at: {product_url}")


@client.tree.command(name="check_stock", description="Check the current stock level of a product")
async def check_stock(interaction: discord.Interaction, product_url: str):
    await interaction.response.send_message(f"Checking stock for: {product_url}")


@client.event
async def on_ready():
    Logger.debug('Logged in as', client.user)


if __name__ == "__main__":
    try:
        token = os.getenv('DISCORD_BOT_TOKEN')
        client.run(token)
    except Exception as e:
        Logger.critical('Internal error occurred', e)
