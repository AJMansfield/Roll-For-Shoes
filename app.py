import discord
import discord
from discord.ext import commands
# from discord.utils import get
import logging
import re
from slugify import slugify
import dice
import random
import psycopg2
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

import asciitree
from collections import OrderedDict

from data import engine, Base, Player, Char, Skill

logging.basicConfig(level=logging.INFO)

log = logging.getLogger('rfs')
bot = commands.Bot('!')

Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def regional_indicator(c:str):
    return chr(ord(c.strip().lower()[0]) - ord('a') + ord('🇦'))

def token_generator():
    while True:
        for c in 'abcdefghijklmnopqrstuvwxyz':
            yield c
roll_token = token_generator()
last_token = 'a'
rolls = {
    # <token>: (<skill_id>, <comment>, <context>)
}

def get_or_create_player(session, ctx):
    player = session.query(Player).get(ctx.message.author.id)
    if not player:
        player = Player(id=ctx.message.author.id, name=ctx.message.author.mention)
        session.add(player)
    return player

def get_char(session, ctx, name):
    if name:
        slug = slugify(name)
        char = session.query(Char).filter(Char.slug == slug).one()
    else:
        char = get_or_create_player(session, ctx).char
    return char

def get_skill(session, ctx, char_name, skill_name):
    skill_slug = slugify(skill_name)
    if not skill_slug:
        skill_slug = 'do-anything'
    if char_name:
        char_slug = slugify(char_name)
        skill = session.query(Skill).join(Skill.char).filter(Char.slug == char_slug, Skill.slug == skill_slug).one()
    else:
        skill = session.query(Skill).join(Skill.char).join(Char.players).filter(Player.id == ctx.message.author.id, Skill.slug == skill_slug).one()
    return skill

def get_tree(session, skill, fmt=lambda sk: '{0.id}'.format(sk)):
    d = OrderedDict()
    for sub in skill.children:
        d[fmt(sub)] = get_tree(session, sub, fmt)
    return d

tree_re = re.compile(r'(\W*?)( *[-*_\w].*)')
def make_skilltree(session, char, fmt=lambda sk: '{0.id}'.format(sk)):
    tr = asciitree.LeftAligned(
        draw = asciitree.BoxStyle(
            gfx = asciitree.drawing.BOX_HEAVY,
            horiz_len=0,
            indent=0,
            label_space=1
        )
    )
    space_char = '\u2001' # '\u2000' for BOX_LIGHT

    root_skills = session.query(Skill).filter(Skill.char == char, Skill.parent == None).order_by(Skill.created)
    d = OrderedDict()
    for skill in root_skills:
        d[fmt(skill)] = get_tree(session, skill, fmt)
    msg = tr(d)

    return '\n'.join(a.replace(' ', space_char) + b for a,b in (tree_re.match(l).groups() for l in msg.split('\n')))

@bot.command(
    pass_context = True,
    aliases = ['new'],
)
async def newchar(ctx, *, arg=''):
    """Create new character.

    Creates a new character with the given name, and sets it as your default character.

    Usage:
        !newchar CHARACTER
    Examples:
        !newchar Muuug
        !newchar Doug Doug  
    """
    arg = arg.strip()
    try:
        with session_scope() as session:
            player = get_or_create_player(session, ctx)
            char = Char(name=arg, slug=slugify(arg))
            player.char = char
            session.add(char)
            do_anything = Skill(char=char)
            session.add(do_anything)
    except:
        log.exception("newchar")
        await bot.add_reaction(ctx.message, '⁉')
    else:
        await bot.add_reaction(ctx.message, '⏫')

@bot.command(
    pass_context = True,
    aliases = ['use'],
)
async def usechar(ctx, *, arg=''):
    """Set character as default.

    Sets the character with the given name as your default character.

    Usage:
        !usechar CHARACTER
    Examples:
        !usechar Muuug
        !usechar Doug Doug  
    """
    arg = arg.strip()
    try:
        with session_scope() as session:
            player = get_or_create_player(session, ctx)
            char = get_char(session, ctx, arg)
            player.char = char
    except:
        log.exception("usechar")
        await bot.add_reaction(ctx.message, '⁉')
    else:
        await bot.add_reaction(ctx.message, '⏫')

