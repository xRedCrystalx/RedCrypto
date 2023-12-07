import sys, asyncio, os, json
sys.dont_write_bytecode = True
from src.system.colors import auto_color_handler, C, CNone
import src.connector as con
from src.discord.bot import DiscordHandler
from src.crypto.main import CryptoMain

class Main:
    def __init__(self) -> None:
        self.c: C | CNone = auto_color_handler()
        self.path: str = os.path.dirname(os.path.realpath(__file__))
        
        with open(file=f"{self.path}/src/config.json") as config:
            self.config: dict = json.load(fp=config)
    
    # save everything to connector class
    async def save(self) -> None:
        try:
            connector.config = self.config
            connector.colors = self.c
            connector.path = self.path
            connector.loop = self.loop
        except Exception:
            return False
        return True
        
    # start of the discord bot file & CCXT    
    async def main(self) -> None:
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        
        # terminate if failed to save to connector
        if not await self.save():
            await con.terminate()
            
        # actual starting..
        print(f"""{self.c.Red}
____ ____ ___    ____ ____ _   _ ___  ___ ____ 
|__/ |___ |  \\   |    |__/  \\_/  |__]  |  |  | 
|  \\ |___ |__/   |___ |  \\   |   |     |  |__| 
{self.c.R}""")
        
        # starting discord bot in async thread so it doesn't block the main function of the program
        self.loop.run_in_executor(None, DiscordHandler().start)
        
        # starting connection with binance / ccxt in async thread
        self.loop.run_in_executor(None, CryptoMain().start)
        
        
if __name__ == "__main__":
    connector: con.Connector = con.connector
    asyncio.run(Main().main())