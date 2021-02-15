import os

from dotenv import load_dotenv
from discord.ext import commands

load_dotenv(override=True)

bot = commands.Bot(command_prefix='test.', case_insensitive=True)

@bot.event
async def on_ready():
    print('Bot is ready!')

bot.run(os.environ['testing-token'])
