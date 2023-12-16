import plotly.graph_objs as go
from dash import dcc, dash_table, html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Output, Input, Dash
import dash_leaflet as dl
from plotly.subplots import make_subplots
import math
import numpy as np

fig_map = None
fig_timeseries= None

main_color='rgb(255,61,65)'
selected_color='rgb(8,102,255)'
selected_color_opacity='rgba(8,102,255,0.4)'
main_text_color='rgb(24, 29, 31)'
font_family='Montserrat,-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif'

def get_map_component(settings,positions):
    global fig_map

    bounds=[ 
        [settings["min_latitude"],settings["min_longitude"]],
        [settings["max_latitude"],settings["max_longitude"]],
    ]

    children = [
        dl.TileLayer(id='map-layer'),
        dl.FullScreenControl(id='screen-control'),
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

def get_graph_component(df):
    global fig_timeseries
    fig_timeseries = make_subplots(specs=[[{"secondary_y": True}]])
    fig_timeseries.add_trace(go.Scatter(x=df.time, y=df.altitude, fill='tozeroy', fillcolor='rgba(224,224,224,0.5)', mode="lines",line=dict(color='rgb(160,160,160)', width=2), name="altitude", connectgaps=False))
    fig_timeseries.add_trace(go.Scatter(x=df.time, y=df.pace_smoot, mode="lines",line=dict(color=main_color, width=2), name="pace", connectgaps=False),secondary_y=True)
    
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
            dbc.Row([graph_component],
                style={'height': "410px",'margin-top': 10,'margin-left': 10},
            ),
        ]
    )

    return main_component

def define_app_callback(app,positions_for_km,altitude_for_km,time_for_km,settings):

    @app.callback(
        [
            Output("map_container", "children"),
            Output("time-series", "figure"),
        ],
        [
            Input("intertemps", "selectedRows"),
        ],
        prevent_initial_call=True,
    )
    def display_intertemps_on_map(selected_rows):
        global fig_map, fig_timeseries

        selected_list = [f"{s['km']}" for s in selected_rows]
        print(f"You selected the km: {', '.join(selected_list)}" if selected_rows else "No selections")

        selected_kms_old_state = list(map(lambda x: x.id, list(filter(lambda x: x._type=='Polyline' and x.id != 'all-gps-track', fig_map.children.children)) ))
        selected_kms_new_state = selected_list

        intersection=list(set(selected_kms_old_state) & set(selected_kms_new_state))
        add_list= list(set(selected_kms_new_state) - set(intersection))
        remove_list= list(set(selected_kms_old_state) - set(intersection))

        for add in add_list:
            fig_map.children.children.append(dl.Polyline(positions=positions_for_km[int(add)-1],id=add,color=selected_color))
            fig_timeseries.add_trace(go.Scatter(x=time_for_km[int(add)-1], y=altitude_for_km[int(add)-1], fill='tozeroy', fillcolor=selected_color_opacity, mode="lines",line=dict(color=selected_color_opacity, width=2), name=add, connectgaps=False))

        for remove in remove_list:
            del fig_map.children.children[list(map(lambda x: x.id, fig_map.children.children)).index(remove)]
            new_data=list(fig_timeseries.data)
            del new_data[list(map(lambda x: x.name, new_data)).index(remove)]
            fig_timeseries.data=new_data
        
        if selected_rows:
            min_latitude=360
            min_longitude=360
            max_latitude=0
            max_longitude=0
        else:
            min_latitude=settings["min_latitude"]
            min_longitude=settings["min_longitude"]
            max_latitude=settings["max_latitude"]
            max_longitude=settings["max_longitude"]
        

        for child in fig_map.children.children:
            if child._type == 'Polyline' and child.id != 'all-gps-track':
                for p in child.positions:
                    if p[0]<min_latitude:
                        min_latitude=p[0]
                    if p[0]>max_latitude:
                        max_latitude=p[0]
                    if p[1]<min_longitude:
                        min_longitude=p[1]
                    if p[1]>max_longitude:
                        max_longitude=p[1]

        fig_map.children.bounds=[ 
            [min_latitude,min_longitude],
            [max_latitude,max_longitude],
        ]

        return fig_map, fig_timeseries


def init_app(main_component,positions_for_km,altitude_for_km,time_for_km,settings):
    app = Dash(external_stylesheets=[dbc.themes.MINTY])
    server = app.server

    app.layout = main_component
    print("App started!")

    define_app_callback(app,positions_for_km,altitude_for_km,time_for_km,settings)

    return server