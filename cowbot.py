import discord
import asyncio
from time import gmtime, strftime


def compare(t, u):
    t1 = int(t[0][0]) * 60 + int(t[0][1])
    t2 = int(t[1][0]) * 60 + int(t[1][1])
    t3 = int(u[0]) * 60 + int(u[1])
    if t1 < t2 < t3:
        return t3 - t2
    else:
        return -1


def zone(x):
    return str(12 + int(x) - 7 if int(x) < 8 else int(x) - 7)


def last(x):
    return int(x) < 8


def convert(x):
    split = x.split('-')
    out = [y.split(':') for y in split]
    out[0][0] = str(int(out[0][0]) + 12) if int(out[0][0]) < 6 else out[0][0]
    out[1][0] = str(int(out[1][0]) + 12) if int(out[1][0]) < 6 else out[1][0]
    return out


class Class(discord.Client):

    @asyncio.coroutine
    def on_message(self, message):
        if message.content.startswith('//help'):
            embed = discord.Embed(description='Schedule: To see a schedule for a certain date,' +
                                              'type `//s m-d-y` or `//s today`. ' + 'Example: `//s 3-26-18`',
                                  colour=discord.Colour(0x00cc99))
            yield from client.send_message(message.channel, 'Help:', embed=embed)
        elif message.content.startswith('//g'):
            pass
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

            with open('schedules.txt', 'r') as f:
                do = False
                for line in f.readlines():
                    if line.startswith('$$'):
                        do = False
                    if line == '$$' + split[0] + '/' + split[1] + '/' + split[2] + '\n':
                        do = True
                    elif do:
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
