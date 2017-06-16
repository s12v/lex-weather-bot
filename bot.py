import logging
import json
from dateutil import parser as dateutil_parser
from urllib import request

from phrases import Phrases
from darsky import DarkSky, Weather
from geocoder import Geocoder
from lex import LexContext, LexResponses, ValidationError

logger = logging.getLogger()
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

    def __load_webcam(self, context: LexContext) -> dict:
        try:
            u = 'https://webcamstravel.p.mashape.com/webcams/list/nearby={},{},30?show=webcams:location,image'
            url = u.format(context.lat(), context.lng())
            logger.debug('WEBCAMS: url={}'.format(url))
            r = request.Request(url)
            r.add_header('X-Mashape-Key', 'GrQemzLeVMmshGEEMujsXBpIRcRpp1XGI7Ojsn4EioK6QdNGhP')
            data = json.loads(request.urlopen(r).read().decode('utf-8'))
            webcam = data['result']['webcams'][0]
            return {
                'title': webcam['title'],
                'image': webcam['image']['current']['preview']
            }
        except Exception:
            return None

    def __weather_request(self, context: LexContext) -> dict:
        if context.invocation_source == 'DialogCodeHook':
            try:
                self.__validate(context)
                self.__geocode(context)
            except ValidationError as err:
                return LexResponses.elicit_slot(context, err)
            return LexResponses.delegate(context)

        weather = self.__darksky.load(context)
        message_content = self.__get_weather_summary(context, weather)
        webcam = self.__load_webcam(context)
        if webcam:
            response_card = {

                "contentType": "application/vnd.amazonaws.card.generic",
                "genericAttachments": [
                    {
                        "title": webcam['title'],
                        "subTitle": message_content,
                        "imageUrl": webcam['image']
                    }
                ]
            }
            message = {
                'contentType': 'PlainText',
                'content': message_content
            }
        else:
            message = {
                'contentType': 'PlainText',
                'content': message_content
            }
            response_card = None

        return LexResponses.close(
            context,
            'Fulfilled',
            message,
            response_card
        )

    @staticmethod
    def __icon_url(weather: Weather) -> str:
        icons = ['clear-day', 'clear-night', 'rain', 'snow', 'sleet', 'wind', 'fog',
                 'cloudy', 'partly-cloudy-day' 'partly-cloudy-night']
        # TODO
        if weather.day == 'now':
            icon = weather.now.icon
        else:
            icon = weather.day.icon
        if icon in icons:
            return 'https://s3.amazonaws.com/simple-weather-bot/{}.png?v3'.format(icon)

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

        if not context.date() or context.date() == 'now':
            context.slots[LexContext.SLOT_DATE] = 'now'
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
            logger.debug("GEOCODE: session={}".format(json.dumps(context.session)))
        except Exception:
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
