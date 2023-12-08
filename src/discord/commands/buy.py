import discord, sys
sys.dont_write_bytecode = True
from discord import app_commands
from discord.ext import commands
import src.connector as con

class Buy(commands.Cog):
    def __init__(self) -> None:
        self.bot: commands.Bot = con.read_shared("discord_bot")

    @app_commands.command(name="buy")
    async def buy(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(content="Under Development.", ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Buy())
