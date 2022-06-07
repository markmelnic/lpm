import os, json, datetime, requests

API_URL = "https://api.openweathermap.org/data/2.5/forecast?units=metric&lat={}&lon={}&appid={}"


def get_coords_weather(coords: tuple) -> list:
    req_url = API_URL.format(coords[0], coords[1], os.getenv("WEATHER_KEY"))
    response = json.loads(requests.get(req_url).content)
    sunrise = datetime.fromtimestamp(response["city"]["sunrise"]).hour
    sunset = datetime.fromtimestamp(response["city"]["sunset"]).hour
    data = []
    for item in response["list"]:
        hour = datetime.fromtimestamp(item["dt"]).hour
        if hour > sunset + 1 or hour < sunrise - 1:
            time = item["dt_txt"]
            clouds = item["clouds"]["all"]
            temperature = item["main"]["temp"]
            pressure = item["main"]["pressure"]
            humidity = item["main"]["humidity"]
            data.append([time, clouds, temperature, pressure, humidity])
    return sorted(data, key=lambda x: x[1])[0]
