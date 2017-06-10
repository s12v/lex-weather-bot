import logging
import json
import urllib

from lex import LexContext

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DarkSky:

    URL = 'https://api.darksky.net/forecast/{}/{},{},{}?exclude=minutely,hourly,flags&units=auto'

    def __init__(self, key):
        self.api_key = key

    def load(self, context: LexContext) -> dict:
        try:
            url = self.URL.format(self.api_key, context.lat(), context.lng(), context.timestamp())
            logger.debug('url={}'.format(url))
            data = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))
            return {
                "now": data['currently'],
                "day": data['daily']['data'][0]
            }
        except Exception:
            logger.error("Unable to load weather")

        return {}
