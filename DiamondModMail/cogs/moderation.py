import asyncio
import json
import os

import discord
from discord.ext import commands
from discord.utils import get

from utils.customCommands import Command
from utils.moderation import User


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        self.bot = bot

        self.SuccessEmbedColor = int(self.config['Embeds']['Moderation']['Success'], 16)
        self.FailEmbedColor = int(self.config['Embeds']['Moderation']['Fail'], 16)

    @staticmethod
    def get_sec(time_str):
        """
        Converts a time frame to seconds
        param time_str: The time to convert to seconds; HH:MM:SS
        """
        try:
            h, m, s = time_str.split(':')
            return int(h) * 3600 + int(m) * 60 + int(s)
        except ValueError:
            return 30 * 60

    async def close_channel(self, ctx, user, original, seconds):
        """
        Closes the channel after X seconds, unless aborted by the user
        :param ctx: The context of how the command was called
        :param user: The users who channel we will close
        :param original: The original time specified in the command to close; HH:MM:SS
        :param seconds: The amount of seconds before closing, computed from original time
        """
        activeUser = User(bot=self.bot, ctx=ctx)
        activeUser.update_value("closing_channel", 1)
        await user.send(f"The moderation team will mark your issue as solved in {original} unless you make a new request")
        await asyncio.sleep(seconds)

        activeUser = User(bot=self.bot, ctx=ctx)
        if activeUser.closing_channel:
            await ctx.channel.delete()

    async def cog_check(self, ctx):
        """
        :param ctx: The context of how the command was called
        """
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        return True

    @commands.has_permissions(manage_messages=True, manage_channels=True)
    @commands.command(name="LogChannel", aliases=['LC'], help="Sets a new channel to send log messages to", usage="LogChannel <channel>")
    async def setLogChannel_CMD(self, ctx, channel: discord.TextChannel):
        """
        :param ctx: The context of how the command was called
        :param channel: The new channel to log
        """
        self.config['Moderation'].update({"DefaultLogChannel": channel.id})  # Sets the new ModMail delivery channel
        with open(os.getcwd() + '/config/config.json', "w") as jsonFile:
            json.dump(self.config, jsonFile, indent=4)

        embed = discord.Embed(title="Logging Channel Set!", color=self.SuccessEmbedColor)
        embed.add_field(name="The Logging channel has changed to...", value=f"{channel.mention}")
        embed.set_footer(text=f"Changed by {ctx.author.id}")
        modLogs = ctx.guild.get_channel(self.config['Moderation']['DefaultLogChannel'])
        await modLogs.send(embed=embed)  # Sens the embed to the log channel

        message = await ctx.send(":thumbsup:")  # Sends a temp thumbs up and deletes both the user message and the thumbs up
        await ctx.message.delete(delay=10)
        await message.delete(delay=10)

    @commands.has_permissions(manage_messages=True, manage_channels=True)
    @commands.command(name="Reply", aliases=["Message", "Respond"], help="Sends a reply to a user", usage="Reply <user> <message>")
    async def sendReply_CMD(self, ctx, *, response=None):
        """
        :param ctx: The context of how the command was called
        :param response: The message you want to send
        """
        if not response:
            return await ctx.send(":thumbsdown:")
        try:
            user = get(ctx.guild.members, id=int(ctx.channel.name))
        except ValueError:
            return
        if not user:
            return
        embed = discord.Embed(title=ctx.author.top_role.name, color=self.SuccessEmbedColor)
        embed.add_field(name=f"─────────────", value=f"{response}")
        embed.set_footer(text=f"Sent by {ctx.author.name}")
        await user.send(embed=embed)  # Sends the embed to the log channel
        await ctx.send(":thumbsup:")

    @commands.has_permissions(manage_messages=True, manage_channels=True)
    @commands.command(name="Close", aliases=['C'], help="Closes the current channel", usage="Close")
    async def closeChannel_CMD(self, ctx, time="00:30:00"):
        """
        :param ctx: The context of how the command was called
        :param time: The time before the channel is closed
        """
        seconds = self.get_sec(time)
        try:
            user = get(ctx.guild.members, id=int(ctx.channel.name))
        except ValueError:
            return
        if not user:
            return
        await self.close_channel(ctx, user, time, seconds)

    @commands.command(name="Save", aliases=["S", 'Add', 'A'], help="Saves a custom command", usage="Save <name> <message>")
    async def saveCustomCommand_CMD(self, ctx, name, *, message):
        """
        :param ctx: The context of how the command was called
        :param name: The name the custom command will be called by
        :param message: The message that will be printed out when the command is called
        """
        customCommands = Command(bot=self.bot)
        for command in self.bot.commands:
            if name.lower() in [aliases.lower() for aliases in command.aliases]+[command.qualified_name.lower()]:
                return await ctx.send("That is already a registered command name or aliases!")
        added = customCommands.add_command(name.lower(), message)
        if added:
            await ctx.send("Command Added")
        else:
            await ctx.send(f"Failed to add command {name.lower()}")

    @commands.command(name="Remove", aliases=['R'], help="Removes a custom command", usage="Remove <command>")
    async def removeCustomCommand_CMD(self, ctx, name):
        """
        :param ctx: The context of how the command was called
        :param name: The name the custom command to delete
        """
        customCommands = Command(bot=self.bot)
        removed = customCommands.remove_command(name.lower())
        if removed:
            await ctx.send("Command Removed")
        else:
            await ctx.send(f"Failed to remove command {name.lower()}")

    @commands.command(name="CustomCommands", aliases=['D', 'CC', 'Custom', 'Display'], help="Displays all custom commands", usage="CustomCommands")
    async def displayCustomCommands_CMD(self, ctx):
        """
        Displays all custom commands registered
        :param ctx: The context of how the command was called
        """
        embed = discord.Embed(color=self.SuccessEmbedColor)
        comms = []
        customCommands = Command(bot=self.bot)

        for command in customCommands.commands:
            comms.append(f"Command Name: **{command}**\nResponse: {customCommands.commands[command]}")
        embed.add_field(name="Custom Commands", value="\n\n".join(comms) if comms else "No Commands")
        embed.set_footer(text=f"{self.bot.command_prefix}CustomCommands [name] for more info on a command")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
