import os
import requests
import time
import json
import humidity

with open("util.json", "r") as file:
    file_data = json.load(file)

    humidity.Humidity(file_data)



