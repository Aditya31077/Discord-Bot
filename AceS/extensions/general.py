import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from ..core import AceBot


class General(commands.Cog):
    def __init__(self, bot: AceBot) -> None:
        self.bot = bot
    
    @app_commands.command(name="ping", description="Get my ping")
    async def ping(self, inter: discord.Interaction) -> None:
        await inter.response.defer(ephemeral=True, thinking=True)
        embed = discord.Embed(title="My Latency", description=f"{round(self.bot.latency*1000)}ms", colour=discord.Colour.random())
        await inter.edit_original_response(embed=embed)

    @app_commands.command(name="uptime", description="Get my uptime")
    async def uptime(self, inter: discord.Interaction) -> None:
        await inter.response.defer(ephemeral=True, thinking=True)

        _upt = int((datetime.utcnow() - self.bot._boot_time).total_seconds())
        hours, remainder = divmod(_upt, 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        embed = discord.Embed(title="Uptime", description=f"Days: {days}\nHours: {hours}\nMinutes: {minutes}\nSeconds: {seconds}", colour=discord.Colour.random())
        await inter.edit_original_response(embed=embed)
    
    
async def setup(bot: AceBot) -> None:
    await bot.add_cog(General(bot))