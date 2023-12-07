import discord, sys
sys.dont_write_bytecode = True
from discord import app_commands
from discord.ext import commands
import src.connector as con

class Shutdown(commands.Cog):
    def __init__(self) -> None:
        self.shared: con.SharedResource = con.shared

    @app_commands.command(name="stop")
    async def shutdown(self, interaction: discord.Interaction) -> None:
        #if ctx.author.id in [x for x in BotData["owners"]]:
        await interaction.response.send_message(content="Killing the process")
        await self.shared.discord_bot.close()
        
        await con.terminate()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Shutdown())
