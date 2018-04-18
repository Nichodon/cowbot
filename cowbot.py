import discord
import asyncio
from time import gmtime, strftime
from datetime import date
from discord.utils import *
import random
import re
import json
from pprint import pprint

import logging
logging.basicConfig(level=logging.INFO)


def get_dict():
    with open('datum.json', 'r') as g:
        return json.load(g)


def set_dict(new):
    with open('datum.json', 'w') as g:
        json.dump(new, g, indent=2)


with open('schedules.txt', 'r') as f:
    schedule = f.readlines()


def compare(t, u):
    t1 = int(t[0][0]) * 60 + int(t[0][1])
    t2 = int(t[1][0]) * 60 + int(t[1][1])
    t3 = int(u[0]) * 60 + int(u[1])
    if t1 < t3 < t2:
        return t2 - t3
    else:
        return -1


def zone(x):
    return str(12 + int(x) - 7 if int(x) < 8 else int(x) - 7)


def last(x):
    return int(x) < 8 and not strftime("%p", gmtime()) == 'PM'


def convert(x):
    split = x.split('-')
    out = [y.split(':') for y in split]
    out[0][0] = str(int(out[0][0]) + 12) if int(out[0][0]) < 6 else out[0][0]
    out[1][0] = str(int(out[1][0]) + 12) if int(out[1][0]) < 6 else out[1][0]
    return out


def bank_get(user):
    out = get_dict().get(user, {}).get('money')
    if out is None:
        return 0
    return out


def bank_set(user, amount):
    bank = get_dict()
    out = bank.get(user, {}).get('money')
    if out is None:
        if bank.get(user) is None:
            bank[user] = {}
        bank[user]['money'] = amount
    else:
        bank[user]['money'] = out + amount
    set_dict(bank)


def cow_get(user):
    out = get_dict().get(user, {}).get('cow')
    if out is None:
        return {}
    return out


def cow_set(user, pet):
    cow = get_dict()
    if cow.get(user) is None:
            cow[user] = {}
    cow[user]['cow'] = pet
    set_dict(cow)


ER_DESIRED = 0.005
# Desired 1cb = Xu

ER_MAX = 0.5
# Highest 1cb = Xu

TOTAL_MONEY = 0
TOTAL_UN = 100000
GOV_MONEY = TOTAL_UN / ER_MAX
ER_UN = 0


def cowbits():
    bank = get_dict()
    total = 0
    people = bank.keys()
    for person in people:
        total += bank[person]['money']
    return total


def universal():
    global TOTAL_MONEY
    global ER_UN

    total = cowbits()

    TOTAL_MONEY = total / 100
    ER_UN = 1 / (GOV_MONEY + TOTAL_MONEY) * TOTAL_UN


