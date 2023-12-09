
import pandas as pd
import fitparse
import math
from statistics import mean
import numpy as np

def extract_data_from_fit(file_name):

    # Load the FIT file
    fitfile = fitparse.FitFile(file_name)

    # Iterate over all messages of type "record"
    # (other types include "device_info", "file_creator", "event", etc)
    timestamp=[]
    hr=[]
    power=[]
    altitude=[]
    latitude=[]
    max_latitude = 0
    min_latitude = 360
    longitude=[]
    max_longitude = 0
    min_longitude = 360
    distance=[]

    for record in fitfile.get_messages("record"):
        timestamp_point = None
        hr_point = None
        latitude_point = None
        longitude_point = None
        power_point = None
        altitude_point = None
        distance_point = None

        # Records can contain multiple pieces of data (ex: timestamp, latitude, longitude, etc)
        for data in record:
            if data.name == "timestamp":
                timestamp_point = data.value
            elif data.name == "heart_rate":
                hr_point = data.value
            elif data.name == "position_lat":
                if not data.raw_value is None:
                    degr = data.raw_value * ( 180 / 2**31 )
                    latitude_point = degr
                    if degr > max_latitude:
                        max_latitude = degr
                    if degr < min_latitude:
                        min_latitude = degr
            elif data.name == "position_long":
                if not data.raw_value is None:
                    degr = data.raw_value * ( 180 / 2**31 )
                    longitude_point=degr
                    if degr > max_longitude:
                        max_longitude = degr
                    if degr < min_longitude:
                        min_longitude = degr
            elif data.name == "distance":
                distance_point=data.value
            elif data.name == "power":
                power_point = data.value
            elif data.name == "enhanced_altitude":
                altitude_point=data.value

        timestamp.append(timestamp_point)
        hr.append(hr_point)
        latitude.append(latitude_point)
        longitude.append(longitude_point)
        distance.append(distance_point)
        power.append(power_point)
        altitude.append(altitude_point)

    assert len(timestamp) == len(hr) == len(latitude) == len(longitude) == len(distance) == len(power) ==len(altitude)

    df = pd.DataFrame(
        {
            "time": timestamp,
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude,
            "heartrate": hr,
            "power": power,
            "distance": distance
        }
    )

    values = {
        "max_longitude":max_longitude,
        "min_longitude":min_longitude,
        "max_latitude":max_latitude,
        "min_latitude":min_latitude,
    }

    kilometers_count = 0
    last_reset = 0
    aggregates = []
    for t,x in enumerate(df.to_dict('records')):
        if not math.isnan(x["distance"]) and math.floor(x["distance"]/1000)>kilometers_count:
            kilometers_count += 1
            delta_seconds = (x["time"]-df.time[last_reset]).seconds

            dislivello = 0
            altitude_segment = list(df.altitude[last_reset:t].dropna())
            for l in range(0, len(altitude_segment)-1):
                dislivello+= altitude_segment[l+1] - altitude_segment[l]

            aggregates.append(
                {
                    'km' : kilometers_count,
                    'passo': f"{math.floor(delta_seconds/60)}:{str(delta_seconds%60).zfill(2)} /km", 
                    'bpm': round(mean(df.heartrate[last_reset:t].dropna())),
                    'dislivello': f"{round(dislivello)} m"
                }
            )
            last_reset = t

    return df, values, aggregates