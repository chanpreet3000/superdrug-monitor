import traceback

from Logger import Logger
from discord_bot import init_bot

if __name__ == "__main__":
    try:
        init_bot()
    except Exception as e:
        traceback.print_exc()
        Logger.critical('Internal error occurred', e)
    finally:
        Logger.critical('Shutting down bot...')
