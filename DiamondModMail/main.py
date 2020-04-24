import asyncio
import json
import os
import random
import time
import traceback

import discord
from discord.ext import commands
from discord.utils import get

from utils.customCommands import Command
from utils.moderation import User

config = json.load(open(os.getcwd()+'/config/config.json'))

SuccessEmbedColor = int(config['Embeds']['Moderation']['Success'], 16)
FailEmbedColor = int(config['Embeds']['Moderation']['Fail'], 16)

bot = commands.AutoShardedBot(command_prefix=config['Bot']['Prefix'], case_insensitive=True)
bot.config = json.load(open(os.getcwd()+'/config/config.json'))
bot.remove_command('help')

initial_extensions = [
                "cogs.moderation",
                "cogs.help",
                "cogs.error"
                    ]

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f"Failed to load extension {extension}.")
            traceback.print_exc()


@bot.event
async def on_message(message):
    bot.config = json.load(open(os.getcwd() + '/config/config.json'))
    if message.author == bot.user or message.author.bot:
        return

    if not message.guild:
        guild = bot.get_guild(bot.config["Moderation"]["GuildID"])

        activeUser = User(bot=bot, ctx=message)
        activeUser.update_value("last_mod_mail", time.time())
        activeUser.update_value("closing_channel", 0)
        activeUser.close()

        embed = discord.Embed(title="Mail Received", color=SuccessEmbedColor)
        embed.add_field(name=f"Sent by {message.author.name} ({message.author.id})", value=f"{message.content}")
        embed.set_footer(text=f"Sent at {message.created_at} | {bot.command_prefix}reply <message>")

        category = get(guild.categories, id=bot.config['Moderation']['MailCategoryID'])
        channel = get(guild.channels, name=str(message.author.id))
        everyone = get(guild.roles, name="@everyone")
        if not category:
            category = await guild.create_category(bot.config['Moderation']['MailCategoryName'])
            await category.set_permissions(everyone, read_messages=False, send_messages=False)

            bot.config['Moderation'].update({"MailCategoryID": category.id})
            bot.config['Moderation'].update({"MailCategoryName": category.name})

            with open(os.getcwd() + '/config/config.json', "w") as jsonFile:
                json.dump(bot.config, jsonFile, indent=4)

        if not channel:
            channel = await guild.create_text_channel(str(message.author.id), category=category)
            await channel.set_permissions(everyone, read_messages=False, send_messages=False)
        await channel.send(embed=embed)

        activeUser = User(bot=bot, ctx=message)
        if not activeUser.out_going_mail:
            async with message.author.dm_channel.typing():
                activeUser.update_value("out_going_mail", 1)
                while True:
                    try:
                        message = await bot.wait_for('message', check=lambda msg: msg.author.id == message.author.id, timeout=float(config["Moderation"]["MailRespondTime"]))
                        continue
                    except Exception:
                        embed = discord.Embed(color=SuccessEmbedColor)
                        embed.add_field(name="─────────────", value="The staff team has received your message!")
                        embed.set_footer(text="Abusing this message system may get you banned without warning, this is your warning")
                        await message.author.send(embed=embed)
                        activeUser.update_value("out_going_mail", 0)
                        activeUser.close()
                        break
    else:
        if message.content.startswith(bot.command_prefix):
            customCommands = Command(bot=bot)
            customCommandName = message.content.lower().split(bot.command_prefix)[1]
            customCommandName = customCommandName.split(" ")[0]
            other_args = message.content.lower().split(" ")[1:]
            for user in message.mentions:
                if str(user.id) == message.channel.name:
                    return await user.send(customCommands.commands[customCommandName])
            for user in other_args:
                try:
                    check_user = get(message.guild.members, id=int(user))
                except ValueError:
                    continue
                if user == message.channel.name:
                    return await check_user.send(customCommands.commands[customCommandName])
            if customCommandName in customCommands.commands:
                return await message.channel.send(customCommands.commands[customCommandName])

        await bot.process_commands(message)


# noinspection PyTypeChecker
async def status_changer():
    """
        Setting `Playing ` status
        await bot.change_presence(activity=discord.Game(name="a game"))

        Setting `Streaming ` status
        await bot.change_presence(activity=discord.Streaming(name="My Stream", url=my_twitch_url))

        Setting `Listening ` status
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="a song"))

        Setting `Watching ` status
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="a movie"))
    """
    playing = [discord.Game(name="with management")]
    streaming = []
    listening = [discord.Activity(type=discord.ActivityType.listening, name="for DM's")]
    watching = [discord.Activity(type=discord.ActivityType.watching, name="for cries of help"), discord.Activity(type=discord.ActivityType.watching, name="for the change")]
    statuses = playing+streaming+listening+watching
    while True:
        if not bot.is_ready():
            continue
        if bot.is_closed():
            return
        await bot.change_presence(activity=random.choice(statuses))
        await asyncio.sleep(bot.config['Bot']['StatusTimer'])


@bot.event
async def on_ready():
    print("------------------------------------")
    print("Bot Name: " + bot.user.name)
    print("Bot ID: " + str(bot.user.id))
    print("Discord Version: " + discord.__version__)
    print("------------------------------------")

    await status_changer()
    bot.loop.run_until_complete(status_changer())

bot.run(config['Bot']['Token'])
