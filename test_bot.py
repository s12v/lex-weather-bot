import unittest
from unittest.mock import MagicMock

from bot import WeatherBot
from darsky import DarkSky, Weather, WeatherAtTime, WeatherDay
from geocoder import Geocoder


class WeatherBotTest(unittest.TestCase):
    def test_about(self):
        result = self.__new_bot().dispatch(
            {
                'invocationSource': 'foo',
                'currentIntent': {
                    'name': 'About',
                    'slots': {
                        'Date': None,
                        'City': None,
                        'Area': None,
                        'Time': None,
                    }
                }

            }
        )
        self.assertEqual(result['dialogAction']['type'], 'Close')
        self.assertEqual(result['dialogAction']['fulfillmentState'], 'Fulfilled')

    def test_elicit_city(self):
        result = self.__new_bot().dispatch(
            {
                'invocationSource': 'DialogCodeHook',
                'currentIntent': {
                    'name': 'Weather',
                    'slots': {
                        'Date': None,
                        'City': None,
                        'Area': None,
                        'Time': None,
                    }
                }

            }
        )
        self.assertEqual(result['dialogAction']['type'], 'ElicitSlot')
        self.assertEqual(result['dialogAction']['slotToElicit'], 'City')

    def test_city_accepted(self):
        result = self.__new_bot().dispatch(
            {
                'invocationSource': 'DialogCodeHook',
                'currentIntent': {
                    'name': 'Weather',
                    'slots': {
                        'Date': None,
                        'City': 'Berlin',
                        'Area': None,
                        'Time': None,
                    }
                }

            }
        )
        self.assertEqual(result['dialogAction']['type'], 'Delegate')

    def test_tomorrow_evening(self):
        result = self.__new_bot().dispatch(
            {
                "messageVersion": "1.0",
                "invocationSource": "FulfillmentCodeHook",
                "userId": "eish8ui7ahTh0ohyah2koh4iexahheih",
                "sessionAttributes": {
                    'location': '{\"lat\": 52.52000659999999, \"lng\": 13.404954}'
                },
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
        self.assertEqual(result['dialogAction']['type'], 'Close')

    def __new_bot(self):
        darksky = DarkSky('foo')
        darksky.load = MagicMock(return_value=Weather(
                now=WeatherAtTime(20, 'Clear'),
                day=WeatherDay(19, 21, 'Mostly Cloudy')
            )
        )
        geocoder = Geocoder('foo')
        geocoder.geocode = MagicMock(return_value=
            {
                'results': [
                    {
                        'geometry': {
                            'location': {
                                'lat': 1.2,
                                'lng': 3.4
                            }
                        }

                    }

                ]
            }
        )

        return WeatherBot(darksky, geocoder)
