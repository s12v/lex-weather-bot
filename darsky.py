import logging
import json
from urllib import request

from lex import LexContext

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class WeatherAtTime:

    def __init__(self, temp: float, summary: str):
        self.temp = temp
        self.summary = summary


class WeatherDay:

    def __init__(self, temp_min: float, temp_max: float, summary: str):
        self.temp_min = temp_min
        self.temp_max = temp_max
        self.summary = summary


class Weather:

    def __init__(self, now: WeatherAtTime, day: WeatherDay):
        self.now = now
        self.day = day


class DarkSky:

    URL = 'https://api.darksky.net/forecast/{}/{},{},{}?exclude=minutely,hourly,flags&units=auto'

    def __init__(self, key):
        self.api_key = key

    def load(self, context: LexContext) -> Weather:
        url = self.URL.format(self.api_key, context.lat(), context.lng(), context.timestamp())
        logger.debug('DARKSKY: url={}'.format(url))
        data = json.loads(request.urlopen(url).read().decode('utf-8'))
        currently = data['currently']
        day = data['daily']['data'][0]
        return Weather(
            now=WeatherAtTime(currently['temperature'], currently['summary']),
            day=WeatherDay(day['temperatureMin'], day['temperatureMax'], day['summary'])
        )
