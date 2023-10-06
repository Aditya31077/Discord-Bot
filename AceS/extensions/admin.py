import discord
from discord.ext import commands
from discord import app_commands

from ..core import AceBot
from ..settings import Info
import os

all_extensions = [app_commands.Choice(name=file[:-3].capitalize(), value=f"{Info.FORMATTED_EXTENSIONS_PATH}{file[:-3]}") for file in os.listdir(Info.EXTENSIONS_PATH) if file.endswith(".py") and not file.startswith("_")]

class Admin(commands.Cog):
    def __init__(self, bot: AceBot) -> None:
        self.bot = bot
    
    async def cog_check(self, inter: discord.Interaction) -> bool:
        return inter.user.id in self.bot.owner_ids
    
    @app_commands.choices(cog=all_extensions)
    @app_commands.command(name="reload",  description="Reload cog(s)")
    async def reload(self, inter: discord.Interaction, cog: str=None) -> None:
        await inter.response.defer(ephemeral=True, thinking=True)
        if cog is None:
            [await self.bot.unload_extension(f"{Info.FORMATTED_EXTENSIONS_PATH}{file[:-3]}") for file in os.listdir(Info.EXTENSIONS_PATH) if file.endswith(".py") and not file.startswith("_")]
            await self.bot.load_extensions_from()
    
        else:
            await self.bot.reload_extension(cog)
        await inter.edit_original_response(content="Successfully reloaded!")



async def setup(bot: AceBot) -> None:
    await bot.add_cog(Admin(bot))