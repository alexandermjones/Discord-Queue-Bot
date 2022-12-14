"""
Run the Discord bot by running the directory.
"""
# Standard imports
from os import getenv

# Third party imports
from dotenv import load_dotenv

# Local imports
from queue_bot import QueueBot

# Load in Discord token.
load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')
try:
    assert TOKEN is not None
except AssertionError:
    raise EnvironmentError('No token found for the Discord bot in the .env file. Please see the readme for details.')

# Create bot and run.
bot = QueueBot(command_prefix='!')
bot.run(TOKEN)