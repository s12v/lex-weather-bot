import logging
import json
import threading
from typing import Tuple

from phrases import Phrases
from weather import WeatherSource, Weather
from geocoder import Geocoder
from lex import LexContext, LexResponses, ValidationError, LexContextValidator
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
            response = self.__handle_about_request(context)
        elif context.intent_name == LexContext.INTENT_WEATHER:
            response = self.__handle_weather_request(context)
        else:
            raise Exception('Intent with name {} not supported'.format(context.intent_name))

        logger.debug('RESPONSE={}'.format(json.dumps(response)))
        return response

    @staticmethod
    def __handle_about_request(context: LexContext):
        return LexResponses.close(
            context,
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': Phrases.howto()
            }
        )

    def __handle_weather_request(self, context: LexContext) -> dict:
        if context.invocation_source == 'DialogCodeHook':
            try:
                LexContextValidator().validate(context)
                self.__geocode(context)
            except ValidationError as err:
                return LexResponses.elicit_slot(context, err)
            return LexResponses.delegate(context)

        weather, webcam = self.__loader.load(context)
        message_content = self.__get_weather_summary(context, weather)
        return LexResponses.close(
            context,
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': message_content
            },
            self.__response_card(webcam)
        )

    @staticmethod
    def __response_card(webcam: Webcam):
        if webcam:
            return {
                'contentType': 'application/vnd.amazonaws.card.generic',
                'genericAttachments': [
                    {
                        'title': webcam.title,
                        'subTitle': webcam.local_time,
                        'imageUrl': webcam.thumbnail,
                        'attachmentLinkUrl': webcam.url,
                    }
                ]
            }
        return None

    @staticmethod
    def __get_weather_summary(context: LexContext, weather: Weather) -> str:
        if context.now:
            return "{}°C. {}. Today: {}".format(
                round(weather.at_time.temp),
                weather.at_time.summary,
                weather.day.summary
            )
        elif context.specific_time:
            return '{}°C. {}.'.format(round(weather.at_time.temp), weather.at_time.summary)
        else:
            return '{} to {}°C. {}'.format(
                round(weather.day.temp_min),
                round(weather.day.temp_max),
                weather.day.summary
            )

    def __geocode(self, context: LexContext):
        try:
            data = self.__geocoder.geocode(context)
            if len(data['results']) == 0:
                raise ValidationError(LexContext.SLOT_CITY, Phrases.provide_city())
            if len(data['results']) > 1:
                raise ValidationError(LexContext.SLOT_AREA, Phrases.provide_area_details())
            context.session['location'] = data['results'][0]['geometry']['location']
            logger.debug("GEOCODE: session={}".format(json.dumps(context.session)))
        except KeyError:
            logger.exception("Unable to load location: {}".format(context.address))
            raise ValidationError(LexContext.SLOT_CITY, Phrases.provide_city())


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
        return self.__weather_result, self.__webcam_result

    def __load_weather(self, context: LexContext):
        self.__weather_result = self.__weather_source.load(context)

    def __load_webcam(self, context: LexContext):
        try:
            if context.now:
                self.__webcam_result = self.__webcam_source.load(context)
        except Exception:
            logger.exception('Unable to load webcam')
