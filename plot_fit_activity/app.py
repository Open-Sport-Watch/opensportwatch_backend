import dash
from dash import dcc, dash_table, html
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
from waitress import serve
from src.manage_fit import extract_data_from_fit




# file_name = "plot_fit_activity/resources/Morning_Run_Suunto.fit"
# file_name = "plot_fit_activity/resources/Morning_Run_Garmin.fit"
# file_name = "plot_fit_activity/resources/Morning_Trail_Run.fit"
file_name = "plot_fit_activity/resources/Pesaro-Cattolica.fit"

df, activity, summary, aggregates, aggregates_columns, settings = extract_data_from_fit(file_name)

icon = "running.png"
if activity["type"]=="running":
    if activity["subtype"]=="trail":
        icon = "trail_running.png"

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
            east = settings["max_longitude"]+0.1,
            west = settings["min_longitude"]-0.1,
            south = settings["min_latitude"]-0.1,
            north = settings["max_latitude"]+0.1
        )
    },
    margin={"r":10,"t":10,"l":10,"b":0},
    )

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=df.time, y=df.heartrate, mode="lines",line=dict(color='rgb(220,20,60)', width=2), name="heartrate", connectgaps=True,))
fig2.add_trace(go.Scatter(x=df.time, y=df.power, mode="lines",line=dict(color='rgb(34,139,34)', width=2), name="power", connectgaps=True,))
fig2.add_trace(go.Scatter(x=df.time, y=df.altitude, mode="lines",line=dict(color='rgb(49,130,189)', width=2), name="altitude", connectgaps=True,))

fig2.update_layout(
    xaxis=dict(
        showline=True,
        showgrid=False,
        showticklabels=True,
        linecolor='rgb(204, 204, 204)',
        linewidth=2,
        ticks='outside',
        tickfont=dict(
            family='Arial',
            size=12,
            color='rgb(82, 82, 82)',
        ),
    ),
    yaxis=dict(
        showgrid=False,
        zeroline=False,
        showline=True,
        showticklabels=True,
    ),
    autosize=True,
    margin=dict(
        l=40,
        r=10,
        t=0,
        b=10
    ),
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    plot_bgcolor='white'
)

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Row(
    [
        dbc.Row(
            [
                dbc.Col([
                    html.Div(
                        [
                            html.Img(src=f"assets/{icon}",width=34,height=34),
                            html.H3(f'{activity["start"].strftime("%d %B %Y")} {activity["name"]} @ {activity["start"].strftime("%H:%M")}',style={"display": "inline"})
                        ],
                    style={'margin-left': 10,"display": "flex"},
                    ),
                    dash_table.DataTable(summary,style_cell={'text-align': 'center','border': 'none'},style_header={'fontSize': 20, 'backgroundColor':'rgb(255,255,255)','fontWeigth':'bold','vertical-align': 'bottom'},style_data={'fontSize':10,'vertical-align': 'top'}),
                    dash_table.DataTable(data=aggregates,columns=aggregates_columns,merge_duplicate_headers=True,style_cell={'text-align': 'center'},fixed_rows={'headers': True},page_action='none', style_table={'height': '320px', 'overflowY': 'auto'}, style_as_list_view=True)
                ],
                style={'margin-top': 10,'margin-left': 10}
                ),
                dbc.Col([
                    dcc.Graph(id="mymap", figure=fig, config={'displayModeBar': False})
                ],
                # style={'width': "25%"},
                ),
            ],
            
        ),
        dbc.Row(
            [
                dcc.Graph(id="time-series",figure=fig2,config={'displayModeBar': False}),
            ],
            style={'height': "25%"},
        ),
    ]
)
print("app running")


if __name__ == "__main__":
    # app.run_server(debug=True)
    # visit http://127.0.0.1:8050/ in your web browser.

    serve(server,host="localhost",port=8080)
    