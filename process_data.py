import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry


def get_weather_data(**kwargs):
    # parse the parameters
    latitude = kwargs.get("latitude")
    longitude = kwargs.get("longitude")
    start_date = kwargs.get("start_date")
    end_date = kwargs.get("end_date")
    temperature_unit = kwargs.get("temperature_unit")
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,  # input
        "longitude": longitude,  # input
        "start_date": start_date,  # input
        "end_date": end_date,  # input
        "daily": "temperature_2m_min",  # fixed
        "temperature_unit": temperature_unit  # input
    }

    # Get the data from the Open-Meteo API
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    daily = response.Daily()
    daily_temperature_2m = daily.Variables(0).ValuesAsNumpy()

    # this part is copied from the Open-Meteo API documentation
    daily_data = {"date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    ), "temperature_2m": daily_temperature_2m}
    daily_dataframe = pd.DataFrame(data=daily_data)

    return daily_dataframe, f"Coordinates {response.Latitude()}°N {response.Longitude()}°E"


def process_cities():
    cities = pd.read_csv("data-raw/uscities.csv")
    print(cities.head(5))
    print(cities.columns)
    cities = cities[cities["population"] > 10000]
    # merge
    cities["city_state"] = cities["city"] + ", " + cities["state_name"]
    print(cities.head(5))
    # filter
    cities = cities[["city_state", "lat", "lng"]]
    print(cities.shape)
    cities.to_csv("data/cities.csv", index=False)
