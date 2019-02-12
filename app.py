import discord
import discord
from discord.ext import commands
# from discord.utils import get
import logging
import re
from slugify import slugify
import dice
import random

logging.basicConfig(level=logging.INFO)

log = logging.getLogger('rfs')
bot = commands.Bot('!')

chars = {
    341044668269854740: 'muuug',
}
xp = {
    'muuug': 0,
    'bob': 0,
}
levels = {
    'muuug': None,
    'bob': None,
}
skills = {
    'muuug': {
        'do-anything': 1,
    },
    'bob': {
        'do-anything': 1,
    },
}

def regional_indicator(c:str):
    return chr(ord(c.strip().lower()[0]) - ord('a') + ord('🇦'))

def token_generator():
    while True:
        for c in 'abcdefghijklmnopqrstuvwxyz':
            yield c
roll_token = token_generator()
last_token = 'a'
rolls = {
    # <token>: (<mention>, <char>, <skill>, <message>)
}

char_re = re.compile(r'\s*(?:([^.#0-9]*)\.)?([^.#0-9]*)\s*#?\s*(.*)')
def parse_char_roll(player, arg):
    player = int(player)
    char, skill, comment = char_re.match(arg).groups()
    if not char:
        char = chars[player]
    char = slugify(char)
    skill = slugify(skill)
    if not skill:
        skill = 'do-anything'
    return char, skill

@bot.command(pass_context=True)
async def roll(ctx, *, arg=''):
    global last_token
    char, skill = parse_char_roll(ctx.message.author.id, arg)
    token = next(roll_token)
    rolls[token] = (ctx.message.author.mention, char, skill, ctx.message)
    await bot.add_reaction(ctx.message, regional_indicator(token))
    last_token = token

toke_re = re.compile(r'\s*(?:([A-Z])\s+)?(.*)')
@bot.command(pass_context=True)
async def vs(ctx, *, arg=''):
    global last_token
    token, remain = toke_re.match(arg).groups()
    if not token:
        token = last_token
    token = slugify(token)
    am, ac, ask, message = rolls[token]

    bm = ctx.message.author.mention
    bc, bsk = parse_char_roll(ctx.message.author.id, remain)

    if ac == bc:
        await bot.add_reaction(ctx.message, '⁉')
        return

    ar, arm, al, axl = roll_skill(ac, ask)
    br, brm, bl, bxl = roll_skill(bc, bsk)

    if ar > br:
        winmsg = "{} wins!".format(ac)
        brm += add_xp(bc)
    elif ar == br:
        winmsg = "tie!"
    else: #ar < br:
        winmsg = "{} wins!".format(bc)
        arm += add_xp(ac)

    arm += levelup(ac, al+1, axl)
    brm += levelup(bc, bl+1, bxl)

    await bot.remove_reaction(message, regional_indicator(token), bot.user)
    del rolls[token]
    await bot.say("{}\n{} {}\n{} {}".format(winmsg, am, arm, bm, brm))

dice_re = re.compile(r'([^#]*)#?.*')
@bot.command(pass_context=True)
async def dc(ctx, *, arg=''):
    global last_token
    token, remain = toke_re.match(arg).groups()
    if not token:
        token = last_token
    token = slugify(token)
    am, ac, ask, message = rolls[token]

    bm = ctx.message.author.mention
    bd, = dice_re.match(remain).groups()

    ar, arm, al, axl = roll_skill(ac, ask)
    try:
        br = int(dice.roll(bd))
        brm = "`{}` = {}".format(bd, br)
    except dice.DiceBaseException:
        await bot.add_reaction(ctx.message, '⁉')
        return

    if ar > br:
        winmsg = "{} suceeds!".format(ac)
    else: #ar <= br:
        winmsg = "{} fails!".format(ac)
        arm += add_xp(ac)
    
    arm += levelup(ac, al+1, axl)

    await bot.remove_reaction(message, regional_indicator(token), bot.user)
    del rolls[token]
    await bot.say("{}\n{} {}\n{} {}".format(winmsg, am, arm, bm, brm))

def roll_skill(char, skill):
    level = skills[char][skill]
    roll = [random.randint(1,6) for _ in range(level)]
    rollstr = ' '.join(str(r) for r in roll)
    value = sum(roll)
    xpleft = sum(0 if x == 6 else 1 for x in roll)
    
    rollmsg = "{}.{}: `{}d6` = [{}] = {}".format(char, skill, level, rollstr, value)
    return value, rollmsg, level, xpleft

def add_xp(char):
    xp[char] += 1
    return " [+1 XP: {}]".format(xp[char])

def levelup(char, level, xp_left):
    if xp_left == 0:
        levels[char] = (level, xp_left)
        return " [level up to {}!]".format(level)
    elif xp_left <= xp[char]:
        levels[char] = (level, xp_left)
        return " [level up to {} for {} XP!]".format(level, xp_left)
    else:
        levels[char] = None
        return ""

# @client.event
# async def on_message(message):
#     # we do not want the bot to reply to itself
#     if message.author == client.user:
#         return

#     if not message.content.startswith('!hello'):
#         return

#     if message.author.id in users:
#         users 
#     msg = 'Hello {0.author.mention}'.format(message)
#     await client.send_message(message.channel, msg)

# @client.event
# async def on_ready():
#     log.info('Logged in as')
#     log.info(client.user.name)
#     log.info(client.user.id)
#     log.info('------')

from keys import keys
bot.run(keys['discord-token'])