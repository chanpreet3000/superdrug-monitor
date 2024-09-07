import os
import traceback

from dotenv import load_dotenv
from logger import Logger
from discord_bot import client

load_dotenv()

if __name__ == "__main__":
    try:
        token = os.getenv('DISCORD_BOT_TOKEN')
        client.run(token)
    except Exception as e:
        traceback.print_exc()
        Logger.critical('Internal error occurred', e)
