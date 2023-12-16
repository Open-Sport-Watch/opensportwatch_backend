
import pandas as pd
import fitparse
import math
from statistics import mean
import time
import pickle
import os

def extract_data_from_fit(file_name):

    if os.path.isfile(f"{file_name}.pickle"):
        with open(f'{file_name}.pickle', 'rb') as file:       
            messages = pickle.load(file)    
        df, positions, positions_for_km, altitude_for_km, time_for_km, activity, summary, aggregates, aggregates_columns, settings, icon= messages

    else:
        
        # Load the FIT file
        fitfile = fitparse.FitFile(file_name)

        # Iterate over all messages of type "record"
        # (other types include "device_info", "file_creator", "event", etc)
        activity_name=""
        activity_type=""
        activity_subtype=""
        activity_start=""
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
        speed=[]
        pace=[]

        t = time.time()
        messages = fitfile.messages
        elapsed = round(time.time() - t, 1)
        print(f"loaded the fit file in {str(elapsed)} seconds")

        sports=list(filter(lambda mess: mess.def_mesg.name=="sport", messages))
        for sport in sports:
            for data in sport:
                if data.name == "name":
                    activity_name = data.value
                elif data.name == "sub_sport":
                    activity_subtype = data.value
                elif data.name == "sport":
                    activity_type = data.value

        records=list(filter(lambda mess: mess.def_mesg.name=="record", messages))
        for record in records:
            timestamp_point = None
            hr_point = None
            latitude_point = None
            longitude_point = None
            power_point = None
            altitude_point = None
            distance_point = None
            speed_point = None
            pace_point = None

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
                elif data.name == "enhanced_speed":
                    speed_point=data.value
                    if data.value == 0:
                        pace_point = None
                    else:
                        pace_point= 1000/(data.value * 60)

            timestamp.append(timestamp_point)
            hr.append(hr_point)            
            distance.append(distance_point)
            latitude.append(latitude_point)
            longitude.append(longitude_point)
            speed.append(speed_point)
            pace.append(pace_point)

            power.append(power_point)
            altitude.append(altitude_point)

        assert len(timestamp) == len(hr) == len(latitude) == len(longitude) == len(distance) == len(power) ==len(altitude)

        activity_start=timestamp[0]

        df1 = pd.DataFrame(
            {
                "pace": pace
            }
        )
        pace_smoot = df1.pace.rolling(window=90, min_periods=10, center=True).median()

        df = pd.DataFrame(
            {
                "time": timestamp,
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "heartrate": hr,
                "power": power,
                "distance": distance,
                "speed": speed,
                "pace": pace,
                "pace_smoot": pace_smoot
            }
        )

        positions=[]
        for x,y in enumerate(df.latitude):
            if not math.isnan(df.latitude[x]) and not math.isnan(df.longitude[x]) and  \
                not df.latitude[x] is None and not df.longitude[x] is None:
                positions.append([df.latitude[x],df.longitude[x]])

        last_kilometer = 0
        positions_for_km=[] #* math.floor(distance[-1]/1000)
        altitude_for_km=[]
        time_for_km=[]
        for x,y in enumerate(distance):
            if not y is None and not latitude[x] is None and not longitude[x] is None:
                if math.floor(distance[x]/1000) > last_kilometer:
                    last_kilometer +=1
                else:
                    if len(positions_for_km)<last_kilometer+1:
                        positions_for_km.append([[latitude[x],longitude[x]]])
                        altitude_for_km.append([altitude[x]])
                        time_for_km.append([timestamp[x]])
                    else:
                        positions_for_km[last_kilometer].append([latitude[x],longitude[x]])
                        altitude_for_km[last_kilometer].append(altitude[x])
                        time_for_km[last_kilometer].append(timestamp[x])


        kilometers_count = 0
        last_reset = 0
        aggregates = []
        tot_ascent = 0
        tot_descendent = 0
        for t,x in enumerate(df.to_dict('records')):
            if not math.isnan(x["distance"]) and math.floor(x["distance"]/1000)>kilometers_count:
                kilometers_count += 1
                delta_seconds = (x["time"]-df.time[last_reset]).seconds

                ascent = 0
                descendent = 0
                altitude_segment = list(df.altitude[last_reset:t].dropna())
                for l in range(0, len(altitude_segment)-1):
                    delta = altitude_segment[l+1] - altitude_segment[l]
                    if delta >0:
                        tot_ascent += delta
                        ascent+= delta
                    else:
                        tot_descendent += delta
                        descendent+=delta

                aggregates.append(
                    {
                        'km' : kilometers_count,
                        'pace': f"{math.floor(delta_seconds/60)}:{str(delta_seconds%60).zfill(2)}/km", 
                        'bpm': round(mean(df.heartrate[last_reset:t].dropna())),
                        'ascent': f"{round(ascent)} m",
                        'descent': f"{round(descendent)} m"
                    }
                )
                last_reset = t

        aggregates_columns=[
            {
                "headerName": 'Intertemps',
                "children": [
                    {"field": "km"},
                    {"field": "pace"},
                    {"field": "bpm"},
                    {"field": "ascent"},
                    {"field": "descent"},
                ]
            }
        ]

        tot_time_seconds = (df.time.values[-1]-df.time[0]).seconds
        tot_distance = round(df.distance.values[-1]/1000,2)
        avg_pace = tot_time_seconds/(60*tot_distance)
        settings = {
            "max_longitude":max_longitude,
            "min_longitude":min_longitude,
            "max_latitude":max_latitude,
            "min_latitude":min_latitude,
        }

        summary = [
            {
                f"{tot_distance} km":"Distance",
                f"{str(math.floor(tot_time_seconds/3600)).zfill(2)}:{str(math.floor((tot_time_seconds%3600)/60)).zfill(2)}:{str(math.floor((tot_time_seconds%3600)%60)).zfill(2)}":"Time",
                f"{math.floor(avg_pace)}:{str(round((avg_pace%1)*60)).zfill(2)}/km":"Average\npace",
                f"{round(tot_ascent)} m" : "Total\nascendent",
                f"{round(tot_descendent)} m": "Total\ndescendent",
            }
        ]

        activity = {
            "type": activity_type,
            "subtype": activity_subtype,
            "start": activity_start,
            "name": activity_name
        }

        icon = "running.png"
        if activity["type"]=="running":
            if activity["subtype"]=="trail":
                icon = "trail_running.png"

        with open(f"{file_name}.pickle", 'wb') as file: 
            pickle.dump([df, positions, positions_for_km, altitude_for_km, time_for_km, activity, summary, aggregates, aggregates_columns, settings, icon], file) 

    return df, positions, positions_for_km, altitude_for_km, time_for_km, activity, summary, aggregates, aggregates_columns, settings, icon