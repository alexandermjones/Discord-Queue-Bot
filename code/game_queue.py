"""
Class for a Player and class for a Game_Queue of Players.
"""

# Standard library imports
from datetime import datetime as dt
from collections import deque
from copy import deepcopy
from math import floor


class Player():
    """
    A player.

    Attributes:
        name (str): The name of the Player.
        playing (bool): Whether the Player is currently playing a game.
        delaying (bool): Whether the Player is currently delaying games.
    """

    def __init__(self, name: str):
        """
        Initialise a player.

        Args:
            name (str): The name of the Player.
        """
        self.name = name
        self.playing = False
        self.delaying = False



class GameQueue():
    """
    A queue of players (Player objects).

    Attributes:
        players (list): The list of all players (Player objects).
        num_players (int): The number of players for the game.
        game_name (str): The name of the game the Game_Queue is for.
        start_time (datetime.datetime): The creation time of the Game_Queue.
        current_players (collections.deque): A deque of players (Player objects) currently playing
        waiting_players (collections.deque): A deque of players (Player objects) waiting to play
    """

    def __init__(self, game_name: str, player_cutoff: int, players: list=[]):
        """
        Initialise a Game_Queue with the number of players for a game and list of Players.

        The first player_cutoff Players are added into the current_players deque and any other players are
        added to the waiting_players deque.

        Args:
            game_name (str): The name of the game the Game_Queue is for.
            player_cutoff (int): The maximum number of players for the game.
            players (list, default=[]): The list of players (Player objects) to start the Game_Queue.
        """
        self.players = players
        self.delayed_players = []
        self.start_time = dt.now()
        self.player_cutoff = player_cutoff
        self.game_name = game_name
        # Create a deque of the first player_cutoff players.
        self.current_players = deque(players[:self.player_cutoff])
        # Create a deque of all other players.
        if len(players) > self.player_cutoff:
            self.waiting_players = deque(players[self.player_cutoff:])
        else:
            self.waiting_players = deque()
        # Set whether the Player objects are playing or not.
        for player in self.current_players:
            player.playing = True
        for player in self.waiting_players:
            player.playing = False

        # Setup backup lists for undo-ing actions
        self.__backup_players = self.players
        self.__backup_delayed_players = self.delayed_players
        self.__backup_current_players = self.current_players
        self.__backup_waiting_players = self.waiting_players
    

    def add_player(self, player: Player) -> str:
        """
        Adds a player to the queue.

        If there are fewer than self.player_cutoff players, they are added to the current_players deque,
        else they are added to the waiting_players deque.
        If they are the 2*self.player_cutoff player, then it is recommended that two games are played.

        Args:
            player (Player): A Player object to add to the queue.

        Returns:
            message (str): A message saying whether the player has been added.
        """
        self.__backup_queue()
        # Check that player is not already a player.
        if player in self.players:
            message = (f"{player.name} is already a player in the queue.")
            return message
        # Add player to queue and current or waiting players.
        self.players.append(player)
        if len(self.current_players) < self.player_cutoff:
            self.current_players.append(player)
            player.playing = True
        else:
            self.waiting_players.append(player)
            player.playing = False

        message = f"{player.name} has been added to the queue."
        
        # If 2*self.player_cutoff players, recommend you have two games.
        if len(self.players) == self.player_cutoff*2:
            message += (f"\nOh neat! {player.name} is the {self.player_cutoff*2}th player - is it time for two games?")
        return message


    def delete_player(self, player: Player) -> str:
        """
        Removes a player from the queue.

        The player is removed from the list of players.
        If they are in the current_players deque, then they are removed from here and the next
        waiting player is added to current_players.
        If the player is in the waiting_players deque, they are removed from here.

        Args:
            player (Player): A Player object to add to the queue.
        
        Returns:
            str: A message confirming the player has been deleted.
        """
        self.__backup_queue()
        self.players.remove(player)
        if player in self.current_players:
            self.current_players.remove(player)
            # If we have a player waiting who is not delaying, then add them to the current_players list.
            if len(list(filter(lambda x: not x.delaying, self.waiting_players))):
                self.__rotate_queue_once()
        elif player in self.waiting_players:
            self.waiting_players.remove(player)
        else:
            return f"{player} is not a member of the queue."
        message = f"{player} has been removed from the queue.\n"
        message += self.print_players()
        return message

    
    def delay_player(self, player: Player):
        """
        Moves a player from the current or waiting players to delayed_players.

        The player is removed from the current_players or waiting_players deque.
        The player is then added to the delayed_players list.
        Finally, if a player is in the waiting_players deque, then they are added to current_players.

        Args:
            player (Player): A Player object in self.players
        """
        self.__backup_queue()
        player.playing = False
        player.delaying = True
        self.delayed_players.append(player)
        if player in self.current_players:
            self.current_players.remove(player)
            # If we have a player waiting who is not delaying, then add them to the current_players list.
            if len(list(filter(lambda x: not x.delaying, self.waiting_players))):
                self.__rotate_queue_once()
            self.waiting_players.appendleft(player)
        message = self.print_players()
        return message

    
    def rejoin_player(self, player: Player):
        """
        Sets the player to no longer be delaying and adds them to current_players if space.

        Args:
            player (Player): A Player object in self.players
        """
        self.__backup_queue()
        player.delaying = False
        self.delayed_players.remove(player)
        if len(self.current_players) <= self.player_cutoff - 1:
            self.current_players.append(player)
            self.waiting_players.remove(player)
            player.playing = True
        message = self.print_players()
        return message
    

    def print_players(self) -> str:
        """
        Returns a message showing the currently playing players and the waiting players.

        Returns:
            message (str): The message of current and waiting players' status.
        """
        # Print players in the next/current game.
        message = "The players in the next game are: "
        for player in self.current_players:
            message += ("\n\t" + player.name)
        # Print players waiting for a game.
        if self.waiting_players:
            message += "\n\nThe players in the waiting queue are: "
            for player in self.waiting_players:
                message += ("\n\t" + player.name)
                if player.delaying:
                    message += " (Currently delaying)"
        return message


    def update_queue(self) -> str:
        """
        Changes the current players in the queue for the next game.

        If there are fewer than self.player_cutoff players, nothing changes.
        If there are self.player_cutoff + 1 players, then the oldest player is moved to waiting_players and the
        longest waiting player is moved to current_players.
        If there are betweem self.player_cutoff + 2 and self.player_cutoff * 2 - 2 players, then the two oldest players
        are moved to waiting_players and the two longest waiting players are moved to current_players.
        Otherwise if there are self.player_cutoff * 2 - 1 or more players, then the three oldest players are moved to
        waiting_players and the two longest waiting players are moved to current_players.

        Returns:
            message (str): The message from self.print_players()
        """
        self.__backup_queue()
        if (len(self.players) - len(self.delayed_players)) <= self.player_cutoff:
            # No players to swap out
            pass
        elif (len(self.players) - len(self.delayed_players)) == self.player_cutoff + 1:
            # Only a single player to swap
            self.__rotate_queue_once()
        elif (len(self.players) - len(self.delayed_players)) <= self.player_cutoff * 2 - 2:
            # Two players to swap
            self.__rotate_queue_once()
            self.__rotate_queue_once()
        else:
            # Three players to swap
            self.__rotate_queue_once()
            self.__rotate_queue_once()
            self.__rotate_queue_once()

        # Get a message of who the current/waiting players now.
        message = self.print_players()
        return message

    
    def print_player_wait(self, player: Player) -> str:
        """
        Returns a message of the queue status of the Player and how many games they have left/to wait.

        Args:
            player (Player): A Player object to return its status.

        Returns:
            message (str): The message telling the player how long they have to go.
        """
        # If player in a game, return how many games they have left to play.
        if player in self.current_players:
            games_left = int(floor(self.current_players.index(player)/2))
            message = f"{player.name} is currently playing/queuing for a game. They have {games_left} games left after this one."
        # If player waiting for a game, return how many games they have to wait for.
        elif player in self.waiting_players:
            games_left = int(floor(self.waiting_players.index(player)/2))
            message = f"{player.name} has to wait for {games_left} games after this one."
        else:
            message = f"{player.name} is not currently in the queue."
        return message


    def find_player(self, player_name: str):
        """
        Returns a Player object from the queue, given a player name as a string.

        Args:
            player_name (str): The name of a player in the Overwatch_Queue.

        Returns:
            player (Player): A Player object with the same name as player_name in the queue, empty string if none.
        """
        for player in self.players:
            if player.name == player_name:
                return player
        return ""

  
    def empty_queue(self):
        """
        Empties the queue of all players.
        """
        self.__backup_queue()
        for player in self.players:
            del(player)
        self.players = []
        self.current_players = deque()
        self.waiting_players = deque()


    def undo_command(self):
        """
        Undoes the previous command.
        Replaces all current class properties x with the __backup_x property instead.

        Returns:
            message (str): The message from self.print_players()
        """
        # Undo previous operation
        self.players = self.__backup_players
        self.delayed_players = self.__backup_delayed_players
        self.current_players = self.__backup_current_players
        self.waiting_players = self.__backup_waiting_players

        # Return current state of queue
        message = self.print_players()
        return message

    
    def __rotate_queue_once(self):
        """
        Private function. Rotates one current player into the waiting queue.
        Called in update_queue.
        """
        players_delaying = []

        # Remove any delayed players into holding position
        for player in self.delayed_players:
            if player == self.waiting_players[0]:
                players_delaying.append(self.waiting_players.popleft())

        # Swap out player
        new_player = self.waiting_players.popleft()
        self.current_players.append(new_player)
        new_player.playing = True              

        if len(self.current_players) > self.player_cutoff:
            old_player = self.current_players.popleft()
            self.waiting_players.append(old_player)
            old_player.playing = False

        # Replace any players holding position
        for player in players_delaying:
            self.waiting_players.appendleft(player)

    
    def __backup_queue(self):
        """
        Private function. Backs up the current state of the queue in backup properties.
        Called when performing an action, to allow undo-ing the most recent command.
        """
        self.__backup_players = deepcopy(self.players)
        self.__backup_delayed_players = deepcopy(self.delayed_players)
        self.__backup_current_players = deepcopy(self.current_players)
        self.__backup_waiting_players = deepcopy(self.waiting_players)