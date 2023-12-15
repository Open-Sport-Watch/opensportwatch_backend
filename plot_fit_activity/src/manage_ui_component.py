import plotly.graph_objs as go
from dash import dcc, dash_table, html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Output, Input, Dash
import dash_leaflet as dl

fig_map = None

def get_map_component(settings,positions):
    global fig_map

    bounds=[ 
        [settings["min_latitude"],settings["min_longitude"]],
        [settings["max_latitude"],settings["max_longitude"]],
    ]

    children = [
        dl.TileLayer(id='map-layer'),
        dl.FullScreenControl(id='screen-control'),
        dl.Polyline(positions=positions,color='rgb(255,61,65)',id='all-gps-track')
    ]
    
    fig_map = html.Div(
        dl.Map(
            children=children,
            style={'height': '525px',"margin-top": 10,"margin-left": 10},
            bounds=bounds,
            attributionControl=False,
            id="map"
        ),
        id="map_container"
    )
    return fig_map

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

def define_app_callback(app,positions_for_km,settings):

    @app.callback(
        Output("map_container", "children"),
        [
            Input("intertemps", "selectedRows"),
        ],
        prevent_initial_call=True,
    )
    def display_intertemps_on_map(selected_rows):
        global fig_map

        selected_list = [f"{s['km']}" for s in selected_rows]
        print(f"You selected the km: {', '.join(selected_list)}" if selected_rows else "No selections")

        selected_kms_old_state = list(map(lambda x: x.id, fig_map.children.children))
        selected_kms_old_state.pop(selected_kms_old_state.index('map-layer'))
        selected_kms_old_state.pop(selected_kms_old_state.index('screen-control'))
        selected_kms_old_state.pop(selected_kms_old_state.index('all-gps-track'))
        selected_kms_new_state = selected_list

        intersection=list(set(selected_kms_old_state) & set(selected_kms_new_state))
        add_list= list(set(selected_kms_new_state) - set(intersection))
        remove_list= list(set(selected_kms_old_state) - set(intersection))

        for add in add_list:
            fig_map.children.children.append(dl.Polyline(positions=positions_for_km[int(add)-1],id=add,color='blue'))

        for remove in remove_list:
            del fig_map.children.children[list(map(lambda x: x.id, fig_map.children.children)).index(remove)]
        
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

        return fig_map


def init_app(main_component,positions_for_km,settings):
    app = Dash(external_stylesheets=[dbc.themes.MINTY])
    server = app.server

    app.layout = main_component
    print("App started!")

    define_app_callback(app,positions_for_km,settings)

    return server