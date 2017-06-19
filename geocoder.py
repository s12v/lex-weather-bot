import logging
import json
from urllib import request, parse
from lex import LexContext

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class Geocoder:

    URL = 'https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}'

    def __init__(self, api_key):
        self.api_key = api_key

    def geocode(self, context: LexContext):
        url = self.URL.format(parse.quote(context.address, 'utf-8'), self.api_key)
        logger.debug('GEOCODE: {}'.format(url))
        return json.loads(request.urlopen(url).read().decode('utf-8'))
