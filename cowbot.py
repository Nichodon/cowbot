import discord
import asyncio
from time import gmtime, strftime
from discord.utils import *
import random
import re

import logging
logging.basicConfig(level=logging.INFO)


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
    with open('money.txt') as bank:
        money = bank.readlines()

    found = False
    for stuff in money:
        datum = stuff.split(':')
        if datum[1] == user:
            print(datum[2])
            return float(datum[2])
    if not found:
        print(0)
        return 0


def bank_set(user, amount):
    with open('money.txt') as bank:
        money = bank.readlines()

    found = False
    again = ''
    for stuff in money:
        datum = stuff.split(':')
        if datum[1] == user:
            again += ':' + user + ':' + str(float(datum[2]) + amount) + ':\n'
            found = True
        else:
            again += stuff
    if not found:
        again += ':' + user + ':' + str(amount) + ':\n'

    put = open('money.txt', 'w')
    put.write(again)
    put.close()


ER_DESIRED = 0.005
# Desired 1cb = Xu

ER_MAX = 0.5
# Highest 1cb = Xu

TOTAL_NORMAL = 20000000
# Normal bot total

TOTAL_MONEY = 0
TOTAL_UN = TOTAL_NORMAL / ER_DESIRED
GOV_MONEY = TOTAL_UN / ER_MAX
ER_UN = 0


def universal():
    global TOTAL_MONEY
    global ER_UN

    total = 0
    with open('money.txt') as bank:
        money = bank.readlines()

    for stuff in money:
        datum = stuff.split(':')
        total += float(datum[2])

    TOTAL_MONEY = total / 100
    ER_UN = 1 / (GOV_MONEY + TOTAL_MONEY) * TOTAL_UN


