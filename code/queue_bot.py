"""
Class for QueueBot, which is a Discord bot to manage interaction with GameQueue objects from game_queue.py.
"""

# Standard library imports.
import json
from pathlib import Path
from typing import Any

# Third party imports.
import discord
from discord.ext import commands

# Local imports.
from game_queue import Player, GameQueue

# Add the message_content intent to use commands
INTENTS = discord.Intents.default()
INTENTS.message_content = True

class QueueBot(commands.Bot):
    """
    Class for a Queue Discord Bot.
    
    Inherits from a Discord bot with commands for starting and interacting with queues.

    Non-inherited public attributes:
        queues (dict): The dictionary of queue names and corresponding GameQueue objects.
        NO_QUEUE_RESPONSE (str): The default response for there not being a queue.
        NO_PLAYERCUTOFF_PARAM_RESPONSE (str): The default response for there not being a player_number parameter in a command.
        NO_GAME_PARAM_RESPONSE (str): The default response for there not being a game parameter in a command.
    """

    def __init__(self, 
                 command_prefix: str='!'):
        """
        Initialises the Queue_Bot.

        Args:
            command_prefix (str, default='!'): The character which identifies a message as a command.
        """
        super().__init__(command_prefix=command_prefix,
                         intents=INTENTS,
                         help_command=commands.DefaultHelpCommand(no_category='Commands'))
        self.queues = dict()
        self.NO_GAME_PARAM_RESPONSE = "Game to interact with cannot be identified. Please enter it after the command."
        self.NO_PLAYERCUTOFF_PARAM_RESPONSE = "No player count data exists for that game. Please enter it after the game name in the command."
        self.NO_QUEUE_RESPONSE = "There is no queue. Type \'!queue [game_name] [player_number]\' to create one."
        self.__game_dict_fpath = Path("db") / "game_dict.json"
        # Create a db directory if one doesn't exist already
        self.__game_dict_fpath.parent.mkdir(exist_ok=True)
        # Create a game dictionary if one isn't present already
        if not self.__game_dict_fpath.exists():
            with open(self.__game_dict_fpath, 'w') as f:
                json.dump({}, f)
        with open(self.__game_dict_fpath) as f:
            self.game_dict = json.load(f)


    """
    Private class methods to support commands.
    """

    def __update_player_cutoff(self, game_name: str, player_cutoff: int) -> None:
        """
        Updates the player_cutoff for a game in the game_dict.

        Args:
            game_name (str): The name of the game in the game_dict to update.
            player_cutoff (int): The new player_cutoff to update with.
        """
        self.game_dict[game_name] = player_cutoff
        with open(self.__game_dict_fpath, 'w') as f:
            json.dump(self.game_dict, f)
        return

    
    def __check_and_lower_game_name_param(self, game_name, player_name: str='') -> str:
        """
        Infers the game_name parameter if not given and then returns it lowered.

        Args:
            game_name (str): The name of the game to lower.
            player_name (str, default=''): The name of the player to infer a game_name from.

        Returns:
            str: The lowered name of the game, if inferrable.
        """
        if game_name:
            return game_name.lower()
        if len(self.queues) == 1:
            return list(self.queues.keys())[0].lower()
        player_queues = [name for name in self.queues.keys() if self.queues[name].find_player(player_name)]
        if len(player_queues) == 1:
            return player_queues[0]
        else:
            return ""

    
    def __check_player_cutoff_param(self, game_name: str, player_cutoff: int) -> int:
        """
        Get the player_cutoff parameter for game_name, or update this if given.

        Args:
            game_name (str): The name of the game to check the player_cutoff parameter for.
            player_cutoff (int): The new player_cutoff to update the game with.
        
        Returns:
            int: The player_cutoff for the given game_name.
        """
        if game_name in self.game_dict:
            db_player_cutoff = self.game_dict[game_name]
            if not player_cutoff:
                player_cutoff = db_player_cutoff
            if player_cutoff != db_player_cutoff:
                self.__update_player_cutoff(game_name, player_cutoff)
        else:
            self.__update_player_cutoff(game_name, player_cutoff)
        return player_cutoff
    

    def __check_if_queue_exists_and_nonempty(self, game_name: str) -> False:
        """
        Check whether a queue with game_name exists and has players.

        Args:
            game_name (str): The name of the game to check whether it exists and has players for.
        
        Returns:
            bool: True if queue exists with players, else False.
        """
        if not game_name in self.queues.keys():
            return False
        elif not self.queues[game_name].players:
            return False
        else:
            return True


    """
    Commands for the bot. Add using the add_commands() function in this file.
    """
    async def start_queue(self, ctx: commands.Context, game_name: str="", player_cutoff: int=0) -> str:
        """
        Command for the player to start or join  a queue for the given game_name.

        Args:
            ctx (commands.Context): The context of the command.
            game_name (str, default=""): The name of the game to queue for.
            player_cutoff (int, default=0): The player count for the given game_name.

        Returns:
            str: The response message to post in the Discord channel the command was sent in.
        """
        lower_game_name = self.__check_and_lower_game_name_param(game_name=game_name)
        # If no game_name and can't be inferred, then return this needs to be a parameter
        if not lower_game_name:
            response = self.NO_GAME_PARAM_RESPONSE
        # Add player to queue if game already has a queue
        elif self.__check_if_queue_exists_and_nonempty(lower_game_name):
            response = self.queues[lower_game_name].add_player(Player(ctx.message.author.name))
        # Create a new queue if game does not have a queue
        else:
            player_cutoff = self.__check_player_cutoff_param(lower_game_name, player_cutoff)
            # If player_cutoff can't be inferred, return this needs to be a parameter
            if not player_cutoff:
                response = self.NO_PLAYERCUTOFF_PARAM_RESPONSE
            # Create a new queue for the game, and @mention game if possible.
            else:
                self.queues[lower_game_name] = GameQueue(lower_game_name, player_cutoff)
                roles = ctx.guild.roles
                mentioned_game_name = lower_game_name
                for role in roles:
                    if lower_game_name in role.name.lower() and role.mentionable:
                        mentioned_game_name = role.mention
                        break
                response = f"Queue has been created for {mentioned_game_name}.\n"
                response += self.queues[lower_game_name].add_player(Player(ctx.message.author.name))
        await ctx.send(response)


    async def leave_queue(self, ctx: commands.Context, game_name: str="") -> str:
        """
        Command for the player to leave the queue for the given game_name.

        Args:
            ctx (commands.Context): The context of the command.
            game_name (str, default=""): The name of the game to queue for.

        Returns:
            str: The response message to post in the Discord channel the command was sent in.
        """
        player_name = ctx.message.author.name
        lower_game_name = self.__check_and_lower_game_name_param(game_name, player_name=player_name)
        # If no game_name and can't be inferred, then return this needs to be a parameter
        if not lower_game_name:
            response = self.NO_GAME_PARAM_RESPONSE
        # If player in the game_name, them remove from queue
        elif self.queues[lower_game_name].find_player(player_name):
            player = self.queues[lower_game_name].find_player(player_name)
            response = self.queues[lower_game_name].delete_player(player)
        else:
            response = f"{player_name} is not a member of the queue for {lower_game_name}. Please check and try again."
        await ctx.send(response)


    async def next_game_for_queue(self, ctx: commands.Context, game_name: str="") -> str:
        """
        Command to rotate the queue for game_name to view the players for the next game.

        Args:
            ctx (commands.Context): The context of the command.
            game_name (str, default=""): The name of the game to rotate the queue for.

        Returns:
            str: The response message to post in the Discord channel the command was sent in.
        """
        player_name = ctx.message.author.name
        lower_game_name = self.__check_and_lower_game_name_param(game_name, player_name=player_name)
        # If no game_name and can't be inferred, then return this needs to be a parameter
        if not lower_game_name:
            response = self.NO_GAME_PARAM_RESPONSE
        elif not self.__check_if_queue_exists_and_nonempty(lower_game_name):
            response = self.NO_QUEUE_RESPONSE
        # Else rotate the queue once and print the new ordering of the queue
        else:
            response = self.queues[lower_game_name].update_queue()
        await ctx.send(response)


    async def status_queue(self, ctx: commands.Context, game_name: str="") -> str:
        """
        Command to print the status of the queue, i.e. the current ordering of players.

        Args:
            ctx (commands.Context): The context of the command.
            game_name (str, default=""): The name of the game to print the status of the queue for.

        Returns:
            str: The response message to post in the Discord channel the command was sent in.
        """
        player_name = ctx.message.author.name
        lower_game_name = self.__check_and_lower_game_name_param(game_name, player_name=player_name)
        # If no game_name and can't be inferred, then return this needs to be a parameter
        if not lower_game_name:
            response = self.NO_GAME_PARAM_RESPONSE
        elif not self.__check_if_queue_exists_and_nonempty(lower_game_name):
            response = self.NO_QUEUE_RESPONSE
        else:
            response = self.queues[lower_game_name].print_players()
        await ctx.send(response)


    async def wait_queue(self, ctx: commands.Context, game_name: str='') -> str:
        """
        Command to print the wait time of the messager.

        Args:
            ctx (commands.Context): The context of the command.
            game_name (str, default=""): The name of the game to print the wait for.

        Returns:
            str: The response message to post in the Discord channel the command was sent in.
        """
        player_name = ctx.message.author.name
        lower_game_name = self.__check_and_lower_game_name_param(game_name, player_name=player_name)
        if not lower_game_name:
            response = self.NO_GAME_PARAM_RESPONSE
        elif not self.__check_if_queue_exists_and_nonempty(lower_game_name):
            response = self.NO_QUEUE_RESPONSE
        else:
            player = self.queues[lower_game_name].find_player(player_name)
            response = self.queues[lower_game_name].print_player_wait(player)
        await ctx.send(response)

    
    async def add_player(self, ctx: commands.Context, player_to_add: str='', game_name: str=''):
        """
        Command to add a player to the queue.
        
        Args:
            ctx (commands.Context): The context of the command.
            player_to_add (str, default=""): The name of the player to add to the queue.
            game_name (str, default=""): The name of the game to add the player to.

        Returns:
            str: The response message to post in the Discord channel the command was sent in.
        """
        if not player_to_add:
            await ctx.send(f'Please enter {self.command_prefix}add [PLAYERNAME] [GAMENAME].')
        lower_game_name = self.__check_and_lower_game_name_param(game_name, player_name=ctx.message.author.name)
        if not lower_game_name:
            response = self.NO_GAME_PARAM_RESPONSE
        elif not self.__check_if_queue_exists_and_nonempty(lower_game_name):
            response = self.NO_QUEUE_RESPONSE
        elif self.queues[lower_game_name].find_player(player_to_add):
            response = f'{player_to_add} is already a member of the queue for {lower_game_name}.'
        else:
            response = self.queues[lower_game_name].add_player(Player(player_to_add))
        await ctx.send(response)


    async def kick_player(self, ctx: commands.Context, player_to_remove: str='', game_name: str=''):
        """
        Command to remove a player to the queue.
        
        Args:
            ctx (commands.Context): The context of the command.
            player_to_kick (str, default=""): The name of the player to remove from the queue.
            game_name (str, default=""): The name of the game to add the player to.

        Returns:
            str: The response message to post in the Discord channel the command was sent in.
        """
        if not player_to_remove:
            await ctx.send(f'Please enter {self.command_prefix}kick [PLAYERNAME] [GAMENAME].')
        lower_game_name = self.__check_and_lower_game_name_param(game_name, player_name=ctx.message.author.name)
        if not lower_game_name:
            response = self.NO_GAME_PARAM_RESPONSE
        elif not self.__check_if_queue_exists_and_nonempty(lower_game_name):
            response = self.NO_QUEUE_RESPONSE
        else:
            player = self.queues[lower_game_name].find_player(player_to_remove)
            if player:
                response = self.queues[lower_game_name].delete_player(player)
            else:
                response = f'{player_to_remove} is not a member of the queue for {lower_game_name}.'
        await ctx.send(response)

    
    async def delay_player(self, ctx: commands.Context, game_name: str='', player_to_delay: str=''):
        """
        Command to delay joining the current players queue.
        
        Args:
            ctx (commands.Context): The context of the command.
            game_name (str, default=""): The name of the game to add the player to.

        Returns:
            str: The response message to post in the Discord channel the command was sent in.
        """
        player_to_delay = ctx.message.author.name if not player_to_delay else player_to_delay
        lower_game_name = self.__check_and_lower_game_name_param(game_name, player_name=player_to_delay)
        if not lower_game_name:
            response = self.NO_GAME_PARAM_RESPONSE
        elif not self.__check_if_queue_exists_and_nonempty(lower_game_name):
            response = self.NO_QUEUE_RESPONSE
        else:
            player = self.queues[lower_game_name].find_player(player_to_delay)
            if player:
                message = self.queues[lower_game_name].delay_player(player)
                response = f"{player_to_delay} is now delaying their games. Type \'{self.command_prefix}rejoin\' to stop."
                response += ("\n\n" + message)
            else:
                response = f"{player_to_delay} is not a player in the queue for {lower_game_name}."
        await ctx.send(response)

    
    async def rejoin_player(self, ctx: commands.Context, game_name: str=''):
        """
        Command to rejoin the current players queue after delaying.
        
        Args:
            ctx (commands.Context): The context of the command.
            game_name (str, default=""): The name of the game to add the player to.

        Returns:
            str: The response message to post in the Discord channel the command was sent in.
        """
        lower_game_name = self.__check_and_lower_game_name_param(game_name, player_name=ctx.message.author.name)
        game_name = game_name.lower()
        if not lower_game_name:
            response = self.NO_GAME_PARAM_RESPONSE
        elif not self.__check_if_queue_exists_and_nonempty(lower_game_name):
            response = self.NO_QUEUE_RESPONSE
        else:
            player = self.queues[lower_game_name].find_player(ctx.message.author.name)
            if player and player.delaying:
                message = self.queues[lower_game_name].rejoin_player(player)
                response = f"{ctx.message.author.name} is no longer delaying their games."
                response += ("\n\n" + message)
            elif player and not player.delaying:
                response = f"{ctx.message.author.name} was not delaying games."
            else:
                response = f"{ctx.message.author.name} is not a player in the queue for {lower_game_name}."
        await ctx.send(response)


    async def undo_queue(self, ctx: commands.Context, game_name: str=''):
        """
        Command to undo the previous command.

        Args:
            ctx (commands.Context): The context of the command.
            game_name (str, default=""): The name of the game to undo the queue state for.

        Returns:
            str: The response message to post in the Discord channel the command was sent in.
        """
        lower_game_name = self.__check_and_lower_game_name_param(game_name, player_name=ctx.message.author.name)
        if not lower_game_name:
            response = self.NO_GAME_PARAM_RESPONSE
        elif not self.__check_if_queue_exists_and_nonempty(lower_game_name):
            response = self.NO_QUEUE_RESPONSE
        else:
            message = self.queues[lower_game_name].undo_command()
            response = "Previous command has been undone. The status of the queue now is:\n\n"
            response = response + message
        await ctx.send(response)


    async def switch_queue(self, ctx: commands.Context, game_name: str='', player_cutoff: int=0):
        """
        Command to switch the queue to a different game.

        Args:
            ctx (commands.Context): The context of the command.
            game_name (str, default=""): The name of the game to switch the queue to.
            player_cutoff (int, default=0): The player count for the given game_name.

        Returns:
            str: The response message to post in the Discord channel the command was sent in.
        """
        current_game_name = self.__check_and_lower_game_name_param('', player_name=ctx.message.author.name)
        lower_game_name = game_name.lower()
        if not lower_game_name:
            response = self.NO_GAME_PARAM_RESPONSE
        elif not current_game_name:
            response = "You do not appear to currently be in a queue. Please join one before switching games."
        else:
            player_cutoff = self.__check_player_cutoff_param(lower_game_name, player_cutoff)
            # If player_cutoff can't be inferred, return this needs to be a parameter
            if not player_cutoff:
                response = self.NO_PLAYERCUTOFF_PARAM_RESPONSE
            # Create a new queue for the game, and @mention game if possible.
            else:
                players_to_move = self.queues[current_game_name].players.copy()
                self.queues[current_game_name].empty_queue()
                self.queues[lower_game_name] = GameQueue(lower_game_name, player_cutoff, players=players_to_move)
                mentioned_game_name = lower_game_name
                roles = ctx.guild.roles
                for role in roles:
                    if lower_game_name in role.name.lower() and role.mentionable:
                        mentioned_game_name = role.mention
                response = f"Queue has been created for {mentioned_game_name}.\n"
        await ctx.send(response)
        

    async def end_queue(self, ctx: commands.Context, game_name: str=''):
        """
        Command to end the queue.

        Args:
            ctx (commands.Context): The context of the command.
            game_name (str, default=""): The name of the game to add the player to.

        Returns:
            str: The response message to post in the Discord channel the command was sent in.
        """
        lower_game_name = self.__check_and_lower_game_name_param(game_name, player_name=ctx.message.author.name)
        if not lower_game_name:
            response = self.NO_GAME_PARAM_RESPONSE
        else:
            self.queues[lower_game_name].empty_queue()
            response = "The queue has been ended. Type \'!queue [game_name]\' to start a new queue."
        await ctx.send(response)


    async def sync_command_tree(self, ctx: commands.Context):
        '''
        Command to sync the command tree for the bot, to set commands as slash commands.

        Args:
            ctx (commands.Context): The context of the command.
        '''
        if await self.is_owner(ctx.author):
            await self.tree.sync()
            await ctx.send('Command tree synced 👌.')
        else:
            await ctx.send('Only the owner of the bot can use this command 😞.')

    
    """
    Behaviour for events happening to the bot.
    """
    async def on_command_error(self, ctx: commands.Context, error: Any) -> str:
        """
        Error handling for errors with a command.

        Args:
            ctx (commands.Context): The context of the command.
            error (Any): A commands error.

        Returns:
            str: The response message to post in the Discord channel the error was received in.
        """
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("**Invalid command. Try using** `help` **to figure out commands!**")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('**Please pass in all requirements to use the command. Try using** `help`**!**')
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("**You dont have all the requirements or permissions for using this command :angry:**")
        elif isinstance(error, commands.errors.CommandInvokeError):
            await ctx.send("**There was a connection error somewhere, why don't you try again now?**")
        else:
            print(error)


    async def on_ready(self) -> None:
        """
        Message to print in the terminal when the bot is created to confirm its ready.
        """
        print(f"Bot created as: {self.user.name}")
    

    def add_events(self) -> None:
        '''
        Add the new events to the bot.
        '''
        self.on_command_error = self.event(self.on_command_error)
        self.on_ready = self.event(self.on_ready)



