import os
import requests
import time

from dotenv import load_dotenv

load_dotenv()
KEY_AIRNOW = os.getenv("KEY-AIRNOW")


class AQITracker:
    def __init__(self):
        self.last_query_time = time.time()
        self.payload = {"zipCode": "98005", "format": "application/json", "api_key": KEY_AIRNOW}
        self.r = requests.get("https://www.airnowapi.org/aq/observation/zipCode/current", params=self.payload)
        self.aqi = max(self.r.json()[0]["AQI"], self.r.json()[1]["AQI"])

    def aqi_acceptable(self):
        if time.time() - self.last_query_time > 5:
            print("getting new aqi value")
            self.r = requests.get("https://www.airnowapi.org/aq/observation/zipCode/current", params=self.payload)
            self.aqi = max(self.r.json()[0]["AQI"], self.r.json()[1]["AQI"])
            self.last_query_time = time.time()
        else:
            print("too soon to query")
        if self.aqi < 50:
            return True
        return False


