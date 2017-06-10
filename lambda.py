import datetime
import os
import dateutil.parser
import logging
import urllib
import json
import random

geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json?address={}&key=' + os.environ['GOOGLE_KEY']
darksky_url = 'https://api.darksky.net/forecast/' + os.environ['DARKSKY_KEY'] + '/{},{},{}?exclude=minutely,hourly,flags&units=auto'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class ValidationError(Exception):
    def __init__(self, slot, message):
        super(ValidationError, self).__init__(message)
        self.slot = slot
        self.message = message


class LexContext:

    INTENT_ABOUT = 'About'
    INTENT_WEATHER = 'Weather'
    SLOT_CITY = 'City'
    SLOT_AREA = 'Area'
    SLOT_DATE = 'Date'
    SLOT_TIME = 'Time'

    def __init__(self, intent: dict):
        self.intent_name = intent['currentIntent']['name']
        self.slots = intent['currentIntent']['slots']
        self.session = intent.get('sessionAttributes') or {}
        self.invocation_source = intent['invocationSource']

    def validate(self):
        if not self.slots.get(self.SLOT_CITY):
            raise ValidationError(self.SLOT_CITY, provide_city())

        if not self.slots.get(self.SLOT_DATE):
            self.slots[self.SLOT_DATE] = "now"
        elif not self.__is_valid_date(self.slots.get(self.SLOT_DATE)):
            raise ValidationError(self.SLOT_DATE, 'I did not understand date. Could you please enter it again?')

    def geocode(self, geocode_func: callable):
        if self.slots.get(self.SLOT_AREA):
            address = self.slots.get(self.SLOT_CITY) + ", " + self.slots.get(self.SLOT_AREA)
        else:
            address = self.slots.get(self.SLOT_CITY)
        try:
            response = geocode_func(address)
            data = json.loads(response)
            if len(data['results']) == 0:
                raise ValidationError('City', provide_city())
            if len(data['results']) > 1:
                raise ValidationError('Area', provide_area_details())
            self.session['location'] = data['results'][0]['geometry']['location']
            self.session['formatted_address'] = data['results'][0]['formatted_address']
        except Exception:
            logger.error("Unable to load location: {}".format(address))
            raise ValidationError(self.SLOT_CITY, provide_city())

    def timestamp(self) -> int:
        if self.slots(self.SLOT_DATE) == 'now':
            date = datetime.datetime.now()
        else:
            time = self.slots.get(self.SLOT_TIME)
            if time:
                date_str = '{} {}'.format(self.slots(self.SLOT_DATE), self.slots(self.SLOT_TIME))
            else:
                date_str = self.slots(self.SLOT_DATE)
            date = dateutil.parser.parse(date_str)
        return int(date.timestamp())

    def lat(self) -> float:
        try:
            return self.session.get('location').get('lat')
        except KeyError:
            return None

    def lng(self) -> float:
        try:
            return self.session.get('location').get('lng')
        except KeyError:
            return None

    def date(self) -> str:
        return self.slots(self.SLOT_DATE)

    def dump_session(self) -> dict:
        response = {}
        for k, v in self.session:
            response[k] = json.dumps(v)
        return response

    def __is_valid_date(self, date: str) -> bool:
        try:
            dateutil.parser.parse(date)
            return True
        except ValueError:
            return False


# --- Helpers that build all of the responses ---


def elicit_slot(context: LexContext, error: ValidationError) -> dict:
    slots = context.slots.copy()
    slots[error.slot] = None
    return {
        'sessionAttributes': {},
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': context.intent_name,
            'slots': slots,
            'slotToElicit': error.slot,
            'message': {
                'contentType': 'PlainText',
                'content': error.message
            }
        }
    }


def close(context: LexContext, fulfillment_state: str, message: dict) -> dict:
    logger.debug("CLOSE: state={}, session={}".format(fulfillment_state, json.dumps(context.session)))
    return {
        'sessionAttributes': context.dump_session(),
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }


def delegate(context: LexContext) -> dict:
    logger.debug('DELEGATE: slots={}, session={}'.format(json.dumps(context.slots), json.dumps(context.session)))
    return {
        'sessionAttributes': context.dump_session(),
        'dialogAction': {
            'type': 'Delegate',
            'slots': context.slots
        }
    }


def provide_city() -> str:
    return random.choice([
        'Please provide a city',
        'What is your city?',
        'In which city?'
    ])


def provide_area_details() -> str:
    return random.choice([
        'I found several places with this name. Could you provide country or state?',
    ])


def provide_date() -> str:
    return random.choice([
        'Please provide a date',
        'When?'
    ])


def howto() -> str:
    return random.choice([
        "I'm a weather bot. I can provide weather forecast and historical data. For example, ask \"Weather "
        "in Berlin?\", or \"Weather in Moscow on 1st of January?\"",
        "I'm a bot. I can provide historical weather data and forecasts. For example, ask \"What "
        "was the weather in Chicago yesterday?\", or \"Weather in Furnace Creek?\"",
    ])


# --- Helper Functions ---


def do_geocode(address):
    url = geocode_url.format(urllib.parse.quote(address, 'utf-8'))
    logger.debug("GEOCODE: {}".format(url))
    return urllib.request.urlopen(url).read().decode('utf-8')


def load_weather(context: LexContext) -> dict:
    url = darksky_url.format(context.lat(), context.lng(), context.timestamp())
    logger.debug("DARKSKY: {}".format(url))
    response = urllib.request.urlopen(url).read().decode('utf-8')
    try:
        data = json.loads(response)
        return {
            "now": data['currently'],
            "day": data['daily']['data'][0]
        }
    except KeyError:
        logger.error("Unable to parse response: {}".format(response))

    return None


def get_weather_summary(context: LexContext, weather: dict) -> str:
    if context.date() == 'now':
        now = weather.get('now')
        temp = round(now.get('temperature'))
        summary = now.get('summary')
        return "Currently it's {} degrees. {}".format(temp, summary)
    else:
        day = weather.get('day')
        min_temp = round(day.get('temperatureMin'))
        max_temp = round(day.get('temperatureMax'))
        summary = day.get('summary')
        return "{} to {} degrees. {}".format(min_temp, max_temp, summary)


def weather_request(context: LexContext) -> dict:
    if context.invocation_source == 'DialogCodeHook':
        try:
            context.validate()
            context.geocode(do_geocode)
        except ValidationError as err:
            return elicit_slot(context, err)
        return delegate(context)

    return close(
        context,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': get_weather_summary(context, load_weather(context))
        }
    )


def about_request(context: LexContext):
    return close(
        context,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': howto()
        }
    )


# --- Intents ---


def dispatch(intent):
    context = LexContext(intent)
    if context.intent_name == LexContext.INTENT_ABOUT:
        response = about_request(context)
    elif context.intent_name == LexContext.INTENT_WEATHER:
        response = weather_request(context)
    else:
        raise Exception('Intent with name ' + context.intent_name + ' not supported')

    logger.debug('RESPONSE:' + json.dumps(response))
    return response


# --- Main handler ---


def lambda_handler(event, context):
    logger.debug('event={}'.format(json.dumps(event)))
    return dispatch(event)
