import json
import unittest
from unittest.mock import MagicMock

from bot import WeatherBot
from darsky import DarkSky
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

    def test_elicit_city2(self):
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

    def __new_bot(self):
        darksky = DarkSky('foo')
        darksky.load = MagicMock(return_value=dict(now='foo', day='bar'))
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
