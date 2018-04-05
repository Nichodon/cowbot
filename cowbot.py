import discord
import asyncio
from time import gmtime, strftime
from discord.utils import *


schedule = []
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


class Class(discord.Client):

    @asyncio.coroutine
    def on_message(self, message):

        # Datum syntax
        # 0: Player name
        # 1: Size

        if message.content.startswith('//cow'):
            command = message.content.split(' ')[1]
            with open('data.txt') as thing:
                contents = thing.readlines()
            found = False
            output = ''
            for line in contents:
                datum = line.split(':')
                if datum[0] == message.author.name:
                    if command == 'buy':
                        output += line
                        yield from client.send_message(message.channel, 'You already have a cow!')
                        found = True
                    elif command == 'feed':
                        output += datum[0] + ':' + str(int(datum[1]) + 5) + ':\n'
                        yield from client.send_message(message.channel, 'You fed your cow.')
                    elif command == 'sell':
                        yield from client.send_message(message.channel, 'You sold your cow. :(')
                else:
                    output += line
            if command == 'buy' and not found:
                output += message.author.name + ':10:\n'
                yield from client.send_message(message.channel, 'You bought a cow. :)')
            out = open('data.txt', 'w')
            out.write(output)
            out.close()

        elif message.content.startswith('//help'):
            embed = discord.Embed(description='Schedule: `//s m-d-y` or `//s today`. Example: `//s 3-26-18`\n\n' +
                                              'Indented Text: `//e text` or `//e c=color text`. Color is 6-digit hex.' +
                                              ' Example: `//e c=00cc99 Hello`. I am some indented text!!',
                                  colour=discord.Colour(0x00cc99))
            yield from client.send_message(message.channel, 'If you do not see the help menu below, then you are' +
                                           'probably in a channel that does not allow bots. Please go to another' +
                                           'channel that allows bots.', embed=embed)
        elif message.content.startswith('//close'):
            client.logout()
        elif message.content.startswith('//last'):
            with open('data.txt') as thing:
                yield from client.send_message(message.channel, thing.read())
        elif message.content.startswith('//e '):
            thing = message.content.split('//e ')[1]
            color = '0099cc'
            if thing.startswith('c='):
                color = thing.split(' ')[0][2:]
                thing = thing[9:]
            embed = discord.Embed(colour=discord.Colour(int(color, 16)))
            embed.add_field(name=message.author.name + ' says:', value=thing, inline=True)

            yield from client.delete_message(message)
            yield from client.send_message(message.channel, '**Announcement**', embed=embed)
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
