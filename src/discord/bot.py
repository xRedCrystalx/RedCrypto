import sys, discord, aiohttp, glob
sys.dont_write_bytecode = True
from discord.ext import commands
import src.connector as con

class MyBot(commands.AutoShardedBot):
    #initializing bot (intents, shards, prefix..)
    def __init__(self) -> None:
        self.colors: con.C | con.CNone = con.read_shared(var="colors")
        con.write_shared("discord_bot", self)
        super().__init__(command_prefix="!", intents=discord.Intents.all(), shard_count=1, help_command=None)

    # setup_hook - nalaganje vseh modulov predenj se poveže na discord
    async def setup_hook(self) -> None:
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        
        # nalaganje vseh modulov
        cogPaths: tuple[str, ...] = ("src\\discord\\listeners", "src\\discord\\commands")
        for cogPath in cogPaths:
            counter = 0
            windows: str = f"{cogPath}/**/*.py"
            linux: str = f"*/{cogPath}/**/*.py"

            for cog in glob.glob(windows, recursive=True):
                try:
                    await self.load_extension(cog.replace("\\", ".").replace("/", ".").removesuffix(".py"))
                    counter += 1
                except Exception as error:
                    print(f"DISCORD >> {self.colors.Red}Failed to load {cog}: {type(error).__name__}; {error}{self.colors.R}")

        # syncing komand globalno 
        try:
            await self.tree.sync()
        except Exception as error:
            print(f"DISCORD >> {self.colors.Red}Failed to globally sync bot. {type(error).__name__}: {error}{self.colors.R}")

    # zapiranje povezave z discordom (zato da ne dobim errorje)
    async def close(self) -> None:
        await super().close()
        print(f"DISCORD >> Closed connection with discord.")
        await self.session.close()

    # povezava na discord
    async def on_ready(self) -> None:
        print(f"DISCORD >> {self.colors.Magenta}{self.user} has connected to Discord!{self.colors.R}")
        await self.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="Binance"))

# loader handler
class DiscordHandler:
    def start(self) -> None:
        try:
            # štartanje discord bota
            bot = MyBot()
            con.write_shared("discord_bot", bot)
            bot.run(token=con.read_shared(var="config")["discord"]["token"], reconnect=True)#, log_handler=None
        
        except Exception as error:
            print(f"DiscordHandler >> Error when starting the bot. {type(error).__name__}: {error}")
            con.terminate()

