import sys, discord, typing, ccxt, os, asyncio
sys.dont_write_bytecode = True
from src.system.colors import C, CNone
from discord.ext import commands

class Connector:
    #global
    path: str = None
    colors: C | CNone = None
    config: dict = None
    loop: asyncio.AbstractEventLoop = None
    
    # discord
    discord_bot: commands.Bot = None
    discord_notifications: list[dict[str, bool | str | float]] = []

    #crypto
    transaction_db: dict = {}
    price_db: dict = {}

connector = Connector()

async def terminate() -> None:
    #sys.exit(0)
    ...