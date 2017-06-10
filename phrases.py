import random


class Phrases:

    @staticmethod
    def provide_city() -> str:
        return random.choice([
            'Please provide a city',
            'What is your city?',
            'In which city?'
        ])

    @staticmethod
    def provide_area_details() -> str:
        return random.choice([
            'I found several places with this name. Could you provide country or state?',
        ])

    @staticmethod
    def provide_date() -> str:
        return random.choice([
            'Please provide a date',
            'When?'
        ])

    @staticmethod
    def howto() -> str:
        return random.choice([
            'I\'m a weather bot. I can provide weather forecast and historical data. For example, ask "Weather '
            'in Berlin?", or "Weather in Moscow on 1st of January?"',
            'I\'m a bot. I can provide historical weather data and forecasts. For example, ask "What '
            'was the weather in Chicago yesterday?", or "Weather in Furnace Creek?"',
        ])
