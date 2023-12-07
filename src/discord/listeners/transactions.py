import discord, sys, asyncio
sys.dont_write_bytecode = True
from discord.ext import commands
import src.connector as con

class Transactions(commands.Cog):
    def __init__(self) -> None:
        self.shared: con.SharedResource = con.shared
        self.channel_id: int = 1015937645135790120
        
        self.shared.discord_bot.loop.create_task(self.transaction_sender())
        
    async def transaction_sender(self) -> None:
        while True:
            while self.shared.discord_notifications:
                data: dict[str, bool | str | float] = self.shared.discord_notifications[0]
                discord_channel: discord.TextChannel = self.shared.discord_bot.get_channel(self.channel_id)
                
                if discord_channel:
                    message: str = f"```diff\n{"+" if data["profit"] else "-"} {data["action"]} {data["btc_value"]} bitcoins for {data["usd_value"]}.```"
                    await discord_channel.send(message)
                
                self.shared .discord_notifications.pop(0)

            await asyncio.sleep(1)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Transactions())
