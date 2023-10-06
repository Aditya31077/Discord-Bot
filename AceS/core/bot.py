import os
import platform
from datetime import datetime

import discord
from discord.ext import commands

from ..settings import Info
from ..database import DatabaseManager

class AceBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=Info.COMMANDS_PREFIX, intents=discord.Intents.all(), owner_ids=Info.OWNER_IDS)
        self._boot_time = datetime.utcnow() #for uptime command

    async def setup_hook(self) -> None:
        await self.load_extensions_from()
        self.tree.copy_global_to(guild=discord.Object(Info.APP_COMMANDS_GUILD)) #binding server id with all commands
        self.sync_status = await self.tree.sync() #syncing the commands with discord API
        self.tree.on_error = self.on_tree_error #defining the error handler for slash commands

        self.db = DatabaseManager() #creating an instance of the db handler
        await self.db.setup() #running the setup function to trigger the other setup functions inside the DatabaseManager setup method
        
    async def on_tree_error(self, inter: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        print(error) #Slash command error handler (simply prints the error)
    
    async def on_ready(self) -> None:
        app_commands = self.tree.get_commands() #Gets all the slash commands
        print(f'''Host Platform: {platform.system()}\nBoot Time (UTC): {self._boot_time}\nApp Commands: {", ".join(command.name for command in app_commands)}\nSynced: {"True" if self.sync_status else "False"}''')
    
    def run(self) -> None:
        super().run(Info.TOKEN)


    async def load_extensions_from(self, folder_path: str = Info.EXTENSIONS_PATH) -> None:
        [await self.load_extension(f"{Info.FORMATTED_EXTENSIONS_PATH}{file[:-3]}") for file in os.listdir(folder_path) if file.endswith(".py") and not file.startswith("_")] #loads all the commands using a list comprehension