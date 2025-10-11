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

@bot.command(name="help")
async def help(ctx: commands.Context):
    await ctx.send(msgs["help"])

@bot.command(name="status")
async def status(ctx: commands.Context):
    player = ctx.author
    player_id = str(player.id)

    player_data = db.load_player(player_id)
    locs_data = db.load_locations()

    if not player_data:
        await ctx.send(f"{player.mention}, нажми команду `!start`")
        return

    current_hp = player_data['current_hp']
    max_hp = player_data['max_hp']
    damage = player_data['damage']
    player_loc_id = player_data['current_location_id']
    passed_locs_ids = player_data['passed_locs'].split(",") if player_data['passed_locs'] else []

    hp_percent = current_hp / max_hp
    hp_bar = "❤️" * int(hp_percent * 5) + "🖤" * (5 - int(hp_percent * 5))

    current_loc = "Таверна 🍺"
    passed_locs = []

    for loc in locs_data:
        loc_id = str(loc['id'])
        if loc_id == str(player_loc_id):
            current_loc = loc['name']
        if loc_id in passed_locs_ids and loc_id != "1":
            passed_locs.append(loc['name'])

    if not passed_locs:
        passed_locs = ["Отсутствует"]

    await ctx.send(
        msgs['status'].format(
            player.mention, current_hp, max_hp, damage, current_loc, ", ".join(passed_locs), hp_bar
        )
    )


@bot.command(name="map")
async def map(ctx: commands.Context):
    player = ctx.author
    player_id = str(player.id)
    player_mention = player.mention

    player_data = db.load_player(player_id)
    locs_data = db.load_locations()

    if not player_data:
        await ctx.send(f"{player.mention}, нажми команду `!start`")
        return

    msg_data = [f"{player_mention}, вот карта твоих приключений 🗺️\n"]
    passed_locs = player_data['passed_locs'].split(",") if player_data['passed_locs'] else []
    current_loc_id = str(player_data['current_location_id'])

    for data in locs_data:
        loc_id = str(data['id'])
        if loc_id == current_loc_id:
            status = "Текущая локация 📍"
        elif loc_id in passed_locs:
            status = "Пройдено ✅"
        elif loc_id == "1":
            status = "Открыто ⭕"
        else:
            status = "Не исследовано ❓"

        if loc_id == "1":
            msg = msgs['locinfo_hub'].format(data['id'], data['name'], status)
        else:
            msg = msgs['locinfo'].format(
                data['id'], data['name'], status, data['boss_name'], data['boss_hp'],
                data['boss_dmg'], data['hp_bonus'], data['dmg_bonus']
            )
        msg_data.append(msg)

    await ctx.send("\n".join(msg_data))

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

    loc_id = player_data["current_location_id"]
    if loc_id == 1:
        await ctx.send(msgs['noattack_hub'].format(player_mention))

    loc_data = db.load_locations(loc_id=loc_id)[0]
    player_hp = player_data["current_hp"]
    player_dmg = player_data["damage"]
    boss_hp = player_data["current_boss_hp"]
    boss_dmg = loc_data["boss_dmg"]
    boss_name = loc_data["boss_name"]

    print(loc_data)

    if boss_hp <= 0:
        await ctx.send(msgs['alreadydead'].format(player_mention, boss_name))
        return

    boss_hp -= player_dmg
    await ctx.send(msgs["attack"].format(player_mention, boss_name, player_dmg))

    if boss_hp <= 0:
        db.pass_location(player_id, loc_id)
        await ctx.send(msgs['bossdefeat'].format(boss_name))

        db.add_bonus(player_id, loc_data['hp_bonus'], loc_data['dmg_bonus'])
        db.restore_hp(player_id)

        player_data = db.load_player(player_id)
        await ctx.send(msgs['bonus'].format(player_mention, player_data['max_hp'],
                                            loc_data['hp_bonus'], player_data['damage'], loc_data['dmg_bonus']))

        if db.check_win(player_data['passed_locs']):
            await ctx.send(msgs['win'].format(player_mention))
            db.delete_player(player_id)
        return

    player_hp -= boss_dmg
    await ctx.send(msgs["attack"].format(boss_name, player_mention, boss_dmg))

    if player_hp <= 0:
        await ctx.send(msgs['gameover'].format(player_mention))
        return

    db.update_hp(player_id, player_hp, boss_hp)
    await ctx.send(msgs['fightstatus'].format(boss_hp, player_hp))


bot.run(token + 'A')