import json
import os
import logging

from bot import WeatherBot
from darsky import DarkSky
from geocoder import Geocoder

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

bot = WeatherBot(DarkSky(os.environ['DARKSKY_KEY']), Geocoder(os.environ['GOOGLE_KEY']))


def lambda_handler(event, context):
    logger.debug('EVENT={}'.format(json.dumps(event)))
    return bot.dispatch(event)
