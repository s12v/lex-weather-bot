import json
import os
import logging

from bot import WeatherBot
from darsky import DarkSky
from geocoder import Geocoder
from webcam import WebcamSource

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

bot = WeatherBot(
    weather_source=DarkSky(os.environ['DARKSKY_KEY']),
    geocoder=Geocoder(os.environ['GOOGLE_KEY']),
    webcam_source=WebcamSource(os.environ['WEBCAM_KEY'])
)


def lambda_handler(event, context):
    logger.debug('EVENT={}'.format(json.dumps(event)))
    return bot.dispatch(event)
