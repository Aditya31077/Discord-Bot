import discord
from discord.ext import commands

from ..core import AceBot
from discord.http import handle_message_parameters

class Events(commands.Cog):
    def __init__(self, bot: AceBot) -> None:
        self.bot = bot

    @commands.Cog.listener("on_raw_message_delete")
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        if (records:=await self.bot.db.messages.read_message(payload.message_id)) is None:
            return None
        
        for record in records:
            try:
                await self.bot.http.send_message(record.dm_channel_id, params=handle_message_parameters(content=f"Original message for [this](https://discord.com/channels/@me/{record.dm_channel_id}/{record.dm_id}) message has been deleted!"))
            except discord.Forbidden:
                pass

        await self.bot.db.messages.remove_message(payload.message_id)

    @commands.Cog.listener("on_raw_message_edit")
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        if (records:=await self.bot.db.messages.read_message(payload.message_id)) is None:
            return None

        for record in records:
            try:
                await self.bot.http.send_message(record.dm_channel_id, params=handle_message_parameters(content=f"Original message for [this](https://discord.com/channels/@me/{record.dm_channel_id}/{record.dm_id}) message has been updated! Get the **original** message [here](<https://discord.com/channels/{record.guild_id}/{record.channel_id}/{record.message_id}>)!"))
            except discord.Forbidden:
                pass

    
    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> discord.Message | None:
        if message.author.bot is True:
            return None
        user = await self.bot.db.ranks.create(message.author.id, message.guild.id, starting_xp=0)

        if (user.experience+5) % 200 == 0:
            await self.bot.db.ranks.update(message.author.id, message.guild.id, xp=user.experience+5, level=user.level+1)
            try:
                return await message.author.send(f"You have levelled up to **{user.level+1}** in **{message.guild.name}**")
            except:
                return None
        
        await self.bot.db.ranks.update(message.author.id, message.guild.id, xp=user.experience+5)
        

async def setup(bot: AceBot) -> None:
    await bot.add_cog(Events(bot))