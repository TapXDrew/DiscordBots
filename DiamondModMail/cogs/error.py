import sys
import traceback

import discord
from discord.ext import commands


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        Handles errors raised while executing a command
        :param ctx: Information on the context of where the command was called
        :param error: The Exception that was called
        """

        if hasattr(ctx.command, 'on_error'):
            return
        
        ignored = (commands.CommandNotFound, discord.ext.commands.errors.CheckFailure)
        error = getattr(error, 'original', error)
        
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(f'{ctx.command} has been disabled.')  # disabled=True was set in the command kwargs, so we can not use the command

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')  # The command was decorated with @commands.guild_only
            except Exception:
                pass  # We try to send a message, if we fail, continue and print the error

        elif isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.UserInputError):
            return await ctx.send(f"Invalid Command Usage! `{self.bot.command_prefix}{ctx.command.qualified_name} {' '.join(ctx.command.clean_params.keys())}`\nUse `{self.bot.command_prefix}Help {ctx.command.qualified_name}`")
            # This happens whenever a user does not input the correct args, doesnt enter enough args, or enter no args, sends information on using the command

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
