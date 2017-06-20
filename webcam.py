import logging
import json
import random
import datetime
import pytz
from urllib import request

from lex import LexContext

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class Webcam:

    def __init__(self, title: str, thumbnail: str, image: str, url: str, time: int, timezone: str):
        self.title = title
        self.thumbnail = thumbnail
        self.image = image
        self.url = url
        self.time = time
        self.timezone = timezone

    @property
    def local_time(self) -> str:
        time = datetime.datetime.fromtimestamp(self.time, pytz.timezone(self.timezone))
        return time.strftime('%H:%M')


class WebcamSource:

    __DISTANCE_KM = 50
    __URL = 'https://webcamstravel.p.mashape.com/webcams/list/nearby={},{},{}/orderby=popularity/?show=webcams:location,image,url'

    def __init__(self, key):
        self.__api_key = key

    def load(self, context: LexContext) -> Webcam:
        url = self.__URL.format(context.lat, context.lng, self.__DISTANCE_KM)
        logger.debug('WEBCAMS: url={}'.format(url))
        r = request.Request(url)
        r.add_header('X-Mashape-Key', self.__api_key)
        data = json.loads(request.urlopen(r).read().decode('utf-8'))
        if data['result']['webcams']:
            webcam = random.choice(data['result']['webcams'])
            return Webcam(
                title=webcam['title'],
                thumbnail=webcam['image']['current']['thumbnail'],
                image=webcam['image']['current']['preview'],
                url=webcam['url']['current']['mobile'].replace('.travel/webcam/', '.travel/fullscreen/'),
                time=webcam['image']['update'],
                timezone=webcam['location']['timezone']
            )
        else:
            return None