class Class(discord.Client):

    waiting = False

    @asyncio.coroutine
    def on_ready(self):
        yield from client.change_presence(game=discord.Game(name='Being worked on right now, some things might be broken!'))

    @asyncio.coroutine
    def on_message(self, message):
        if message.content.startswith('//echo '):
            yield from client.send_message(message.channel, message.content.split('//echo ')[1])
        if not message.author.bot and message.content.startswith('//convert '):
            data = message.content.split(' ')
            amount = float(data[2])

            with open('money.txt') as bank:
                money = bank.readlines()

            found = False
            for stuff in money:
                datum = stuff.split(':')
                if datum[1] == message.author.name:
                    if int(datum[2]) < amount:
                        yield from client.send_message(message.channel, 'You are too poor for that!')
                        return
                    found = True
            if not found:
                yield from client.send_message(message.channel, 'You are too poor for that!')
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
            yield from client.send_message(message.channel, bot.mention, embed=embed)

            success = yield from client.wait_for_reaction(emoji="👌", user=bot, timeout=15)
            if not success:
                yield from client.send_message(message.channel,
                                               bot.mention + ' did not respond, so no conversion was made.')
            else:
                yield from client.send_message(message.channel, 'Cool.')

                again = ''
                for stuff in money:
                    datum = stuff.split(':')
                    if datum[1] == message.author.name:
                        again += ':' + message.author.name + ':' + str(int(datum[2]) - int(data[2])) + ':\n'
                    else:
                        again += stuff

                put = open('money.txt', 'w')
                put.write(again)
                put.close()
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

                    with open('money.txt') as bank:
                        money = bank.readlines()

                    found = False
                    again = ''
                    for stuff in money:
                        datum = stuff.split(':')
                        if datum[1] == user.name:
                            again += ':' + user.name + ':' + str(int(datum[2]) + amount) + ':\n'
                            found = True
                        else:
                            again += stuff
                    if not found:
                        again += ':' + user.name + ':' + str(amount) + ':\n'

                    put = open('money.txt', 'w')
                    put.write(again)
                    put.close()

                    yield from client.add_reaction(message, '\U0001F44C')

        # Datum syntax
        # 0: Player name
        # 1: Size

        if message.content.startswith('//cow'):
            command = message.content.split(' ')[1]
            with open('data.txt') as thing:
                contents = thing.readlines()
            with open('money.txt') as bank:
                money = bank.readlines()

            dollars = 0

            found = False
            going = []
            for stuff in money:
                datum = stuff.split(':')
                if datum[1] == message.author.name:
                    going.append(stuff)
                    dollars = int(datum[2])
                    found = True
                else:
                    going.append(stuff)
            if not found:
                dollars = 0
                going.append(':' + message.author.name + ':0:\n')

            found = False
            output = ''

            for line in contents:
                datum = line.split(':')
                if datum[1] == message.author.name:
                    if command == 'buy':
                        output += line

                        yield from client.send_message(message.channel, 'You already have a cow!')
                        found = True
                    elif command == 'feed' and dollars > 4:
                        dollars -= 5

                        amount = random.randint(5, 10)
                        if int(datum[2]) + amount < 50:
                            output += ':' + message.author.name + ':' + str(int(datum[2]) + amount) + ':\n'

                            yield from client.send_message(message.channel, 'You fed your cow.')
                        else:
                            yield from client.send_message(message.channel, 'Your cow exploded!!')

                    elif command == 'size':
                        output += line

                        if int(datum[2]) > 40:
                            yield from client.send_message(message.channel, 'Your cow is extreme obese!!')
                        elif int(datum[2]) > 30:
                            yield from client.send_message(message.channel, 'Your cow is pretty fat!')
                        elif int(datum[2]) > 20:
                            yield from client.send_message(message.channel, 'Your cow is looking a bit big.')
                        elif int(datum[2]) > 10:
                            yield from client.send_message(message.channel, 'Your cow is a tad small.')
                        else:
                            yield from client.send_message(message.channel, 'Your cow is starving!')
                    elif command == 'sell':
                        dollars += 490 + int(datum[2])

                        yield from client.send_message(message.channel, 'You sold your cow for ' +
                                                       str(490 + int(datum[2])) + 'cb. :(')
                else:
                    output += line

            if not found:
                if command == 'buy':
                    if dollars > 499:
                        dollars -= 500
                        output += ':' + message.author.name + ':10:\n'

                        yield from client.send_message(message.channel, 'You bought a cow for 500cb. :)')
                    else:
                        yield from client.send_message(message.channel, 'You can\'t afford a cow!')

            out = open('data.txt', 'w')
            out.write(output)
            out.close()

            again = ''
            for stuff in going:
                datum = stuff.split(':')
                if datum[1] == message.author.name:
                    again += ':' + message.author.name + ':' + str(dollars) + ':\n'
                else:
                    again += stuff

            put = open('money.txt', 'w')
            put.write(again)
            put.close()

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
                                              '\t\tExample: `//covfefe CNN`',
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
        elif message.content.startswith('//last'):
            with open('data.txt') as thing:
                yield from client.send_message(message.channel, thing.read())
        elif message.content.startswith('//indent '):
            thing = message.content.split('//indent ')[1]
            color = '00cc99'
            if thing.startswith('c='):
                color = thing.split(' ')[0][2:]
                thing = thing[9:]
            embed = discord.Embed(colour=discord.Colour(int(color, 16)))
            embed.add_field(name=message.author.name + ' says:', value=thing, inline=True)

            yield from client.send_message(message.channel, '**Announcement**', embed=embed)
            yield from client.delete_message(message)
        elif message.content.startswith('//s '):
            date = message.content.split('//s ')[1]
            if date == 'today':
                date = strftime("%m-%d-%y", gmtime())

            split = date.split('-')
            split = [str(int(x)) for x in split]

            if last(strftime("%I", gmtime())) and message.content == '//s today':
                split[1] = str(int(split[1]) - 1)

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
            yield from client.send_message(message.channel, '**The Schedule:**', embed=embed)


client = Class()
with open('supersecrettoken') as f:
    client.run(f.read())
