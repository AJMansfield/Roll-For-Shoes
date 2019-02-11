import discord
import discord
from discord.ext import commands
# from discord.utils import get
import logging
import re
from slugify import slugify
import dice

logging.basicConfig(level=logging.INFO)

log = logging.getLogger('rfs')
bot = commands.Bot('!')

chars = {
    341044668269854740: 'muuug',
}
skills = {
    'muuug': {
        'do-anything': 1,
    },
}

emoji = {
    a: b for (a,b) in zip('abcdefghijklmnopqrstuvwxyz', (chr(i) for i in range(0x1F1E6, 0x1F1FF+1)))
}
def token_generator():
    while True:
        for e in emoji:
            yield e
roll_token = token_generator()
last_token = 'a'
rolls = {

}

char_re = re.compile(r'\s*(?:([^.#0-9]*)\.)?([^.#0-9]*)\s*#?\s*(.*)')
def parse_char_roll(player, arg):
    char, skill, comment = char_re.match(arg).groups()
    if not char:
        char = chars[player]
    char = slugify(char)
    skill = slugify(skill)
    if not skill:
        skill = 'do-anything'
    return char, skill

@bot.command()
async def roll(ctx, *, arg=''):
    global last_token
    char, skill = parse_char_roll(ctx.message.author.id, arg)
    token = next(roll_token)
    rolls[token] = (char, skill)
    await ctx.message.add_reaction(emoji[token])
    last_token = token

toke_re = re.compile(r'\s*(?:\$([a-zA-Z]))?(.*)')
@bot.command()
async def vs(ctx, *, arg=''):
    global last_token
    token, remain = toke_re.match(arg).groups()
    if not token:
        token = last_token
    token = slugify(token)
    char, skill = rolls[token]
    del rolls[token]

    await ctx.send("Rolling {} against {}.{}".format(remain, char, skill))

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