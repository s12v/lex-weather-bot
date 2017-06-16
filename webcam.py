import logging
import json
import random
import datetime
from urllib import request

from lex import LexContext

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class Webcam:

    def __init__(self, title: str, image: str, time: int, timezone: str):
        self.title = title
        self.image = image
        self.time = time
        self.timezone = timezone

    @property
    def local_time(self) -> str:
        time = datetime.datetime.fromtimestamp(self.time, timezone(self.timezone))
        return time.strftime('%H:%M')


class WebcamSource:

    __DISTANCE_KM = 30
    __URL = 'https://webcamstravel.p.mashape.com/webcams/list/nearby={},{},{}?show=webcams:location,image'

    def __init__(self, key):
        self.__api_key = key

    def load(self, context: LexContext) -> Webcam:
        url = self.__URL.format(context.lat(), context.lng(), self.__DISTANCE_KM)
        logger.debug('WEBCAMS: url={}'.format(url))
        r = request.Request(url)
        r.add_header('X-Mashape-Key', self.__api_key)
        data = json.loads(request.urlopen(r).read().decode('utf-8'))
        webcam = random.choice(data['result']['webcams'])
        return Webcam(
            title=webcam['title'],
            image=webcam['image']['current']['preview'],
            time=webcam['update'],
            timezone=webcam['location']['timezone']
        )
