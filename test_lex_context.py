import datetime
from dateutil import parser as date_parser
import unittest

from lex import LexContext


class LexContextTest(unittest.TestCase):

    def test_lex_context(self):
        lex = LexContext(
            {
                'invocationSource': 'foo',
                'currentIntent': {
                    'name': 'test1',
                    'slots': {
                        'Date': '2017-06-10',
                        'City': 'Berlin'
                    }
                }

            }
        )
        self.assertEqual(lex.date, '2017-06-10')
        self.assertEqual(lex.city, 'Berlin')
        self.assertIsNone(lex.time)
        self.assertIsNone(lex.area)

    def test_tomorrow_evening(self):
        lex = LexContext(
            {
                "messageVersion": "1.0",
                "invocationSource": "FulfillmentCodeHook",
                "userId": "eish8ui7ahTh0ohyah2koh4iexahheih",
                "sessionAttributes": {},
                "bot": {
                    "name": "WeatherBot",
                    "alias": None,
                    "version": "$LATEST"
                },
                "outputDialogMode": "Text",
                "currentIntent": {
                    "name": "Weather",
                    "slots": {
                        "Area": None,
                        "Time": "EV",
                        "City": "Berlin",
                        "Date": "2017-06-11"
                    },
                    "confirmationStatus": "None"
                },
                "inputTranscript": "weather tomorrow evening in Berlin"
            }
        )
        self.assertEqual(lex.timestamp, date_parser.parse('2017-06-11 19:00').timestamp())


    def test_this_evening_buggy(self):
        lex = LexContext(
            {
                "messageVersion": "1.0",
                "invocationSource": "FulfillmentCodeHook",
                "userId": "eish8ui7ahTh0ohyah2koh4iexahheih",
                "sessionAttributes": {},
                "bot": {
                    "name": "WeatherBot",
                    "alias": None,
                    "version": "$LATEST"
                },
                "outputDialogMode": "Text",
                "currentIntent": {
                    "name": "Weather",
                    "slots": {
                        "Area": None,
                        "Time": "HIS EV",
                        "City": "Berlin",
                        "Date": None
                    },
                    "confirmationStatus": "None"
                },
                "inputTranscript": "weather tomorrow evening in Berlin"
            }
        )
        self.assertEqual(lex.timestamp, date_parser.parse('{} 19:00'.format(datetime.datetime.now().strftime('%Y-%m-%d'))).timestamp())
