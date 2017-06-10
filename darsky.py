import logging
import json
import urllib

from lex import LexContext

logger = logging.getLogger(__name__)
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
        logger.debug('url={}'.format(url))
        data = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))
        return Weather(
            now=WeatherAtTime(data['now']['temperature'], data['now']['summary']),
            day=WeatherDay(data['day']['temperatureMin'], data['day']['temperatureMax'], data['day']['summary'])
        )
