# Overwatch Queue Discord Bot
A Discord bot for managing a queue of game players.

## Description

A Discord bot created for a group of friends that play 
games together, but often have more players than the team 
limits allow.

Originally created for Overwatch 1, 
the bot allows a user to create a queue, which players can join.
When a game ends, the queue can be updated to see who sits out of the next game
and who joins the following game.
The queue cycles through players, so all players
get a chance to play games with minimal fuss.

## Installation

Create a .env file in your local version of this folder with the structure:
```
# .env
DISCORD_TOKEN=your-discord-token
```
The details for getting this token and setting up a Discord bot are 
[here](https://realpython.com/how-to-make-a-discord-bot-python/).
Once done, just install the necessary dependencies:
```
pip3 install -r requirements.txt
```

## Usage

Run the code folder with python (in the right virtual environment) to start the bot.
```
python3 bot_code
```
Type `!help` in your Discord server to see the available commands and check the bot is working:

```
  add            Add a player to the queue.
  delay          Temporarily no longer be counted as a current player
  end            End (empty) the current queue.
  help           Shows this message
  join           Join the Overwatch queue.
  kick           Remove a player from the queue.
  leave          Leave the Overwatch queue.
  link           Link a discord name to a battle net account
  next           Update the queue for the next game.
  queue          Starts an Overwatch queue.
  rejoin         Stop delaying games and be a current player again.
  status         See the status of the queue.
  undo           Undo the previous command issued.
  wait           See how long until your next game.
```

## Contributing
Contributions are welcome, but please get in touch with me first
to discuss.

## Licence
[MIT](https://choosealicense.com/licenses/mit/)