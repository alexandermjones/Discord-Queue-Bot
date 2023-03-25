"""
Run the Discord bot by running the directory.
"""
# Standard imports
from os import getenv

# Third party imports
from dotenv import load_dotenv

# Local imports
from queue_bot import QueueBot, add_commands_to_bot


if __name__ == '__main__':
    # Load in Discord token.
    load_dotenv()
    token = getenv('DISCORD_TOKEN')

    try:
        assert token is not None
    except AssertionError:
        raise EnvironmentError('No token found for the Discord bot in the .env file. Please see the readme for details.')

    # Create bot and run.
    bot = QueueBot(command_prefix='!')
    add_commands_to_bot(bot)
    bot.run(token)