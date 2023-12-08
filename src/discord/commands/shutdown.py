import discord, sys
sys.dont_write_bytecode = True
from discord import app_commands
from discord.ext import commands
import src.connector as con

class Shutdown(commands.Cog):
    @app_commands.command(name="stop")
    async def shutdown(self, interaction: discord.Interaction) -> None:
        bot: commands.Bot = con.read_shared("discord_bot")
        config: dict = con.read_shared("config")
        
        if interaction.user.id in config["discord"]["administrators"]:
            await interaction.response.send_message(content="Killing the process")
            await bot.close()
        
            await con.terminate()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Shutdown())
