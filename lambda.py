import json
import os
import logging

from bot import WeatherBot
from weather import WeatherSource
from geocoder import Geocoder
from webcam import WebcamSource
from timezone import TimezoneApi

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

timezone_api = TimezoneApi(os.environ['GOOGLE_TIMEZONE_KEY'])
weather_source = WeatherSource(os.environ['DARKSKY_KEY'], timezone_api)
geocoder = Geocoder(os.environ['GOOGLE_KEY'])
webcam_source = WebcamSource(os.environ['WEBCAM_KEY'])

bot = WeatherBot(weather_source, geocoder, webcam_source)


def lambda_handler(event, context):
    logger.debug('EVENT={}'.format(json.dumps(event)))
    return bot.dispatch(event)
