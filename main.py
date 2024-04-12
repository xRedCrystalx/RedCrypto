import sys, asyncio, os, json, typing
sys.dont_write_bytecode = True
from src.system.colors import auto_color_handler, C, CNone
import src.connector as con
from src.discord.bot import DiscordHandler
from src.crypto.main import CryptoMain
from src.website.API import MainWebsite

class Main:
    def __init__(self) -> None:
        self.c: C | CNone = auto_color_handler()
        self.path: str = os.path.dirname(os.path.realpath(__file__))
        
        with open(file=f"{self.path}/src/config.json") as config:
            self.config: dict = json.load(config)
    
    # shranjevanje v shared dataclass
    async def save(self) -> None:
        try:
            shared.config = self.config
            shared.colors = self.c
            shared.path = self.path
            shared.loop = self.loop
            shared.sandbox = self.sandbox
            shared.WALLET = self.config["general"]["sandbox"]["wallet"]
        except Exception:
            return False
        return True
        
    # main funkcija k vse zažene
    async def main(self) -> None:
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.sandbox: bool = self.config["general"]["sandbox"]["status"]
        
        # terminira če shranjevanje faila
        if not await self.save():
            await con.terminate()
            
        # actual starting..
        print(f"""{self.c.Red}
____ ____ ___    ____ ____ _   _ ___  ___ ____ 
|__/ |___ |  \\   |    |__/  \\_/  |__]  |  |  | 
|  \\ |___ |__/   |___ |  \\   |   |     |  |__|
{self.c.R}
Initializing..""")

        # začetek discord bota v novem threadu
        if self.config["discord"]["switch"]:
            shared.discordHandler = DiscordHandler()
            self.loop.run_in_executor(None, shared.discordHandler.start)
        else:
            print(f"{self.c.DBlue}INFO {self.c.R}>> Discord bot is disabled")
        
        # začetek internetne strani v novem threadu
        if self.config["local-tracking"]["switch"]:
            shared.trackingWebsite = MainWebsite()
            self.loop.run_in_executor(None, shared.trackingWebsite.start)
            print(f"Local website link: {self.c.Magenta}http://localhost:{self.config["local-tracking"]["port"]}/ {self.c.R}")
        else:
            print(f"{self.c.DBlue}INFO {self.c.R}>> Webserver (tracker) is disabled.")
    
        # zacetek celotne logike in povezave z binance v novem threadu
        shared.cryptoMain = CryptoMain()
        self.loop.run_in_executor(None, shared.cryptoMain.start)      
        
if __name__ == "__main__":
    shared: con.SharedResource = con.shared
    asyncio.run(Main().main())
