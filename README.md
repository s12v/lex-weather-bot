
# Simple Weather Bot

This bot is integrated with Facebook and can: 
 - tell you about current weather conditions in specified place
 - send a recent photo from a nearby webcam
 - provide historical data about weather, for example you can ask "Weather in Barcelona on 10th of October"
 - provide forecasts, e.g. "weather in Berlin tomorrow morning", "Sunday evening" and so on.

![Architecture](https://user-images.githubusercontent.com/1462574/27773400-18ac110e-5f79-11e7-9530-46af85fc304a.png)

It uses Google Geocode and Timezone, DarkSky weather, and Webcams.travel APIs.

## How to run it

### Install modules

```
python3 -m pip install --target=. pytz
```

### Run tests
```
python3 -m unittest discover -v
```

### Deploy

```
serverless deploy
```