def add_commands_to_bot(bot: QueueBot):
    '''
    Add commands to a QueueBot.

    Functions have to be tied to class instance, not class, due to decorators attached to object.

    Args:
        bot (QueueBot): An instance of the QueueBot class.
    '''
    @bot.hybrid_command(name='queue', 
                        aliases=['join'],
                        brief='Join a Game Queue for the given game_name, start queue if none exists.')
    async def start_queue(ctx, game_name: str='', player_cutoff: int=0):
        await bot.start_queue(ctx, game_name=game_name, player_cutoff=player_cutoff)

    @bot.hybrid_command(name='leave',
                        aliases=['quit'],
                        brief='Leave the queue for the given game_name.')
    async def leave_queue(ctx, game_name: str=''):
        await bot.leave_queue(ctx, game_name=game_name)
    
    @bot.hybrid_command(name='next',
                        aliases=['rotate', 'update'],
                        brief='Rotate the queue to get the players for the next game.')
    async def next_game_for_queue(ctx, game_name: str=""):
        await bot.next_game_for_queue(ctx, game_name=game_name)

    @bot.hybrid_command(name='status', 
                        brief='See the status of the queue for the given game_name.')
    async def status_queue(ctx, game_name: str=""):
        await bot.status_queue(ctx, game_name=game_name)

    @bot.hybrid_command(name='wait', 
                        aliases=['time'],
                        brief='See how long until your next game.')
    async def wait_queue(ctx, game_name: str=''):
        await bot.wait_queue(ctx, game_name=game_name)

    @bot.hybrid_command(name='add', 
                        brief='Add a player to the queue.')
    async def add_player(ctx, player_to_add: str='', game_name: str=''):
        await bot.add_player(ctx, player_to_add=player_to_add, game_name=game_name)

    @bot.hybrid_command(name='kick', 
                        aliases=['remove'],
                        brief='Remove a player from the queue.')
    async def kick_player(ctx, player_to_remove: str='', game_name: str=''):
        await bot.kick_player(ctx, player_to_remove=player_to_remove, game_name=game_name)

    @bot.hybrid_command(name='delay', 
                        brief='Temporarily no longer join current players until rejoined.')
    async def delay_player(ctx, player_to_delay: str='', game_name: str=''):
        await bot.delay_player(ctx, game_name=game_name, player_to_delay=player_to_delay)

    @bot.hybrid_command(name='rejoin', 
                        brief='Stop delaying games and be able to join current players again.')
    async def rejoin_player(ctx, game_name: str=''):
        await bot.rejoin_player(ctx, game_name=game_name)

    @bot.hybrid_command(name='undo', 
                        brief='Reset the queue to the previous state.')
    async def undo_queue(ctx, game_name: str=''):
        await bot.undo_queue(ctx, game_name=game_name)

    @bot.hybrid_command(name='game',
                        aliases=['switch'],
                        brief='Switch the queue to a different game.')
    async def switch_queue(ctx, game_name: str='', player_cutoff: int=0):
        await bot.switch_queue(ctx, game_name=game_name, player_cutoff=player_cutoff)

    @bot.hybrid_command(name='end',
                        aliases=['stop'], 
                        brief='End a current queue.')
    async def end_queue(ctx, game_name: str=''):
        await bot.end_queue(ctx, game_name=game_name)

    @bot.command(name='sync_commands_queuebot',
                 hidden=True)
    async def sync_command_tree(ctx):
        await bot.sync_command_tree(ctx)
    
    print('Commands added to bot.')