import json
import datetime
import time
import os
import dateutil.parser
import logging

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


""" --- Functions that control the bot's behavior --- """


def weather(intent_request):

    # load city from google (i.e. validate)
    # load data from api
    # respond with data

    city = try_ex(lambda: intent_request['currentIntent']['slots']['City'])
    country = try_ex(lambda: intent_request['currentIntent']['slots']['Country'])
    date = try_ex(lambda: intent_request['currentIntent']['slots']['Date'])

    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    user_data = json.dumps({
        'city': city,
        'country': country,
        'date': date
    })
    session_attributes['user_data'] = user_data

    if intent_request['invocationSource'] == 'DialogCodeHook':
        try:
            validate_request(intent_request['currentIntent']['slots'])
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

        return delegate(session_attributes, intent_request['currentIntent']['slots'])

    logger.debug('do stuff')

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Done!!'
        }
    )

# --- Main handler ---


def lambda_handler(event, context):
    logger.debug('event={}'.format(json.dumps(event)))
    return weather(event)
