import discord
from discord import app_commands
from discord.ext import commands

from ..core import AceBot
from ..ext import Record, BookmarkView


class Messages(commands.Cog):
    def __init__(self, bot: AceBot) -> None:
        self.bot = bot

    def get_id(self, id_or_link: str | int, /) -> int | None:
        if len(id_or_link) in (19, 20,) and id_or_link.isdigit():
            message_id = id_or_link

        elif len(id_or_link) == 88 and not id_or_link.isdigit() and id_or_link.startswith("https://discord.com/channels/"):
            message_id = id_or_link.split("/")[-1]
        else:
            return None

        return int(message_id)
    
    def get_current_tracking_ftstring(self, records: list[Record] | Record):
        if isinstance(records, list):
            return "\n- ".join([f"<https://discord.com/channels/{message.guild_id}/{message.channel_id}/{message.message_id}>" for message in records])
        return f"<https://discord.com/channels/{records.guild_id}/{records.channel_id}/{records.message_id}>"

    @app_commands.command(name="bookmark", description="Bookmark a message!")
    async def bookmark(self, inter: discord.Interaction, id_or_link: str) -> None:
        await inter.response.defer()

        message_id = self.get_id(id_or_link)
        message = await inter.channel.fetch_message(message_id)
        if message.attachments:
            attachment = message.attachments[0]

        if message.embeds:
            embed = message.embeds[0]
            has_embed = True
            embed_title = 'No Title' if embed.title is None else embed.title
            embed_description = 'No Description' if embed.description is None else embed.description
            embed_content = f"**Title**: {embed_title}\n**Description**: {embed_description}"
        else:
            has_embed = False
        embed = discord.Embed()
        if message.content:
            embed.description = f"**Message Content**: {message.content}" 
        embed.add_field(name="Attachment", value="True" if message.attachments else "False", inline=False) 
        embed.add_field(name="Embed content", value=embed_content, inline=False) if has_embed is True else ...
        embed.add_field(name="Server", value=inter.guild.name, inline=False)
        embed.add_field(name="Channel", value=inter.channel, inline=False)
        embed.add_field(name="Message author", value=message.author, inline=False)
        embed.add_field(name="Message", value=f"[Click Here]({message.jump_url})", inline=False)
        view = BookmarkView(embed)
        await inter.edit_original_response(content=f"The button below will timeout in 3 minutes!", embed=embed, view=view)
        try:
            await inter.user.send(embed=embed)
        except discord.Forbidden:
            await inter.channel.send(f"{inter.user.mention}, Enable your DMs and click the **Copy** button!")


    @app_commands.command(name="track", description="Track a message!")
    async def track(self, inter: discord.Interaction, id_or_link: str, message_channel: discord.TextChannel) -> discord.InteractionMessage | None:
        await inter.response.defer(ephemeral=True, thinking=True)
        
        if (message_id:=self.get_id(id_or_link)) is None:
            return await inter.edit_original_response(content="Invalid message ID/link!")

        if (await self.bot.db.messages.read_user_message(inter.user.id, message_id)):
            return await inter.edit_original_response(content="You're already tracking that message!")
        
        if (limit:=(await self.bot.db.messages.read_user(inter.user.id))):
            if len(limit) >= 3:
                embed = discord.Embed(title="Currently tracking messages!", description=self.get_current_tracking_ftstring(limit))
                return await inter.edit_original_response(content="You are already tracking **3** messages! You can only track **3** messages at a time!", embed=embed)

        message = await message_channel.fetch_message(message_id)

        await inter.edit_original_response(content=f"Now tracking [this]({message.jump_url}) message!")

        embed = discord.Embed()
        if message.content:
            embed.description = f"**Message Content**: {message.content}" 
        embed.add_field(name="Attachment", value="Yes" if message.attachments else "None", inline=False) 
        embed.add_field(name="Embed content", value=message.embeds[0].description, inline=False) if message.embeds else ...
        embed.add_field(name="Server", value=message.guild.name, inline=False)
        embed.add_field(name="Channel", value=message.channel, inline=False)
        embed.add_field(name="Message author", value=message.author, inline=False)
        embed.add_field(name="Message", value=f"[Click Here]({message.jump_url})", inline=False)
        embed.set_image(url=message.attachments[0].url) if message.attachments else ...
        
        m = await inter.user.send(embed=embed)
        await self.bot.db.messages.create(inter.user.id, message_channel.id, message_id, message_channel.guild.id, m.id, m.channel.id)

    @app_commands.command(name="untrack", description="Untrack a message!")
    async def untrack(self, inter: discord.Interaction, id_or_link: str) -> discord.InteractionMessage | None:
        await inter.response.defer(ephemeral=True, thinking=True)

        if (message_id:=self.get_id(id_or_link)) is None:
            return await inter.edit_original_response(content="Invalid message ID/link!")

        if (message:=await self.bot.db.messages.remove(inter.user.id, message_id)) is False:
            return await inter.edit_original_response(content="Could not find any tracked messages with that ID/link")

        await inter.edit_original_response(content=f"Successfully untracked [this]({self.get_current_tracking_ftstring(message)}) message!")

    @app_commands.command(name="untrack_all", description="Untrack all messages!")
    async def untrack_all(self, inter: discord.Interaction) -> discord.InteractionMessage | None:
        await inter.response.defer(ephemeral=True, thinking=True)
        if await self.bot.db.messages.read_user(inter.user.id) is None:
            return await inter.edit_original_response(content="You are already not tracking any message!")

        await self.bot.db.messages.remove_user(inter.user.id)
        await inter.edit_original_response(content="Successfully untracked all messages!")        

    @app_commands.command(name="current_tracking", description="Get current tracking messages!")
    async def current_tracking(self, inter: discord.Interaction) -> discord.InteractionMessage | None: 
        await inter.response.defer(ephemeral=True, thinking=True)
        i = await self.bot.db.messages.read_user(inter.user.id)
        if i is None:
            return await inter.edit_original_response(content="You are not tracking any messages!")
        embed = discord.Embed(title="Currently tracking messages!", description=self.get_current_tracking_ftstring(i))
        await inter.edit_original_response(embed=embed)

async def setup(bot: AceBot):
    await bot.add_cog(Messages(bot))