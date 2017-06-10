import logging
import json
import urllib

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class Geocoder:

    URL = 'https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}'

    def __init__(self, api_key):
        self.api_key = api_key

    def geocode(self, address: str):
        url = self.URL.format(urllib.parse.quote(address, 'utf-8'), self.api_key)
        logger.debug('GEOCODE: {}'.format(url))
        return json.loads(urllib.request.urlopen(url).read().decode('utf-8'))
