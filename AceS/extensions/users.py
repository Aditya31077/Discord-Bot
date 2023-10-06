from discord.ext import commands
from discord import app_commands
import discord

from ..core import AceBot

class Users(commands.Cog):
    def __init__(self, bot: AceBot) -> None:
        self.bot = bot

    def get_guild_rank(self, guild_data: list, member: discord.Member) -> None | int:
        s = sorted(guild_data, key=lambda element: element[2])
        form = list(reversed([record[0] for record in s]))
        return None if form is None else (form.index(member.id) + 1)
    
    @app_commands.command(name="get_avatar", description="Get the avatar of a user")
    async def get_avatar(self, inter: discord.Interaction, user: discord.User=None) -> None:
        await inter.response.defer(ephemeral=True, thinking=True)
        user = user or inter.user
        embed = discord.Embed(colour=discord.Colour.random()).set_image(url=user.display_avatar.url)
        await inter.edit_original_response(embed=embed)
    
    @app_commands.command(name="info", description="Get the info of a user")
    async def info(self, inter: discord.Interaction, user: discord.User | discord.Member=None) -> None:
        await inter.response.defer(ephemeral=True, thinking=True)
        user = user or inter.user
        
        embed = discord.Embed(colour=user.top_role.colour).set_thumbnail(url=user.display_avatar.url)
        
        embed.add_field(name="Username", value=user).add_field(name="Display name", value=user.global_name).add_field(name="Discord ID", value=user.id).add_field(name="Status", value=user.status).add_field(name="Avatar URL", value=f"[{user.name}'s avatar URL]({user.display_avatar.url})")
    
        embed.add_field(name="Nickname", value=user.display_name).add_field(name="Colour", value=user.top_role.colour).add_field(name="Number of Roles", value=len(user.roles)-1).add_field(name="Server join", value=discord.utils.format_dt(user.joined_at)).add_field(name="Account created", value=discord.utils.format_dt(user.created_at)) if isinstance(user, discord.Member) else ...
        
        embed.add_field("Activity", ", ".join([activity.name for activity in user.activities])) if user.activities else ...

        await inter.edit_original_response(embed=embed)
    
    @app_commands.command(name="rank", description="Display the rank of the member in the current server")
    async def rank(self, inter: discord.Interaction, member: discord.Member=None) -> None:
        await inter.response.defer(ephemeral=True, thinking=True)
        member = member or inter.user
        if member.bot is True:
            return await inter.edit_original_response(content="Bots are excluded from levelling!")
        user_record = await self.bot.db.ranks.create(member.id, inter.guild.id)
        guild_records = await self.bot.db.ranks.all_guild_records(inter.guild.id, raw=True)
        guild_rank = self.get_guild_rank(guild_records, member)
        
        embed = discord.Embed(title=f"{member.name}'s experience!").set_thumbnail(url=member.display_avatar.url).add_field(name="Experience", value=user_record.experience, inline=False).add_field(name="Level", value=user_record.level, inline=False).add_field(name="Rank", value=guild_rank, inline=False)
        await inter.edit_original_response(embed=embed)

async def setup(bot: AceBot) -> None:
    await bot.add_cog(Users(bot))