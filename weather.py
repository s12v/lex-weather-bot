import logging
import json
from urllib import request

from lex import LexContext
from timezone import TimezoneApi

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class WeatherAtTime:

    def __init__(self, temp: float, summary: str, icon: str):
        self.temp = temp
        self.summary = summary
        self.icon = icon


class WeatherDay:

    def __init__(self, temp_min: float, temp_max: float, summary: str, icon: str):
        self.temp_min = temp_min
        self.temp_max = temp_max
        self.summary = summary
        self.icon = icon


class Weather:

    def __init__(self, now: WeatherAtTime, day: WeatherDay):
        self.now = now
        self.day = day


class WeatherSource:

    URL = 'https://api.darksky.net/forecast/{}/{},{}?exclude=minutely,hourly,flags&units=si'
    URL_TIME_MACHINE = 'https://api.darksky.net/forecast/{}/{},{},{}?exclude=minutely,hourly,flags&units=si'

    def __init__(self, key, timezone_api: TimezoneApi):
        self.api_key = key
        self.timezone_api = timezone_api

    def load(self, context: LexContext) -> Weather:
        if context.now:
            url = self.URL.format(self.api_key, context.lat, context.lng)
        else:
            try:
                timestamp = self.timezone_api.load(context.lat, context.lng, context.timestamp)
            except Exception:
                logger.exception('Unable to load time zone')
                timestamp = context.timestamp
            url = self.URL_TIME_MACHINE.format(self.api_key, context.lat, context.lng, timestamp)
        logger.debug('DARKSKY: url={}'.format(url))
        data = json.loads(request.urlopen(url).read().decode('utf-8'))
        currently = data['currently']
        day = data['daily']['data'][0]
        return Weather(
            now=WeatherAtTime(currently['temperature'], currently['summary'], currently['icon']),
            day=WeatherDay(day['temperatureMin'], day['temperatureMax'], day['summary'], day['icon'])
        )
