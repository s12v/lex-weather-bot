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
        self.assertEqual(lex.date(), '2017-06-10')
        self.assertEqual(lex.city(), 'Berlin')
        self.assertIsNone(lex.time())
        self.assertIsNone(lex.area())
