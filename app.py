import discord
import logging
import re
from slugify import slugify

logging.basicConfig(level=logging.INFO)

log = logging.getLogger('rfs')


users = {
    'AJMansfield#5742' : {
        'active': 'Muuug',
        'chars': [
            'Muuug'
        ],
    }
}
chars = {
    'Muuug' : {
        'xp' : 0,
        'skills' : {
            'do-anything' : 1
        },
    },
}

client = discord.Client()
@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return
    
    log.info("Author's ID is {0.author.id}.".format(message))

    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)

@client.event
async def on_ready():
    log.info('Logged in as')
    log.info(client.user.name)
    log.info(client.user.id)
    log.info('------')

from keys import keys
log.info("key is "+keys['discord-token'])

client.run(keys['discord-token'])