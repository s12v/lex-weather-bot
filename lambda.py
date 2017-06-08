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


# --- Helpers that build all of the responses ---


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


def provide_city():
    return random.choice([
        'Please provide a city',
        'What is your city?',
        'In which city?'
    ])


def provide_area_details():
    return random.choice([
        'I found several places with this name. Could provide country or state?',
    ])


def provide_date():
    return random.choice([
        'Please provide a date',
        'When?'
    ])


def help():
    return random.choice([
        "I'm a weather bot. I can provide weather forecast and historical data. For example, ask \"Weather "
        "in Berlin?\", or \"Weather in Moscow on 1st of January?\"",
        "I'm a bot. I can provide historical weather data and forecasts. For example, ask \"What "
        "was the weather in Chicago yesterday?\", or \"Weather in Furnace Creek?\"",
    ])


# --- Helper Functions ---


def is_valid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


class ValidationError(Exception):
    def __init__(self, slot, message):
        super(ValidationError, self).__init__(message)
        self.slot = slot
        self.message = message


def validate_request(slots):
    city = slots.get('City')
    date = slots.get('Date')

    # No city
    if not city:
        raise ValidationError('City', provide_city())

    if date and not is_valid_date(date):
            raise ValidationError('Date', 'I did not understand date. Could you please enter it again?')

    return {'isValid': True}


def get_location(city, area):
    location = city + ", " + area if area else city
    url = geocode_url.format(urllib.parse.quote(location, 'utf-8'))
    logger.debug("Loading {}".format(url))
    response = urllib.request.urlopen(url).read().decode('utf-8')
    try:
        data = json.loads(response)
        # Todo check API errors
        if len(data['results']) > 1:
            raise ValidationError('Area', provide_area_details())
        return {
            'location': data['results'][0]['geometry']['location'],
            'formatted_address': data['results'][0]['formatted_address']
        }
    except KeyError:
        logger.error("Unable to parse response: {}".format(response))

    return None


def get_weather(lat, lng, date_str):
    date = datetime.datetime.now() if date_str == 'now' else dateutil.parser.parse(date_str)
    timestamp = date.timestamp()
    url = darksky_url.format(lat, lng, int(timestamp))
    logger.debug("Loading {}".format(url))
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


def get_weather_summary(weather, formatted_address, date):
    if date == 'now':
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


def weather_request(intent_request):

    slots = intent_request['currentIntent']['slots']
    city = slots.get('City')
    area = slots.get('Area')
    date = slots.get('Date')
    time = slots.get('Time')
    if not date:
        date = "now"

    session_attributes = intent_request.get('sessionAttributes') or {}

    if intent_request['invocationSource'] == 'DialogCodeHook':
        try:
            validate_request(slots)

            location = get_location(city, area)
            if not location:
                raise ValidationError('City', 'Unable to find city?')

            session_attributes['location'] = json.dumps(location)
            logger.debug('Found location {} for city {}'.format(json.dumps(location), city))

        except ValidationError as err:
            slots[err.slot] = None
            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                err.slot,
                {'contentType': 'PlainText', 'content': err.message}
            )

        logger.debug('delegate, session_attributes={}'.format(session_attributes))
        return delegate(session_attributes, intent_request['currentIntent']['slots'])

    location = json.loads(session_attributes['location'])
    weather = get_weather(lat=location['location']['lat'], lng=location['location']['lng'], date_str=date)
    logger.debug("Fulfill, session_attributes: {}".format(session_attributes))

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': get_weather_summary(weather, location['formatted_address'], date)
        }
    )


def about_request():
    return close(
        {},
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': help()
        }
    )


# --- Intents ---


def dispatch(intent_request):
    intent_name = intent_request['currentIntent']['name']
    if intent_name == 'Weather':
        return weather_request(intent_request)
    elif intent_name == 'About':
        return about_request()

    raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---


def lambda_handler(event, context):
    logger.debug('event={}'.format(json.dumps(event)))
    return dispatch(event)
