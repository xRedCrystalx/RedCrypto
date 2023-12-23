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

        # discord stvari
        self.discord_bot: commands.Bot = None
        self.discord_notifications: list[dict[str, bool | str | float]] = []

        # crypto stvari
        self.binance: ccxt.binance = None
        self.interval: int | float = 15
        self.transaction_db: dict = {}
        
        self.price_requester: PriceRequester = None
        
        # tracking
        self.hourly_tracker: list[dict[str, float | str]] = []

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

def update_shared(var_path: str, update_type: typing.Literal["extend", "append", "update", "add", "remove", "multiply", "divide"], update_value: typing.Any) -> None:
    with shared.lock:
        try:
            keys: list[str] = var_path.split('.')
            current_value = getattr(shared, keys[0])

            for key in keys[1:]:
                current_value = current_value[key]            
            
            if isinstance(current_value, list):
                if update_type == "extend":
                    current_value.extend(update_value)
                    setattr(shared, keys[0], current_value)
                elif update_type == "append":
                    current_value.append(update_value)
                    setattr(shared, keys[0], current_value)
                    
            elif isinstance(current_value, (int, float)):
                if update_type == "add":
                    setattr(shared, keys[0], current_value + update_value)
                elif update_type == "remove":
                    setattr(shared, keys[0], current_value - update_value)
                elif update_type == "multiply":
                    setattr(shared, keys[0], current_value * update_value)
                elif update_type == "divide" and update_value != 0:
                    setattr(shared, keys[0], current_value / update_value)
                else:
                    print(f"Error: Unsupported numeric operation for '{var_path}'")                

            # DICT SUPPORT NEEDED

        except Exception as e:
            print(f"Error updating '{var_path}': {e}")


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
    #sys.exit(0)