class Class(discord.Client):

    waiting = False

    @asyncio.coroutine
    def on_ready(self):
        yield from client.change_presence(game=discord.Game(name='//help | In development! Things might break!'))

    @asyncio.coroutine
    def on_message(self, message):
        if message.content.startswith('//daily'):
            thing = get_dict()
            daily = thing.get(message.author.name, {}).get('daily')
            if daily is None or daily != str(date.today()):
                bank_set(message.author.name, 100)
                thing[message.author.name]['daily'] = str(date.today())
                set_dict(thing)
                yield from client.send_message(message.channel, 'Here\'s your daily 100cb!')
            else:
                yield from client.send_message(message.channel, 'You have to wait another day!')

        elif message.content.startswith('//econ'):
            universal()
            yield from client.send_message(message.channel, 'Total cb: ' + str(cowbits()) + '\nExchange: ' + str(ER_UN))

        elif message.content.startswith('//bank ') and len(message.mentions) > 0:
            yield from client.send_message(message.channel,
                                           message.mentions[0].name + ' has ' +
                                           str(int(bank_get(message.mentions[0].name))) + 'cb')

        elif message.content.startswith('//echo ') and not message.author.bot:
            if message.content[7:] == '':
                yield from client.send_message(message.channel, 'Er, that\'s a bad echo.')
                return
            yield from client.send_message(message.channel, message.content[7:])

        elif not message.author.bot and message.content.startswith('//convert '):
            data = message.content.split(' ')
            amount = float(data[2])

            if bank_get(message.author.name) < amount:
                yield from client.send_message(message.channel, 'You are too poor to make that conversion.')
                return

            bot = discord.User()
            if data[1] == 'mn':
                bot = yield from client.get_user_info('427609586032443392')
            elif data[1] == 'bcbw':
                bot = yield from client.get_user_info('393248490739859458')

            universal()
            amount *= ER_UN

            embed = discord.Embed(title='convert',
                                  description='<@' + message.author.id + '> ' + str(amount))
            yield from client.send_message(client.get_channel(id='433441820102361110'), bot.mention, embed=embed)

            success = yield from client.wait_for_reaction(emoji="👌", user=bot, timeout=15)
            if not success:
                yield from client.send_message(message.channel,
                                               bot.mention + ' did not respond, so no conversion was made.')
            else:
                yield from client.send_message(message.channel, 'A conversion was made!')
                bank_set(message.author.name, -float(data[2]))

        if len(message.mentions) > 0:
            if message.author.name != 'cowbot' and len(message.embeds) == 0 and message.mentions[0].name == 'cowbot':
                yield from client.send_message(message.channel, 'Hi! Do `//help` for a list of commands.')

            elif message.author.name != 'cowbot' and message.mentions[0].name == 'cowbot':
                if message.embeds[0]["title"] == 'convert':
                    regex = re.compile(r'<@!?(\d+)>')
                    user = yield from client.get_user_info(regex.search(message.embeds[0]["description"]).group(1))
                    amount = float(message.embeds[0]["description"].split(' ')[1])
                    universal()
                    amount /= ER_UN

                    bank_set(user.name, amount)

                    yield from client.add_reaction(message, '\U0001F44C')

        if message.content.startswith('//cow'):
            command = message.content.split(' ')[1]
            print(command)

            difference = 0
            money = bank_get(message.author.name)
            cow = cow_get(message.author.name)

            if not cow:
                if command == 'buy':
                    if money >= 500:
                        cow_set(message.author.name, {'size': 10})
                        difference = -500
                        yield from client.send_message(message.channel, 'You spent 500cb to buy a cow.')
                    else:
                        yield from client.send_message(message.channel, 'You are too poor to buy a cow!')
                else:
                    yield from client.send_message(message.channel, 'You don\'t have a cow!')
            else:
                if command == 'size':
                    yield from client.send_message(message.channel, 'Your cow is of size ' + str(cow['size']) + '.')
                elif command == 'feed':
                    if money >= 5:
                        difference = -5
                        yield from client.send_message(message.channel, 'You spent 5cb to feed your cow.')
                    else:
                        yield from client.send_message(message.channel, 'You are too poor to feed your cow!')
                elif command == 'sell':
                    difference = 500
                    cow_set(message.author.name, {})
                    yield from client.send_message(message.channel, 'You sold your cow for 500cb.')
                else:
                    yield from client.send_message(message.channel, 'Wait what?')

            bank_set(message.author.name, difference)

        elif message.content.startswith('//help'):
            embed = discord.Embed(description='**Schedule**: `//s <date>`\n' +
                                              '\t\tShows Gunn Alternate Schedules\n' +
                                              '\t\t`date`: A date in the format `m-d-y` or "`today`". ' +
                                              '`y` is two digit.\n' +
                                              '\t\tExample: `//s 3-28-18`\n\n' +
                                              '**Indent**: `//indent [c=color] <text>`\n' +
                                              '\t\tPuts text in a pretty box\n' +
                                              '\t\t`color`: A 6-digit RGB Hex.\n' +
                                              '\t\tExample: `//indent c=00cc99 I am some indented text!`\n\n' +
                                              '**Poll**: `//poll ["num"] [text]`\n' +
                                              '\t\tGenerates a poll through reactions\n' +
                                              '\t\t`"num"`: If present, will generate one to ten. ' +
                                              'If absent, will generate yes / no.\n' +
                                              '\t\tExample: `//poll num How many cows should we buy?`\n\n' +
                                              '**Trump Tweet**: `//covfefe [person]`\n' +
                                              '\t\tMakes Trump tweet about someone\n' +
                                              '\t\t`person`: A victim of a Trump attack\n' +
                                              '\t\tExample: `//covfefe CNN`\n\n' +
                                              '**BANK**: do `//bh` for more info!',
                                  colour=discord.Colour(0x00cc99))
            yield from client.send_message(message.channel, 'If you do not see the help menu below, then you are' +
                                           ' probably in a channel that does not allow bots. Please go to another' +
                                           ' channel that allows bots.', embed=embed)

        elif message.content.startswith('//bh'):
            embed = discord.Embed(description='**Cowbot Banking**\n' +
                                              'Cowbot has a very experimental banking system that communicates with ' +
                                              'moofy and discow! The currency is the cowbit (cb). To see someone\'s ' +
                                              'bank, do `//bank <mention>`. To take money out of the cowbot bank ' +
                                              '(the cowbank), do `//convert <currency> <amount>`. Supported ' +
                                              'currencies are `bcbw` for bitcoin but worse, and `mn` for mooney.',
                                  colour=discord.Colour(0x00cc99))
            yield from client.send_message(message.channel, 'If you do not see the help menu below, then you are' +
                                           ' probably in a channel that does not allow bots. Please go to another' +
                                           ' channel that allows bots.', embed=embed)

        elif message.content.startswith('//covfefe '):
            target = message.content.split('//covfefe ')[1]
            with open('covfefe.txt') as covfefe:
                lines = covfefe.readlines()
                tweet = discord.Embed(title='',
                                      description=lines[random.randint(0, 19)].replace('[]', target) + '\n\n' +
                                                  '\U0001f5e8\ufe0f ' + str(random.randint(10, 50)) + 'K   ' +
                                                  '\U0001F503 ' + str(random.randint(10, 50)) + 'K   ' +
                                                  '\U0001F499 ' + str(random.randint(50, 250)) + 'K')
                tweet.set_author(name='Donald J. Trump @realDonaldTrump',
                                 icon_url='https://pbs.twimg.com/profile_images/' +
                                          '874276197357596672/kUuht00m_400x400.jpg')
                yield from client.send_message(message.channel, 'Someone just got covfefed:', embed=tweet)

        elif message.content.startswith('//poll num '):
            yield from client.add_reaction(message, '\u0030\u20e3')
            yield from client.add_reaction(message, '\u0031\u20e3')
            yield from client.add_reaction(message, '\u0032\u20e3')
            yield from client.add_reaction(message, '\u0033\u20e3')
            yield from client.add_reaction(message, '\u0034\u20e3')
            yield from client.add_reaction(message, '\u0035\u20e3')
            yield from client.add_reaction(message, '\u0036\u20e3')
            yield from client.add_reaction(message, '\u0037\u20e3')
            yield from client.add_reaction(message, '\u0038\u20e3')
            yield from client.add_reaction(message, '\u0039\u20e3')
            yield from client.add_reaction(message, '\U0001f51f')

        elif message.content.startswith('//poll '):
            yield from client.add_reaction(message, '\u2705')
            yield from client.add_reaction(message, '\u274e')

        elif message.content.startswith('//indent '):
            thing = message.content.split('//indent ')[1]
            color = '00cc99'
            if thing.startswith('c='):
                color = thing.split(' ')[0][2:]
                thing = thing[9:]
            try:
                embed = discord.Embed(colour=discord.Colour(int(color, 16)))
            except ValueError:
                yield from client.send_message(message.channel, 'Er, that\'s a bad color.')
                return
            embed.add_field(name=message.author.name + ' says:', value=thing, inline=True)

            try:
                yield from client.send_message(message.channel, '**Announcement**', embed=embed)
                yield from client.delete_message(message)
            except discord.errors.Forbidden:
                yield from client.send_message(message.channel, 'Er, I don\'t have all the perms to do that.')
            except discord.errors.HTTPException:
                yield from client.send_message(message.channel, 'Er, that\'s a bad color.')

        elif message.content.startswith('//s '):
            try:
                day = message.content.split('//s ')[1]
                if day == 'today':
                    day = strftime("%m-%d-%y", gmtime())

                split = day.split('-')
                split = [str(int(x)) for x in split]
            except ValueError:
                yield from client.send_message(message.channel, 'Er, that\'s a bad date.')
                return

            if last(strftime("%I", gmtime())) and message.content == '//s today':
                split[1] = str(int(split[1]) - 1)

            if len(split) < 3:
                yield from client.send_message(message.channel, 'Er, that\'s a bad date.')
                return

            periods = ''
            times = ''
            left = 'Nothing is happening right now...'
            now = [zone(strftime("%I", gmtime())), strftime("%M", gmtime())]

            do = False
            for line in schedule:
                if line.startswith('$$'):
                    do = False
                if line == '$$' + split[0] + '/' + split[1] + '/' + split[2] + '\n':
                    do = True
                elif do:
                    if line == 'None\n':
                        yield from client.send_message(message.channel, 'Nothing for that day!')
                        return
                    elif line == 'Default\n':
                        yield from client.send_message(message.channel, 'Regular schedule that day!')
                        return
                    periods += line.split('[')[1].split(']')[0] + '\n'
                    span = line.split('(')[1].split(')')[0]
                    times += span + '\n'
                    until = compare(convert(span), now)
                    if message.content == '//s today':
                        left = 'Period ends in ' + str(until) + ' minutes.' if until > -1 else left

            embed = discord.Embed(title=split[0] + '/' + split[1] + '/' + split[2] + ', ' + now[0] + ':' + now[1],
                                  description=left, colour=discord.Colour(0xff0066))
            embed.set_footer(text='By Brandon, txt file provided by Timothy.')
            embed.set_author(name='CowBot Gunn Schedule')
            embed.add_field(name='Periods', value=periods, inline=True)
            embed.add_field(name='Times', value=times, inline=True)
            embed.set_thumbnail(
                url="https://gunn.pausd.org/sites/default/files/oa_features/images/gunn%20athletics%20logo.gif")
            try:
                yield from client.send_message(message.channel, '**The Schedule:**', embed=embed)
            except discord.errors.HTTPException:
                yield from client.send_message(message.channel, 'Er, that\'s a bad date.')


client = Class()
with open('supersecrettoken') as f:
    client.run(f.read())
