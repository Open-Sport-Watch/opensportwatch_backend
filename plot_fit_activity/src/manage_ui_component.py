import plotly.graph_objs as go
from dash import dcc, dash_table, html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Output, Input, Dash

fig_map = None

def create_figure_map(settings,df,latitude_for_km,longitude_for_km,add_list=[],remove_list=[]):
    global fig_map

    if not df is None:
        fig_map = go.Figure(
            go.Scattermapbox(
                mode = "lines",
                lon = df.longitude,
                lat = df.latitude,
                marker = {'size': 10},
                text = "all",
                line = {'width': 3},
                marker_color='red',
                hoverinfo='none'
            )
        )

        fig_map.update_layout(
            mapbox={
                'style': "open-street-map",
            },
            margin={"r":0,"t":10,"l":10,"b":0},
            showlegend=False,
        )

    for add in add_list: 
        fig_map.add_scattermapbox(
            lat=latitude_for_km[int(add)-1],
            lon=longitude_for_km[int(add)-1],
            mode='lines',
            text=add,
            marker = {'size': 10},
            line = {'width': 4},
            # marker_color='rgb(235, 0, 100)'
            marker_color='blue',
            hoverinfo='none'
        )
    for remove in remove_list:
        index_to_remove = list(map(lambda x: x["text"], fig_map.data)).index(remove)
        new_data = list(fig_map.data)
        new_data.pop(index_to_remove)
        fig_map.data=new_data

    fig_map.update_layout(
        mapbox={
            'bounds' : {
                'east' : settings["max_longitude"],
                'west' : settings["min_longitude"],
                'south' : settings["min_latitude"],
                'north' : settings["max_latitude"]
            }
        }
    )

    return fig_map

def get_map_component(settings,df,latitude_for_km,longitude_for_km):
    map_component=dcc.Graph(id="mymap", figure=create_figure_map(settings,df,latitude_for_km,longitude_for_km), config={'displayModeBar': False},style={'height': 535})

    return map_component

def get_graph_component(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.time, y=df.heartrate, mode="lines",line=dict(color='rgb(220,20,60)', width=2), name="heartrate", connectgaps=True,))
    fig.add_trace(go.Scatter(x=df.time, y=df.power, mode="lines",line=dict(color='rgb(34,139,34)', width=2), name="power", connectgaps=True,))
    fig.add_trace(go.Scatter(x=df.time, y=df.altitude, mode="lines",line=dict(color='rgb(49,130,189)', width=2), name="altitude", connectgaps=True,))

    fig.update_layout(
        xaxis=dict(
            showline=True,
            showgrid=False,
            showticklabels=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=2,
            ticks='outside'
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

    graph_component = dcc.Graph(id="time-series",figure=fig,config={'displayModeBar': False})

    return graph_component


def get_main_component(icon,activity,summary,aggregates,aggregates_columns,map_component,graph_component):
    main_component = dbc.Row(
        [
            dbc.Row(
                [
                    dbc.Col([
                        html.Div(
                            [
                                html.Img(src=f"assets/{icon}",width=55,height=55,style={"margin-right": 10}),
                                html.Div(
                                    [
                                        html.P(f'{activity["start"].strftime("%d %B %Y @ %H:%M")}',style={'vertical-align': 'bottom',"display": "inline","font-style": "italic",'fontSize': 15}),
                                        html.H3(f'{activity["name"]}',style={'vertical-align': 'top'})
                                    ]
                                ),
                            ],
                        style={"display": "flex"},
                        ),
                        dash_table.DataTable(
                            summary,
                            cell_selectable=False,
                            style_cell={'text-align': 'center','border': 'none'},
                            style_header={'fontSize': 20, 'backgroundColor':'rgb(255,255,255)','fontWeigth':'bold','vertical-align': 'bottom'},
                            style_data={'fontSize':10,'vertical-align': 'top'}
                        ),
                        dag.AgGrid(
                            id="intertemps",
                            rowData=aggregates,
                            columnDefs=aggregates_columns,
                            defaultColDef={"resizable": False, "sortable": False, "filter": False},
                            columnSize="responsiveSizeToFit",
                            dashGridOptions={
                                "rowSelection": "multiple",
                                "rowMultiSelectWithClick": True,
                                "suppressCellFocus": True,
                            },
                            style={"height": 400}
                            
                        )
                    ],
                    style={'margin-top': 10,'margin-left': 10},
                    # md=12,lg=12,xl=12,xxl='auto'
                    ),
                    dbc.Col(
                        [map_component],
                        style={'margin-top': 0,'margin-left': 0},
                        # md=12,lg=12,xl=12,xxl=8
                    ),
                ],
                
            ),
            dbc.Row([graph_component],
                style={'height': "25%",'margin-top': 10},
            ),
        ]
    )

    return main_component

def define_app_callback(app,latitude_for_km, longitude_for_km):
    
    @app.callback(
        Output("mymap", "figure"),
        [
            Input("intertemps", "selectedRows"),
        ],
        prevent_initial_call=True,
    )
    def display_intertemps_on_map(selected_rows):
        global fig_map

        selected_list = [f"{s['km']}" for s in selected_rows]
        print(f"You selected the km: {', '.join(selected_list)}" if selected_rows else "No selections")

        selected_kms_old_state = list(map(lambda x: x["text"], fig_map.data))
        selected_kms_old_state.pop(selected_kms_old_state.index('all'))
        selected_kms_new_state = selected_list

        intersection=list(set(selected_kms_old_state) & set(selected_kms_new_state))
        add_list= list(set(selected_kms_new_state) - set(intersection))
        remove_list= list(set(selected_kms_old_state) - set(intersection))

        # no funziona :(
        settings = {
            "max_longitude":360,
            "min_longitude":0,
            "max_latitude":360,
            "min_latitude":0,
        }

        return create_figure_map(settings,None,latitude_for_km,longitude_for_km,add_list,remove_list)


def init_app(main_component,latitude_for_km,longitude_for_km):
    app = Dash(external_stylesheets=[dbc.themes.MINTY])
    server = app.server

    app.layout = main_component
    print("App started!")

    define_app_callback(app,latitude_for_km,longitude_for_km)

    return server