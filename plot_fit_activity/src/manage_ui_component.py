import plotly.graph_objs as go
from dash import dcc, dash_table, html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Output, Input, Dash, State, exceptions
import dash_leaflet as dl
from plotly.subplots import make_subplots
import math
import numpy as np
import json
from src.manage_fit import retrieve_positions_from_dataframe

main_color='rgb(255,61,65)'
selected_color='rgb(8,102,255)'
selected_color_opacity='rgba(8,102,255,0.4)'
main_text_color='rgb(24, 29, 31)'
font_family='Montserrat,-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif'


def retrieve_map_bounds(fig_map,settings):
    latitude=[]
    longitude=[]
    for child in fig_map:
        if child["type"] == 'Polyline' and child["props"]["id"] != 'all-gps-track':
            temp = list(map(list, zip(*child["props"]["positions"])))
            latitude.extend(temp[0])
            longitude.extend(temp[1])
    
    if len(latitude)>0 and len(longitude)>0:
        min_latitude=min(latitude)
        min_longitude=min(longitude)
        max_latitude=max(latitude)
        max_longitude=max(longitude)
    else:
        min_latitude=settings["min_latitude"]
        min_longitude=settings["min_longitude"]
        max_latitude=settings["max_latitude"]
        max_longitude=settings["max_longitude"]

    return min_latitude,min_longitude,max_latitude,max_longitude

def get_map_component(settings,positions):

    bounds=[ 
        [settings["min_latitude"],settings["min_longitude"]],
        [settings["max_latitude"],settings["max_longitude"]],
    ]

    children = [
        dl.TileLayer(id='map-layer'),
        dl.FullScreenControl(id='screen-control'),
        dl.GestureHandling(id='gesture-control'),
        dl.Polyline(positions=positions,color=main_color,id='all-gps-track')
    ]
    
    fig_map = html.Div(
        dl.Map(
            children=children,
            style={'height': '520px',"margin-top": 10,"margin-left": 10},
            bounds=bounds,
            attributionControl=False,
            id="map"
        ),
        id="map_container"
    )
    return fig_map

def add_to_map(map,id,positions):
    map.append({
        "props":{
            "children":None,
            "id":id,
            "color":selected_color,
            "positions": positions
        },
        "type":"Polyline",
        "namespace":"dash_leaflet"
    })
    return map

def add_to_graph(graph,id,x,y):
    graph["data"].append({
        'x':x, 
        'y':y, 
        'fill':'tozeroy', 
        'fillcolor':selected_color_opacity, 
        'mode':"lines",
        'line':dict(color=selected_color_opacity, width=2),
        'name':id,
        'connectgaps':False,
        'hoverinfo':'skip'
    })
    return graph

def get_graph_component(df):
    customdata=[f"{math.floor(pace)}:{str(round((pace%1)*60)).zfill(2)}/km" for pace in df.pace_smoot]
    fig_timeseries = make_subplots(specs=[[{"secondary_y": True}]])
    fig_timeseries.add_trace(
        go.Scatter(
            x=df.time,
            y=df.altitude,
            fill='tozeroy',
            fillcolor='rgba(224,224,224,0.5)',
            mode="lines",
            line=dict(
                color='rgb(160,160,160)',
                width=2
            ),
            name="altitude",
            customdata=customdata,
            hovertemplate="%{y} %{_xother}",
            connectgaps=False
        )
    )
    fig_timeseries.add_trace(
        go.Scatter(
            x=df.time,
            y=df.pace_smoot,
            mode="lines",
            line=dict(
                color=main_color,
                width=2
            ),
            name="pace",
            customdata=customdata,
            hovertemplate="%{_xother} %{customdata}",
            connectgaps=False
        ),
        secondary_y=True
    )
    
    y2_scale=list(np.arange(math.floor(df.pace_smoot.min()),math.ceil(df.pace_smoot.max()),(df.pace_smoot.max()-df.pace_smoot.min())/6))
    y2_scale_text=[f"{math.floor(y2)}:{str(round((y2%1)*60)).zfill(2)}/km" for y2 in y2_scale]


    fig_timeseries.update_layout(
        font_family=font_family,
        xaxis=dict(
            showline=False,
            zeroline=True,
            showgrid=False,
            showticklabels=False,
            # linecolor='rgb(204, 204, 204)',
            # gridcolor='rgb(204, 204, 204)',
            linewidth=2,
            # ticks='outside'
        ),
        yaxis=dict(
            fixedrange= True,
            showgrid=True,
            zeroline=True,
            showline=True,
            # linecolor='rgb(204, 204, 204)',
            gridcolor='rgb(224,224,224)',
            showticklabels=True,
            # showticksuffix='last',
            tickcolor='rgb(224,224,224)',
            ticksuffix=' m'
        ),
        yaxis2=dict(
            fixedrange= True,
            showspikes=True,
            spikecolor=main_color,
            showgrid=False,
            zeroline=True,
            showline=True,
            # linecolor='rgb(204, 204, 204)',
            gridcolor='rgb(224,224,224)',
            showticklabels=True,
            # showticksuffix='last',
            tickcolor='rgb(224,0,0)',
            # ticksuffix=' /km',
            autorange="reversed",
            tickvals=y2_scale,
            ticktext=y2_scale_text,
        ),
        autosize=True,
        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0
        ),
        hovermode="x unified",
        showlegend=False,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='white'
    )

    graph_component = dcc.Graph(id="time-series",figure=fig_timeseries,config={'displayModeBar': False})

    return graph_component


