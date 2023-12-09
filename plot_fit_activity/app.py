import dash
from dash import dcc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objs as go
import fitparse
import dash_bootstrap_components as dbc
from waitress import serve

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server


# file_name = "plot_fit_activity/resources/Morning_Run_Suunto.fit"
file_name = "plot_fit_activity/resources/Morning_Run_Garmin.fit"

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
        "distance": distance
    }
)

fig = go.Figure(
    go.Scattermapbox(
        mode = "lines",
        lon = df.longitude,
        lat = df.latitude,
        marker = {'size': 10},
        line = {'width': 3},
    )
)

fig.update_layout(
    mapbox={
        'style': "open-street-map",
        # 'center' : dict(
        #     lat=(max_latitude+min_latitude)/2,
        #     lon=(max_longitude+min_longitude)/2
        # ),
        'bounds' : dict(
            east = max_longitude+0.1,
            west = min_longitude-0.1,
            south = min_latitude-0.1,
            north = max_latitude+0.1
        )
    },
    margin={"r":0,"t":10,"l":10,"b":0},
    )


app.layout = dbc.Row(
    [
        dbc.Row(
            [
                dbc.Col([
                    dcc.Graph(id="mymap", figure=fig, config={'displayModeBar': False})
                ],
                style={'width': "25%"},
                ),
                dbc.Col([
                    dcc.Textarea(id="text")
                ]),
            ],
            
        ),
        dbc.Row(
            [
                dcc.Graph(id="time-series",config={'displayModeBar': False}),
                dcc.Dropdown(
                    id="column",
                    options=[
                        {"label": i, "value": i} for i in ["altitude", "heartrate"]
                    ],
                    value="altitude",
                ),
            ],
            style={'height': "25%"},
        ),
    ]
)




def lineplot(x, y, title="", axis_type="Linear"):
    return {
        "data": [go.Scatter(x=x, y=y, mode="lines")],
    }


@app.callback(
    Output("time-series", "figure"),
    [
        Input("column", "value"),
        Input("mymap", "selectedData")
    ],
)
def update_timeseries(column, selectedData):
    # add filter data by selectData points
    temp = df
    if selectedData is not None:
        sel_data = pd.DataFrame(selectedData['points'])
        temp = df.loc[(df.latitude.isin(sel_data.lat)) & (df.longitude.isin(sel_data.lon))]
    x = temp["time"]
    y = temp[column]
    return lineplot(x, y)


if __name__ == "__main__":
    # app.run_server(debug=False)
    # visit http://127.0.0.1:8050/ in your web browser.

    serve(server,host="localhost",port=8080)
    