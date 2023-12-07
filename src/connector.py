import sys, discord, typing, ccxt, os, asyncio, threading
sys.dont_write_bytecode = True
from src.system.colors import C, CNone
from discord.ext import commands

class SharedResource:
    def __init__(self) -> None:
        self.lock: threading.Lock = threading.Lock()
        
        #global
        self.path: str = None
        self.colors: C | CNone = None
        self.config: dict = None
        self.loop: asyncio.AbstractEventLoop = None

        # discord
        self.discord_bot: commands.Bot = None
        self.discord_notifications: list[dict[str, bool | str | float]] = []

        #crypto
        self.interval: int | float = 5
        self.transaction_db: dict = {}
        self.price_db: dict = {}

shared = SharedResource()

async def read_shared(var: str) -> typing.Any:
    with shared.lock:
        try:
            return getattr(shared, var)
        except:
            return None
    
async def update_shared(var: str, value: typing.Any, action: typing.Literal["replace", "add", "substract", "divide", "multiply", "append", "remove", "pop", "update"] = "replace") -> bool:
    with shared.lock:
        try:
            shared_variable: typing.Any = getattr(shared, var)
        except:
            return
        
        if isinstance(shared_variable, list):
            ...
        elif isinstance(shared_variable, dict):
            ...
        elif type(shared_variable) in (int, float):
            ...
        elif isinstance(shared_variable, str):
            ...
        elif isinstance(shared_variable, bool):
            ...
        else:
            return
        
        



async def terminate() -> None:
    #sys.exit(0)
    ...