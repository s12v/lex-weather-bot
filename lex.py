import datetime
import json
import re
from dateutil import parser as date_parser
from phrases import Phrases


class ValidationError(Exception):
    def __init__(self, slot: str, message: str):
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

    __now = False
    __specific_time = False

    def __init__(self, intent: dict):
        self.intent_name = intent['currentIntent']['name']
        self.slots = intent['currentIntent']['slots']
        self.session = self.__unmarshall_session(intent.get('sessionAttributes') or {})
        self.invocation_source = intent['invocationSource']
        self.__init_date_time()

    def __init_date_time(self):
        date = self.date
        if not date:
            self.__now = True
            date = datetime.datetime.now().strftime('%Y-%m-%d')

        if self.time:
            self.__specific_time = True
            time = re.sub(r'^HIS\s+', '', self.time)  # AWS bug
            if time == 'MO':
                time = '09:00'
            elif time == 'AF':
                time = '14:00'
            elif time == 'EV':
                time = '19:00'
            elif time == 'NI':
                time = '23:00'
            date_str = '{} {}'.format(date, time)
        else:
            date_str = '{} 12:00'.format(date)
        self.timestamp = int(date_parser.parse(date_str).timestamp())

    @property
    def lat(self) -> float:
        try:
            return self.session.get('location').get('lat')
        except Exception:
            return None

    @property
    def lng(self) -> float:
        try:
            return self.session.get('location').get('lng')
        except Exception:
            return None

    @property
    def date(self) -> str:
        return self.slots.get(self.SLOT_DATE)

    @property
    def time(self) -> str:
        return self.slots.get(self.SLOT_TIME)

    @property
    def now(self) -> bool:
        return self.__now

    @property
    def specific_time(self) -> bool:
        return self.__specific_time

    @property
    def city(self) -> str:
        return self.slots.get(self.SLOT_CITY)

    @property
    def area(self) -> str:
        return self.slots.get(self.SLOT_AREA)

    @property
    def address(self):
        if self.area:
            return '{}, {}'.format(self.city, self.area)
        else:
            return self.city

    def marshall_session(self) -> dict:
        response = {}
        for k, v in self.session.items():
            response[k] = json.dumps(v)
        return response

    @staticmethod
    def __unmarshall_session(session):
        response = {}
        for k, v in session.items():
            response[k] = json.loads(v)
        return response


class LexResponses:

    @staticmethod
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

    @staticmethod
    def close(context: LexContext, fulfillment_state: str, message: dict, response_card=None) -> dict:
        response = {
            'sessionAttributes': context.marshall_session(),
            'dialogAction': {
                'type': 'Close',
                'fulfillmentState': fulfillment_state,
                'message': message
            }
        }

        if response_card:
            response['dialogAction']['responseCard'] = response_card

        return response

    @staticmethod
    def delegate(context: LexContext) -> dict:
        return {
            'sessionAttributes': context.marshall_session(),
            'dialogAction': {
                'type': 'Delegate',
                'slots': context.slots
            }
        }


class LexContextValidator:

    def validate(self, context: LexContext):
        if not context.city:
            raise ValidationError(LexContext.SLOT_CITY, Phrases.provide_city())
        if context.date and not self.__is_valid_date(context.date):
            raise ValidationError(LexContext.SLOT_DATE, Phrases.provide_date())

    @staticmethod
    def __is_valid_date(date: str) -> bool:
        try:
            date_parser.parse(date)
            return True
        except ValueError:
            return False
