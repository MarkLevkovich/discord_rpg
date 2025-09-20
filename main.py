from discord.ext import commands
from dotenv import load_dotenv
import discord
import os

load_dotenv()
token = os.getenv("TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot {bot.user} ready for work!")


bot.run(token)