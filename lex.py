import datetime
import json
from dateutil import parser as date_parser


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

    def __init__(self, intent: dict):
        self.intent_name = intent['currentIntent']['name']
        self.slots = intent['currentIntent']['slots']
        self.session = self.__unmarshall_session(intent.get('sessionAttributes') or {})
        self.invocation_source = intent['invocationSource']

    def timestamp(self) -> int:
        if self.date == 'now':
            date = datetime.datetime.now()
        else:
            if self.time:
                if self.time == 'MO':
                    self.__set_time('09:00')
                elif self.time == 'AF':
                    self.__set_time('14:00')
                elif self.time == 'EV':
                    self.__set_time('19:00')
                elif self.time == 'NI':
                    self.__set_time('23:00')
                date_str = '{} {}'.format(self.date, self.time)
            else:
                date_str = self.date
            date = date_parser.parse(date_str)
        return int(date.timestamp())

    def lat(self) -> float:
        try:
            return self.session.get('location').get('lat')
        except Exception:
            return None

    def lng(self) -> float:
        try:
            return self.session.get('location').get('lng')
        except Exception:
            return None

    @property
    def date(self) -> str:
        return self.slots.get(self.SLOT_DATE)

    @property
    def now(self) -> bool:
        return self.slots.get(self.SLOT_DATE) == 'now'

    @property
    def time(self) -> str:
        return self.slots.get(self.SLOT_TIME)

    def __set_time(self, time: str):
        self.slots[self.SLOT_TIME] = time

    @property
    def city(self) -> str:
        return self.slots.get(self.SLOT_CITY)

    @property
    def area(self) -> str:
        return self.slots.get(self.SLOT_AREA)

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