level_re = re.compile(r'\s*(?:([^.>#0-9]*)\.)?([^.>#0-9]*)\s*>\s*([^.>#0-9]*)\s*#?.*')
@bot.command(
    pass_context = True,
    aliases = ['level', 'up', 'upgrade'],
)
async def levelup(ctx, *, arg=''):
    """Level up a skill.

    Levels an existing skill and adds a new subskill to your character, automatically deducting the appropriate amount of XP.

    Usage:
        !levelup [CHARACTER  .] [PARENT_SKILL] > NEW_SKILL [# COMMENT]
    Examples:
        !levelup axe > chop tree
        !levelup Doug Doug . do anything > run away  # level up a different character 
        !levelup > axe                               # defaults to <current char>.do-anything
    """
    try:
        char_name, skill_name_from, skill_name_to = level_re.match(arg).groups()
        with session_scope() as session:
            char = get_char(session, ctx, char_name)
            base = get_skill(session, ctx, char_name, skill_name_from)
            assert base.xp is not None
            assert char.xp >= base.xp
            session.add(Skill(name=skill_name_to, slug=slugify(skill_name_to), level=base.level+1, char=char, parent=base))
            base.xp = None
    except:
        log.exception("upgrade")
        await bot.add_reaction(ctx.message, '⁉')
    else:
        await bot.add_reaction(ctx.message, '⏫')

@bot.command(
    pass_context = True,
    aliases = ['character', 'c', 'skills'],
)
async def char(ctx, *, arg=''):
    """Show a character's stats.

    Displays the remaining XP total and skill tree for a character.
    Skills that have the potential for being leveled up will show the XP cost in parenthesis after the skill.
    Skills with pending level-ups from rolling all 6's will instead show an exclamation point.

    Usage:
        !char [CHARACTER]
    Examples:        
        !char Doug Doug     # can explicitly specify the character
        !char               # defaults to current character
    """
    arg = arg.strip()
    try:
        with session_scope() as session:
            char = get_char(session, ctx, arg)
            embed = discord.Embed(
                title=char.name,
                description="**XP:** {0.xp}".format(char)
            )
            embed.add_field(
                name="Skills", 
                value=make_skilltree(session, char, 
                    fmt=lambda sk: '**{0.name} {0.level}** {1}'.format(sk, skill_xp_msg(sk))),
                inline=False,
            )
        await bot.say(embed=embed)
    except:
        log.exception("skills")
        await bot.add_reaction(ctx.message, '⁉')

def skill_xp_msg(skill):
    numbers = {
        0: ':zero:',
        1: ':one:',
        2: ':two:',
        3: ':three:',
        4: ':four:',
        5: ':five:', 
        6: ':six:',
        7: ':seven:',
        8: ':eight:',
        9: ':nine:',
        10: ':keycap_ten:',
    }
    if skill.xp is None:
        return ''
    elif skill.xp == 0:
        return '(!)' # '⬆'
    # elif skill.xp in numbers:
    #     return numbers[skill.xp]
    else:
        return '({})'.format(skill.xp)

@bot.command(
    pass_context = True,
    aliases = ['r'],
)
async def roll(ctx, *, arg=''):
    """Roll for a skill check.

    Begins a skill check using the specified skill.
    If not specified, the command will use the current character's do-anything skill.

    The bot will react to this command with a letter to indicate it's waiting for the GM or another character to oppose the check with `!vs` or `!dc`.
    This letter is used as a "token" to allow later commands to specify which of multiple rolls they are opposing.

    Usage:
        !roll [CHARACTER .] [SKILL] [# COMMENT]
    Examples:        
        !roll axe                  # defaults to current character
        !roll Doug Doug.run away   # can specify another character
        !roll                      # defaults to using the do-anything skill
    """
    global last_token
    try:
        with session_scope() as session:
            skill, comment = parse_char_roll(session, ctx, arg)
            token = next(roll_token)
            rolls[token] = (skill, comment, ctx)
            await bot.add_reaction(ctx.message, regional_indicator(token))
            last_token = token
    except:
        log.exception("roll")
        await bot.add_reaction(ctx.message, '⁉')

