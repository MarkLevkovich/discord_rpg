from discord.ext import commands
from dotenv import load_dotenv
import discord
import os

from game_data import msgs
import database as db

BASE_VALUES = [100, 100, 15, 1, "", 0]

db.init_db()

load_dotenv()
token = os.getenv("TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(msgs['ready'].format(bot.user))


@bot.command(name="start")
async def start_game(ctx: commands.Context):
    player = ctx.author
    player_id = str(player.id)

    player_data = db.load_player(player_id)

    if not player_data:
        db.save_player(player_id=player_id, player_data=BASE_VALUES)
        await ctx.send(msgs['welcome'].format(player.mention))
    else:
        await ctx.send(msgs['started'].format(player.mention))


@bot.command(name="go")
async def go(ctx: commands.Context, location: str = None):
    player = ctx.author
    player_id = str(player.id)
    player_mention = player.mention

    player_data = db.load_player(player_id)

    if not player_data:
        await ctx.send(f"{player_mention}, нажми команду `!start`")
        return

    if location is None:
        await ctx.send(msgs['goerror'].format(player_mention))
        return

    loc_data = db.load_locations(loc_id=int(location)) if location.isdigit() else db.load_locations(loc_name=location)

    if not loc_data:
        await ctx.send(msgs['wrongloc'].format(player_mention, location))
        return

    loc_data = loc_data[0]
    loc_id = loc_data['id']
    loc_name = loc_data["name"]

    if loc_id == player_data['current_location_id']:
        await ctx.send(msgs['alreadyonloc'].format(player_mention, loc_name))
        return

    if loc_id != 1:
        passed_locations = player_data['passed_locs'].split(",") if player_data["passed_locs"] else []
        if str(loc_id) in passed_locations:
            await ctx.send(msgs["onpassedloc"].format(player_mention, loc_name))
            return

    db.update_location(player_id, loc_id=loc_id)
    if loc_id != 1:
        db.update_current_boss_hp(player_id, loc_data['boss_hp'])
        await ctx.send(msgs['bossmeet'].format(player_mention, loc_name, loc_data['boss_name'], loc_data['boss_hp'],
                                               loc_data['boss_dmg']))
    else:
        await ctx.send(msgs['hub_return'].format(player_mention, loc_name))



@bot.command(name="attack")
async def attack(ctx: commands.Context):
    player = ctx.author
    player_id = str(player.id)
    player_mention = player.mention

    player_data = db.load_player(player_id)

    if not player_data:
        await ctx.send(f"{player_mention}, нажми команду `!start`")
        return

    loc_id = player_data['current_location_id']
    if loc_id == 1:
        await ctx.send(msgs['noattack_hub'].format(player_mention))

    loc_data = db.load_locations(loc_id=loc_id)[0]
    player_hp = player_data['current_hp']
    player_dmg = player_data['damage']
    boss_hp = player_data['current_boss_hp']
    boss_dmg = loc_data['boss_dmg']
    boss_name = loc_data['boss_name']

    if boss_hp <= 0:
        await ctx.send(msgs['alreadydead'].format(player_mention, boss_name))
        return

    boss_hp -= player_dmg
    await ctx.send(msgs['attack'].format(player_mention, boss_name, player_dmg))

    if boss_hp <= 0:
        await ctx.send(msgs['bossdefeat'].format(boss_name))

        player_data = db.load_player(player_id)

    player_hp -= boss_dmg
    await ctx.send(msgs['attack'].format(boss_name, player_mention, boss_dmg))

    if player_hp <= 0:
        await ctx.send(msgs['gameover'].format(player_mention))
        return

    await ctx.send(msgs['fightstatus'].format(boss_hp, player_hp))


bot.run(token+'A')