from ..data import SurvivrData
from discord.ext import commands

class CommandsCog(commands.Cog):
    @commands.command(aliases=['stats'])
    async def user_stats(self, ctx, slug, gamemode='all', interval='all'):
        survivr = await SurvivrData(slug, interval=interval, gamemode=gamemode)
        if survivr:
            await ctx.send(embed=survivr.embed)
        else:
            await ctx.send(f'{slug!r} is not valid survivr.')
