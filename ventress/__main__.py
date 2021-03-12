import os

from dotenv import load_dotenv
from discord.ext import commands
from .cogs.commands import CommandsCog

load_dotenv(override=True)

bot = commands.Bot(command_prefix='test.', case_insensitive=True)

bot.add_cog(CommandsCog())

@bot.event
async def on_ready():
    print('Bot is ready!')

bot.run(os.environ['testing-token'])