toke_re = re.compile(r'\s*(?:([A-Z])\s+)?(.*)')
@bot.command(
    pass_context = True,
    aliases = ['v'],
)
async def vs(ctx, *, arg=''):
    """Oppose a skill check with a character skill.

    Rolls a given skill check against a check previously started with `!roll`, and outputs the result.
    The semantics for specifying which skill to use are the same as for `!roll`.

    By default the bot will oppose the most-recent skill check.
    To specify which roll you're opposing, add the token letter as the first argument.
    Otherwise, the bot will use the most recent roll.
    
    This command does not allow characters to oppose their own rolls, even if rolled by a different player.
    Different characters rolled by the same player are allowed however.

    Usage:
        !vs [TOKEN] [CHARACTER .] [SKILL] [# COMMENT]
    Examples:        
        !vs P               # oppose the roll P with the current character's do anything skill
        !vs Dorg Dorg.run   # oppose the most recent roll with Dorg Dorg's run skill.
    """
    global last_token
    try:
        with session_scope() as session:
            token, arg = toke_re.match(arg).groups()
            if not token:
                token = last_token
            token = slugify(token)

            a_skill, a_comment, a_ctx = rolls[token]
            session.add(a_skill)
            # am, ac, ask, message = 

            b_skill, b_comment = parse_char_roll(session, ctx, arg)
            b_ctx = ctx

            if a_skill.char == b_skill.char:
                await bot.add_reaction(b_ctx.message, '⁉')
                return

            ar, arm = roll_skill(a_skill)
            br, brm = roll_skill(b_skill)

            if ar > br:
                winmsg = "{} wins!".format(a_skill.char.name)
                brm += add_xp(b_skill.char)
            elif ar == br:
                winmsg = "tie!"
            else: #ar < br:
                winmsg = "{} wins!".format(b_skill.char.name)
                arm += add_xp(a_skill.char)

            arm += levelmsg(a_skill)
            brm += levelmsg(b_skill)

            embed = discord.Embed(title=winmsg, description="{} {}\n{} {}".format(a_comment, arm, b_comment, brm))

            await bot.remove_reaction(a_ctx.message, regional_indicator(token), bot.user)
            del rolls[token]
            await bot.say(embed=embed)
    except:
        log.exception("vs")
        await bot.add_reaction(ctx.message, '⁉')

dice_re = re.compile(r'([^#]*)#?(.*)')
@bot.command(
    pass_context = True,
)
async def dc(ctx, *, arg=''):
    """Oppose a skill check with a fixed value or die roll.

    Rolls a given die expression against a check previously started with `!roll`, and outputs the result.
    This command supports general die expressions including arithmetic operations.

    By default the bot will oppose the most-recent skill check.
    To specify which roll you're opposing, add the token letter as the first argument.
    Otherwise, the bot will use the most recent roll.

    Usage:
        !dc [TOKEN] DIE_EXPRESSION [# COMMENT]
    Examples:        
        !dc 4d6       # roll 4d6 against the most recent skill roll
        !dc X 28      # oppose roll X with a fixed DC of 28
        !dc 2d6 + 5   # compute 2d6+5 and oppose the most recent roll with the result

    """
    global last_token
    try:
        with session_scope() as session:
            token, remain = toke_re.match(arg).groups()
            if not token:
                token = last_token
            token = slugify(token)
            a_skill, a_comment, a_ctx = rolls[token]
            session.add(a_skill)

            b_die, b_comment = dice_re.match(remain).groups()

            try:
                br = int(dice.roll(b_die))
                brm = "DC `{}` = {}".format(b_die, br)
            except dice.DiceBaseException:
                await bot.add_reaction(ctx.message, '⁉')
                return

            ar, arm = roll_skill(a_skill)

            if ar > br:
                winmsg = "{} suceeds!".format(a_skill.char.name)
            else: #ar <= br:
                winmsg = "{} fails!".format(a_skill.char.name)
                arm += add_xp(a_skill.char)
            
            arm += levelmsg(a_skill)

            embed = discord.Embed(title=winmsg, description="{} {}\n{} {}".format(a_comment, arm, b_comment, brm))

            await bot.remove_reaction(a_ctx.message, regional_indicator(token), bot.user)
            del rolls[token]
            await bot.say(embed=embed)
    except:
        log.exception("dc")
        await bot.add_reaction(ctx.message, '⁉')

char_re = re.compile(r'\s*(?:([^.#0-9]*)\.)?([^.#0-9]*)\s*#?\s*(.*)')
def parse_char_roll(session, ctx, arg):
    char_name, skill_name, comment = char_re.match(arg).groups()
    skill = get_skill(session, ctx, char_name, skill_name)
    return skill, comment

def roll_skill(skill):
    roll = [random.randint(1,6) for _ in range(skill.level)]
    
    xp_left = sum(0 if x == 6 else 1 for x in roll)
    if skill.xp is None or skill.xp > xp_left:
        skill.xp = xp_left

    rollstr = ' '.join(str(x) for x in roll)
    value = sum(roll)
    
    rollmsg = "({}.{}): `{}d6` = [{}] = {}".format(skill.char.slug, skill.slug, skill.level, rollstr, value)
    return value, rollmsg

def add_xp(char):
    char.xp += 1
    return " [+1 XP]"

def levelmsg(skill):
    if skill.xp == 0:
        return " [level up!]"
    elif skill.xp is None:
        return ""
    else:
        return " [{}/{} to level up]".format(skill.char.xp, skill.xp)

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
if __name__ == '__main__':
    bot.run(keys['discord-token'])