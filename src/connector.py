import sys, discord, typing, ccxt, os, asyncio
sys.dont_write_bytecode = True
from src.system.colors import C, CNone
from discord.ext import commands

class Connector:
    path: str = None
    colors: C | CNone = None
    config: dict = None
    loop: asyncio.AbstractEventLoop = None
    discord_bot: commands.Bot = None
    discord_connection: asyncio.Future = None

connector = Connector()

async def terminate() -> None:
    if not connector.discord_bot:
        print("IF")
        #await connector.discord_bot.close()
        await connector.discord_connection
