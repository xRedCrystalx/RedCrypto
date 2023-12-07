import sys, discord, aiohttp, glob
sys.dont_write_bytecode = True
from discord.ext import commands
import src.connector as con

class MyBot(commands.AutoShardedBot):
    #initializing bot (intents, shards, prefix..)
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=discord.Intents.all(), shard_count=1, help_command=None)

    #starting setup_hook -> loading all extensions and syncing commands. !aiohttp required!
    async def setup_hook(self) -> None:
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        shared.discord_bot = self
        #Loading Extensions
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
                    print(f"DISCORD >> {shared.colors.Red}Failed to load {cog}: {type(error).__name__}; {error}{shared.colors.R}")

        #Syncing Attempts   
        try:
            await self.tree.sync()
        except Exception as error:
            print(f"DISCORD >> {shared.colors.Red}Failed to globally sync bot. {type(error).__name__}: {error}{shared.colors.R}")

    #Closing aiohttp session
    async def close(self) -> None:
        await super().close()
        await self.session.close()

    #Connect to discord
    async def on_ready(self) -> None:
        print(f"DISCORD >> {shared.colors.Magenta}{self.user} has connected to Discord!{shared.colors.R}")
        await self.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="Binance"))

shared: con.SharedResource = con.shared

class DiscordHandler:
    def start(self) -> None:
        try:
            bot = MyBot()
            bot.run(token=shared.config["discord"]["token"], reconnect=True, log_handler=None)#
            
        except Exception as e:
            print(e)

