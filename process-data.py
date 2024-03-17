import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry

def get_weather_data():
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": 52.52,               # input
        "longitude": 13.41,              # input
        "start_date": "2024-02-14",      # input
        "end_date": "2024-02-28",        # input
        "daily": "temperature_2m_min",   # fixed
        "temperature_unit": "fahrenheit" # input
    }

    # Get the data from the Open-Meteo API
    responses = openmeteo.weather_api(url, params=params)


def process_cities():
    # read the csv file in data-raw
    cities = pd.read_csv("data-raw/uscities.csv")
    print(cities.head(5))
    print(cities.columns)
    # filter the cities to only have the population greater than 10000
    cities = cities[cities["population"] > 10000]
    # merge the 'city' and 'state_name' columns to create a new column 'city_state'
    cities["city_state"] = cities["city"] + ", " + cities["state_name"]
    print(cities.head(5))
    # filter the columns to only have 'city_state', 'lat', and 'lng'
    cities = cities[["city_state", "lat", "lng"]]
    # check the total rows of the dataframe
    print(cities.shape)
    # save the file to cities.csv under /data directory
    cities.to_csv("data/cities.csv", index=False)
process_cities()
