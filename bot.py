import logging
import json
import threading
from typing import Tuple
from dateutil import parser as dateutil_parser

from phrases import Phrases
from weather import WeatherSource, Weather
from geocoder import Geocoder
from lex import LexContext, LexResponses, ValidationError
from webcam import Webcam, WebcamSource

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class WeatherBot:
    def __init__(self, weather_source: WeatherSource, geocoder: Geocoder, webcam_source: WebcamSource):
        self.__loader = AsyncLoader(weather_source, webcam_source)
        self.__geocoder = geocoder

    def dispatch(self, intent: dict) -> dict:
        context = LexContext(intent)
        if context.intent_name == LexContext.INTENT_ABOUT:
            response = self.__about_request(context)
        elif context.intent_name == LexContext.INTENT_WEATHER:
            response = self.__weather_request(context)
        else:
            raise Exception('Intent with name {} not supported'.format(context.intent_name))

        logger.debug('RESPONSE={}'.format(json.dumps(response)))
        return response

    @staticmethod
    def __about_request(context: LexContext):
        return LexResponses.close(
            context,
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': Phrases.howto()
            }
        )

    def __weather_request(self, context: LexContext) -> dict:
        if context.invocation_source == 'DialogCodeHook':
            try:
                self.__validate(context)
                self.__geocode(context)
            except ValidationError as err:
                return LexResponses.elicit_slot(context, err)
            return LexResponses.delegate(context)

        weather, webcam = self.__loader.load(context)
        message_content = self.__get_weather_summary(context, weather)
        if webcam:
            response_card = {
                "contentType": "application/vnd.amazonaws.card.generic",
                "genericAttachments": [
                    {
                        "title": webcam.title,
                        "subTitle": webcam.local_time,
                        "imageUrl": webcam.thumbnail,
                        "attachmentLinkUrl": webcam.url,
                    }
                ]
            }
        else:
            response_card = None

        return LexResponses.close(
            context,
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': message_content
            },
            response_card
        )

    @staticmethod
    def __get_weather_summary(context: LexContext, weather: Weather) -> str:
        if context.now:
            return "{} degrees. {}. Today: ".format(round(weather.now.temp), weather.now.summary, weather.day.summary)
        elif context.time:
            return '{} degrees. {}.'.format(round(weather.now.temp), weather.now.summary)
        else:
            return '{} to {} degrees. {}'.format(
                round(weather.day.temp_min),
                round(weather.day.temp_max),
                weather.day.summary
            )

    def __validate(self, context: LexContext):
        if not context.city:
            raise ValidationError(LexContext.SLOT_CITY, Phrases.provide_city())

        if not context.date or context.date == 'now':
            context.slots[LexContext.SLOT_DATE] = 'now'
        elif not self.__is_valid_date(context.date):
            raise ValidationError(LexContext.SLOT_DATE, 'I did not understand date. Could you please enter it again?')

    def __geocode(self, context: LexContext):
        try:
            data = self.__geocoder.geocode(self.__address(context))
            if len(data['results']) == 0:
                raise ValidationError(LexContext.SLOT_CITY, Phrases.provide_city())
            if len(data['results']) > 1:
                raise ValidationError(LexContext.SLOT_AREA, Phrases.provide_area_details())
            context.session['location'] = data['results'][0]['geometry']['location']
            logger.debug("GEOCODE: session={}".format(json.dumps(context.session)))
        except KeyError:
            logger.exception("Unable to load location: {}".format(self.__address(context)))
            raise ValidationError(LexContext.SLOT_CITY, Phrases.provide_city())

    @staticmethod
    def __is_valid_date(date: str) -> bool:
        try:
            dateutil_parser.parse(date)
            return True
        except ValueError:
            return False

    @staticmethod
    def __address(context: LexContext):
        if context.area:
            return '{}, {}'.format(context.city, context.area)
        else:
            return context.city


class AsyncLoader:
    __weather_result = None
    __webcam_result = None

    def __init__(self, weather_source: WeatherSource, webcam_source: WebcamSource):
        self.__weather_source = weather_source
        self.__webcam_source = webcam_source

    def load(self, context: LexContext) -> Tuple[Weather, Webcam]:
        self.__weather_result = None
        self.__webcam_result = None
        threads = [
            threading.Thread(target=self.__load_weather, args=[context]),
            threading.Thread(target=self.__load_webcam, args=[context]),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return (self.__weather_result, self.__webcam_result)

    def __load_weather(self, context: LexContext):
        self.__weather_result =  self.__weather_source.load(context)

    def __load_webcam(self, context: LexContext):
        try:
            if context.now:
                self.__webcam_result = self.__webcam_source.load(context)
        except Exception:
            logger.exception('Unable to load webcam')
