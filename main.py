from discord.ext import commands
from dotenv import load_dotenv
import discord
import os
from game_data import msgs
import database as db

BASE_VALUES = [100, 100, 15]


load_dotenv()
token = os.getenv("TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(msgs['ready'].format(bot.user))

@bot.command(name='start')
async def start_game(ctx: commands.Context):
    player = ctx.author
    player_id = str(player.id)

    player_data = db.load_players(player_id)

    if not player_data:
        db.save_player(player_id=player_id, player_data=BASE_VALUES)
        await ctx.send(msgs['welcome'].format(player.mention))
    else:
        await ctx.send(msgs['started'].format(player.mention))


bot.run(token + 'A')