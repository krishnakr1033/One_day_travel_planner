import requests
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

load_dotenv()
GOOGLE_MAP_API_KEY=os.getenv('GOOGLE_MAP_API_KEY')

# Constants
GEOCODE_BASE_URL = 'https://maps.googleapis.com/maps/api/geocode/json'
WEATHER_BASE_URL = 'https://weather.googleapis.com/v1/forecast/hours:lookup'

def processData(response):
    df=pd.DataFrame(response['forecastHours'])

    def datedata(data):
        # Convert to datetime objects
        start_dt = datetime.strptime(data['startTime'], "%Y-%m-%dT%H:%M:%SZ")
        end_dt = datetime.strptime(data['endTime'], "%Y-%m-%dT%H:%M:%SZ")

        # Extract values
        return {
            "date" : start_dt.date(),  # Extract date
            "start_time" : start_dt.strftime("%H:%M"),  # 24-hour format
            "end_time" : end_dt.strftime("%H:%M")  # 24-hour format
        }
    
    df[['date','start_time','end_time']] = pd.json_normalize(df['interval'].apply(datedata))
    df['weatherCondition'] = df['weatherCondition'].apply(lambda dictx: [dictx['description']['text'],dictx['type']])
    df['rain_probability'] = df['precipitation'].apply(lambda dictx: dictx['probability']['percent'])
    df['qpf_in_mm'] = df['precipitation'].apply(lambda dictx: dictx['qpf']['quantity'])
    df['snowQpf_in_mm'] = df['precipitation'].apply(lambda dictx: dictx['snowQpf']['quantity'])
    df.drop(columns=['precipitation','interval','displayDateTime'],axis=1,inplace=True)
    df = df[['date', 'start_time', 'end_time','rain_probability',
        'qpf_in_mm', 'snowQpf_in_mm', 'thunderstormProbability', 'cloudCover', 'weatherCondition', 'temperature', 'feelsLikeTemperature', 'dewPoint',
        'heatIndex', 'windChill', 'wetBulbTemperature', 'airPressure', 'wind',
        'visibility', 'iceThickness', 'isDaytime', 'relativeHumidity',
        'uvIndex']]
    
    return df.to_json()

def weatherForecast(address:str):
    """
    It will give the weather details of the address of the location of visit in json format. 
    """ 
    address=address.replace(' ','+') # processing address
    params = { # params to get the latitude and longitude details
    'address': address,
    'key':GOOGLE_MAP_API_KEY
    }
    geo_params = {'address': address, 'key': GOOGLE_MAP_API_KEY}
    geo_response = requests.get(GEOCODE_BASE_URL, params=geo_params)
    geo_json = geo_response.json()

    location = geo_json['results'][0]['geometry']['location']
    LATITUDE = location['lat']
    LONGITUDE = location['lng']

    # will use the longitude and latitude details for extracting weather details
    weather_params = { # params for google weather api
        "key": GOOGLE_MAP_API_KEY,
        "location.latitude": LATITUDE,   # Replace with actual latitude
        "location.longitude": LONGITUDE  # Replace with actual longitude
    }
    weather_response = requests.get(WEATHER_BASE_URL, params=weather_params)

    weather_json = weather_response.json()
    print("Yes the llm knows the weather details")
    return processData(weather_json)

