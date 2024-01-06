import sys, typing, ccxt, asyncio, threading
sys.dont_write_bytecode = True
from discord.ext import commands

if typing.TYPE_CHECKING:
    import discord
    from src.discord.bot import DiscordHandler
    from src.crypto.main import CryptoMain
    from src.website.API import MainWebsite
    from src.system.colors import C, CNone
    from src.crypto.transmitters.API2Client import PriceRequester
    from src.crypto.transmitters.Client2API import Market
    from src.crypto.transmitters.sandbox import MarketSimulator, RequesterSimulator

class SharedResource:
    def __init__(self) -> None:
        self.lock: threading.Lock = threading.Lock()
        
        # glavni clasi
        self.discordHandler: DiscordHandler = None
        self.trackingWebsite: MainWebsite = None
        self.cryptoMain: CryptoMain = None
        
        # globalni var
        self.path: str = None
        self.colors: C | CNone = None
        self.config: dict = None
        self.loop: asyncio.AbstractEventLoop = None
        self.sandbox: bool = None

        # discord stvari
        self.discord_bot: commands.Bot = None 
        self.discord_notifications: list[dict[str, bool | str | float]] = []

        # crypto stvari
        self.binance: ccxt.binance = None
        self.price_requester: PriceRequester | RequesterSimulator = None
        self.market: Market | MarketSimulator = None
        self.interval: int | float = 15
        
        # databaze
        self.logic_db: dict[str, list[int | float] | int | float | None] = {
            "lastPrice" : None,
            "priceDB" : [],
            "precentDB" : [],
            "buy" : {
                "%" : None,
                "counter" : 0
            }
        }
        self.transaction_db: list[dict[str, typing.Any]] = []
        
        # tracking
        self.hourly_tracker: list[dict[str, float | str]] = []
        self.daily_tracker: dict[str, float | int] = {
            "buy_events" : 0,
            "sell_events" : 0,
            "profit" : 0.0, 
            "lowest" : 9999999999999,
            "highest" : 0
        }

        # sandbox
        self.WALLET: float = None
        self.CURRENT_MARKET_PRICE: float = 0

shared = SharedResource()

# branje podatkov iz shared classa (thread safe)
def read_shared(var: str) -> typing.Any:
    with shared.lock:
        try:
            return getattr(shared, var)
        except:
            return None

    
# pisanje podatkov iz shared classa (thread safe)
def write_shared(var: str, value: typing.Any) -> None:
    with shared.lock:
        try:
            setattr(shared, var, value)
        except Exception as e:
            print(f"Error writing to '{var}': {e}")


# terminate funkcija
def terminate() -> None:
    print(f"{shared.colors.Red}TERMINATING.{shared.colors.R}")

    if shared.discord_bot:
        try:
            # close connection with discord
            asyncio.run(shared.discord_bot.close())
        except Exception as error:
            print(f"TERMINATOR >> Error with terminating discord bot. {type(error).__name__}: {error}")
            
    if shared.price_requester:
        shared.price_requester.infLoop = False
    
    try:
        # kill main loop and its tasks/threads
        shared.loop.close()
    except Exception as error:
        print(error)

    # system exit
    sys.exit(0)