def get_main_component(icon,activity,summary,aggregates,aggregates_columns,map_component,graph_component):
    main_component = dbc.Row(
        [
            dcc.Store(id='memory'),
            dbc.Row(
                [
                    dbc.Col([
                        html.Div(
                            [
                                html.Img(src=f"assets/{icon}",width=55,height=55,style={"margin-right": 10}),
                                html.Div(
                                    [
                                        html.P(f'{activity["start"].strftime("%d %B %Y @ %H:%M")}',style={'vertical-align': 'bottom',"display": "inline","font-family":font_family,"font-style": "normal",'fontSize': 10}),
                                        html.H3(f'{activity["name"]}',style={'vertical-align': 'top','color':main_text_color,'font-weight':'bold','margin-bottom':0})
                                    ]
                                ),
                            ],
                        style={"display": "flex"},
                        ),
                        dash_table.DataTable(
                            summary,
                            cell_selectable=False,
                            style_cell={'text-align': 'center','border': 'none'},
                            style_header={'fontSize': 20, 'backgroundColor':'rgb(255,255,255)','color':main_text_color,'font-weight':'normal','vertical-align': 'bottom','font-family':font_family},
                            style_data={'fontSize':10,'vertical-align': 'top','font-family':font_family}
                        ),
                        dag.AgGrid(
                            id="intertemps",
                            rowData=aggregates,
                            className="ag-theme-alpine selection compact",
                            columnDefs=aggregates_columns,
                            defaultColDef={"resizable": False, "sortable": False, "filter": False},
                            columnSize="responsiveSizeToFit",
                            dashGridOptions={
                                "rowSelection": "multiple",
                                "rowMultiSelectWithClick": True,
                                "suppressCellFocus": True,
                            },
                            style={"height": 400,"textAlign": 'center'}
                            
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
            dbc.Row([
                    graph_component,
                    html.Div(id="layout_output"),
                ],
                style={'height': "410px",'margin-top': 10,'margin-left': 10},
            ),
        ]
    )

    return main_component

def define_app_callback(app,df,positions_for_km,altitude_for_km,time_for_km,settings):

    @app.callback(
        [
            Output("map", "children", allow_duplicate=True),
            Output('map', 'viewport', allow_duplicate=True),
            Output("time-series", "figure"),
            Output("memory", 'data'),
        ],
        [
            Input("intertemps", "selectedRows"),
            State("map", "children"),
            State("time-series", "figure"),
            State("memory", 'data')
        ],
        prevent_initial_call=True,
    )
    def display_intertemps_on_map(selected_rows,fig_map,fig_timeseries,data):

        selected_list = [f"{s['km']}" for s in selected_rows]
        print(f"You selected the km: {', '.join(selected_list)}" if selected_rows else "No selections")

        selected_kms_old_state = list(map(lambda x: x["props"]["id"], list(filter(lambda x: x["type"]=='Polyline' and x["props"]["id"] != 'all-gps-track', fig_map)) ))
        selected_kms_new_state = selected_list

        intersection=list(set(selected_kms_old_state) & set(selected_kms_new_state))
        add_list= list(set(selected_kms_new_state) - set(intersection))
        remove_list= list(set(selected_kms_old_state) - set(intersection))

        for add in add_list:
            fig_map=add_to_map(fig_map,add,positions_for_km[int(add)-1])
            fig_timeseries=add_to_graph(fig_timeseries,add,time_for_km[int(add)-1],altitude_for_km[int(add)-1])

        
        for remove in remove_list:
            del fig_map[list(map(lambda x: x["props"]["id"], fig_map)).index(remove)]
            del fig_timeseries["data"][list(map(lambda x: x["name"], fig_timeseries["data"])).index(remove)]
        
        min_latitude,min_longitude,max_latitude,max_longitude=retrieve_map_bounds(fig_map,settings)

        fig_map_viewport=dict(bounds=[[min_latitude,min_longitude],[max_latitude,max_longitude]])

        print('callback finish')
        return fig_map, fig_map_viewport, fig_timeseries, data

    @app.callback(
        [
            Output("map", "children"),
            Output('map', 'viewport'),
        ],
        [
            Input("time-series", "relayoutData"),
            State("map", "children"),
        ],
        prevent_initial_call=True,
    )
    def display_selected_on_map(relayout_data,fig_map):
        if "xaxis.range[0]" in relayout_data:
            start_date=relayout_data["xaxis.range[0]"]
            end_date=relayout_data["xaxis.range[1]"]

            df_filt = df[df['time'].dt.strftime('%Y-%m-%d %H:%M:%S.%f').between(start_date, end_date)]
            positions=retrieve_positions_from_dataframe(df_filt.latitude.to_list(),df_filt.longitude.to_list())
            fig_map=add_to_map(fig_map,'manual-range',positions)
            min_latitude,min_longitude,max_latitude,max_longitude=retrieve_map_bounds(fig_map,settings)
            fig_map_viewport=dict(bounds=[[min_latitude,min_longitude],[max_latitude,max_longitude]])
            return fig_map,fig_map_viewport
        elif "xaxis.autorange" in relayout_data and relayout_data['xaxis.autorange']==True and 'manual-range' in list(map(lambda x: x["props"]["id"], fig_map)):
            del fig_map[list(map(lambda x: x["props"]["id"], fig_map)).index('manual-range')]
            min_latitude,min_longitude,max_latitude,max_longitude=retrieve_map_bounds(fig_map,settings)
            fig_map_viewport=dict(bounds=[[min_latitude,min_longitude],[max_latitude,max_longitude]])
            return fig_map,fig_map_viewport
        raise exceptions.PreventUpdate

def init_app(main_component,df,positions_for_km,altitude_for_km,time_for_km,settings):
    app = Dash(external_stylesheets=[dbc.themes.MINTY])
    server = app.server

    app.layout = main_component
    print("App started!")

    define_app_callback(app,df,positions_for_km,altitude_for_km,time_for_km,settings)

    return server