import json
import datetime
import time
import os
import dateutil.parser
import logging
import urllib
import json

geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json?address={}&key=' + os.environ['GOOGLE_KEY']

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


# --- Helper Functions ---


def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None


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
    country = slots.get('Country')
    date = slots.get('Date')

    # No city
    if not city:
        raise ValidationError('City', 'Which city?')

    # No date
    if not date:
        raise ValidationError('Date', 'Please provide a date')

    # Invalid date
    if date:
        if not is_valid_date(date):
            raise ValidationError('Date', 'I did not understand date. Could you please enter it again?')

    return {'isValid': True}


def get_location(city):
    r = urllib.request.urlopen(geocode_url.format(city))
    response = r.read().decode('utf-8')
    try:
        data = json.loads(response)
        # Todo check API errors
        return data['results'][0]['geometry']['location']
    except KeyError:
        logger.error("Unable to parse response: {}".format(response))

    return None


""" --- Functions that control the bot's behavior --- """


def weather(intent_request):

    # load city from google (i.e. validate)
    # load data from api
    # respond with data

    city = try_ex(lambda: intent_request['currentIntent']['slots']['City'])
    country = try_ex(lambda: intent_request['currentIntent']['slots']['Country'])
    date = try_ex(lambda: intent_request['currentIntent']['slots']['Date'])

    session_attributes = intent_request.get('sessionAttributes') or {}

    if intent_request['invocationSource'] == 'DialogCodeHook':
        try:
            validate_request(intent_request['currentIntent']['slots'])

            location = get_location(city)
            if not location:
                raise ValidationError('City', 'Unable to find city?')

            session_attributes['location'] = json.dumps(location)
            logger.debug('location={}'.format(json.dumps(location)))

            # ...

        except ValidationError as err:
            slots = intent_request['currentIntent']['slots']
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

    logger.debug('do stuff, session_attributes={}'.format(session_attributes))

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Done! Your location is {}'.format(session_attributes['location'])
        }
    )

# --- Main handler ---


def lambda_handler(event, context):
    logger.debug('event={}'.format(json.dumps(event)))
    return weather(event)
