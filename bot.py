import logging
import json
import datetime
from dateutil import parser as dateutil_parser

from phrases import Phrases
from darsky import DarkSky, Weather
from geocoder import Geocoder
from lex import LexContext, LexResponses, ValidationError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class WeatherBot:

    def __init__(self, darksky: DarkSky, geocoder: Geocoder):
        self.__darksky = darksky
        self.__geocoder = geocoder

    def dispatch(self, intent: dict) -> dict:
        context = LexContext(intent)
        if context.intent_name == LexContext.INTENT_ABOUT:
            response = self.__about_request(context)
        elif context.intent_name == LexContext.INTENT_WEATHER:
            response = self.__weather_request(context)
        else:
            raise Exception('Intent with name ' + context.intent_name + ' not supported')

        logger.debug('RESPONSE:' + json.dumps(response))
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

        return LexResponses.close(
            context,
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': self.__get_weather_summary(context, self.__darksky.load(context))
            }
        )

    @staticmethod
    def __get_weather_summary(context: LexContext, weather: Weather) -> str:
        if context.date() == 'now':
            return "Currently it's {} degrees. {}".format(round(weather.now.temp), weather.now.summary)
        elif context.time():
            # hi = datetime.datetime.fromtimestamp(context.timestamp()).strftime('%H:%M')
            return '{} degrees. {}.'.format(round(weather.now.temp), weather.now.summary)
        else:
            return '{} to {} degrees. {}'.format(
                round(weather.day.temp_min),
                round(weather.day.temp_max),
                weather.day.summary
            )

    def __validate(self, context: LexContext):
        if not context.city():
            raise ValidationError(LexContext.SLOT_CITY, Phrases.provide_city())

        if not context.date():
            context.slots[LexContext.SLOT_DATE] = "now"
        elif not self.__is_valid_date(context.date()):
            raise ValidationError(LexContext.SLOT_DATE, 'I did not understand date. Could you please enter it again?')

    def __geocode(self, context: LexContext):
        try:
            data = self.__geocoder.geocode(self.__address(context))
            if len(data['results']) == 0:
                raise ValidationError('City', Phrases.provide_city())
            if len(data['results']) > 1:
                raise ValidationError('Area', Phrases.provide_area_details())
            context.session['location'] = data['results'][0]['geometry']['location']
            logger.debug("SESSION: {}".format(json.dumps(context.session)))
        except Exception as err:
            logger.error("Unable to load location: {}".format(self.__address(context)))
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
        if context.area():
            return '{}, {}'.format(context.city(), context.area())
        else:
            return context.city()
