import logging
import json
from urllib import request

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class TimezoneApi:

    URL = 'https://maps.googleapis.com/maps/api/timezone/json?location={},{}&timestamp={}&key={}'

    def __init__(self, key):
        self.api_key = key

    def load(self, lat: float, lng: float, timestamp: int) -> int:
        url = self.URL.format(lat, lng, timestamp, self.api_key)
        logger.debug('TIMEZONE: url={}'.format(url))
        data = json.loads(request.urlopen(url).read().decode('utf-8'))
        new_timestamp = timestamp - data['dstOffset'] - data['rawOffset']
        logger.debug('TIMEZONE: url={}'.format(url))
        return new_timestamp
