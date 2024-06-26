import plotly.graph_objs as go
from dash import dcc, dash_table, html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Output, Input, Dash, State, exceptions
import dash_leaflet as dl
import os
import math
import numpy as np
from src.manage_fit import retrieve_positions_from_dataframe

main_color = "rgb(255,61,65)"
selected_color = "rgb(8,102,255)"
selected_color_opacity = "rgba(8,102,255,0.4)"
main_text_color = "rgb(24, 29, 31)"
font_family = 'Montserrat,-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif'
OWN_APP_ID = os.getenv("OWM_APP_ID", "<<your_open_weather_map_appid>>")
JAWG_APP_ID = os.getenv("JAWG_APP_ID", "<<your_jswg_map_appid>>")

custom_icon = dict(
    iconUrl="assets/blue_dot.png",
    iconSize=[15, 15],
)


def find_indices(list_to_check, item_to_find):
    indices = []
    for idx, value in enumerate(list_to_check):
        if value == item_to_find:
            indices.append(idx)
    return indices


def reset_marker(fig_map):
    if "Marker" in list(map(lambda x: x["type"], fig_map)):
        del fig_map[list(map(lambda x: x["type"], fig_map)).index("Marker")]
    return fig_map


def update_marker_position(fig_map, lat, lon):
    if len(list(filter(lambda x: x["type"] == "Marker", fig_map))) == 0:
        fig_map.append(
            {
                "props": {
                    "children": None,
                    "position": [lat, lon],
                    "icon": custom_icon,
                    "id": "marker-position",
                },
                "type": "Marker",
                "namespace": "dash_leaflet",
            }
        )
    else:
        fig_map[list(map(lambda x: x["type"], fig_map)).index("Marker")]["props"][
            "position"
        ] = [lat, lon]

    return fig_map


def retrieve_map_bounds(fig_map, settings):
    latitude = []
    longitude = []
    for child in fig_map:
        if child["type"] == "Polyline" and child["props"]["id"] != "all-gps-track":
            temp = list(map(list, zip(*child["props"]["positions"])))
            latitude.extend(temp[0])
            longitude.extend(temp[1])

    if len(latitude) > 0 and len(longitude) > 0:
        min_latitude = min(latitude)
        min_longitude = min(longitude)
        max_latitude = max(latitude)
        max_longitude = max(longitude)
    else:
        min_latitude = settings["min_latitude"]
        min_longitude = settings["min_longitude"]
        max_latitude = settings["max_latitude"]
        max_longitude = settings["max_longitude"]

    return min_latitude, min_longitude, max_latitude, max_longitude


def get_map_component(settings, positions):

    bounds = [
        [settings["min_latitude"], settings["min_longitude"]],
        [settings["max_latitude"], settings["max_longitude"]],
    ]

    layers = dl.LayersControl(
        [
            dl.BaseLayer(
                dl.TileLayer(
                    id="map-layer",
                    url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                    maxZoom=19,
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                ),
                name="map",
                checked=True,
            ),
            dl.BaseLayer(
                dl.TileLayer(
                    id="satellite-layer",
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                    attribution='&copy; <a href="https://doc.arcgis.com/it/arcgis-online/reference/tile-layers.htm">ArcGIS</a>',
                ),
                name="satellite",
                checked=False,
            ),
            dl.BaseLayer(
                dl.TileLayer(
                    id="terrain-layer",
                    url=f"https://{{s}}.tile.jawg.io/jawg-terrain/{{z}}/{{x}}/{{y}}{{r}}.png?access-token={JAWG_APP_ID}",
                    attribution='&copy; <a href="https://www.jawg.io/en/">Jawg</a>',
                ),
                name="terrain",
                checked=False,
            ),
            dl.Overlay(
                dl.TileLayer(
                    id="snow-layer",
                    url="https://tiles.opensnowmap.org/pistes/{z}/{x}/{y}.png",
                    attribution='&copy; <a href="https://www.opensnowmap.org/">OpenSnow</a>',
                ),
                name="ski slopes",
                checked=False,
            ),
            dl.Overlay(
                dl.TileLayer(
                    id="wind-layer",
                    url=f"https://tile.openweathermap.org/map/wind_new/{{z}}/{{x}}/{{y}}.png?appid={OWN_APP_ID}",
                    # opacity= 0.5,
                    attribution='&copy; <a href="https://openweathermap.org">OpenWeather</a>',
                ),
                name="wind",
                checked=False,
            ),
            dl.Overlay(
                dl.TileLayer(
                    id="precipitation-layer",
                    url=f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWN_APP_ID}",
                    # opacity= 0.5,
                    attribution='&copy; <a href="https://openweathermap.org">OpenWeather</a>',
                ),
                name="precipitation",
                checked=False,
            ),
            dl.Overlay(
                dl.TileLayer(
                    id="sea-layer",
                    url="https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
                    # opacity= 0.5,
                    attribution='&copy; <a href="http://www.openseamap.org">OpenSea</a>',
                ),
                name="sea",
                checked=False,
            ),
            dl.Overlay(
                dl.TileLayer(
                    id="bathymetry-layer",
                    url="https://tiles.emodnet-bathymetry.eu/latest/mean_rainbowcolour/web_mercator/{z}/{x}/{y}.png",
                    opacity=0.5,
                    attribution='&copy; <a href="https://emodnet.ec.europa.eu/en/emodnet-web-service-documentation">Emodnet</a>',
                ),
                name="bathymetry",
                checked=False,
            ),
        ],
        id="lc",
    )

    children = [
        layers,
        dl.LocateControl(id="locate", locateOptions={"enableHighAccuracy": True}),
        dl.FullScreenControl(id="screen-control"),
        dl.GestureHandling(id="gesture-control"),
        dl.Polyline(positions=positions, color=main_color, id="all-gps-track"),
    ]

    fig_map = html.Div(
        dl.Map(
            children=children,
            style={"height": "520px", "margin-top": 10, "margin-left": 10},
            bounds=bounds,
            attributionControl=True,
            id="map",
        ),
        id="map_container",
    )
    return fig_map


def add_to_map(map, id, positions):
    map.append(
        {
            "props": {
                "children": None,
                "id": id,
                "color": selected_color,
                "positions": positions,
            },
            "type": "Polyline",
            "namespace": "dash_leaflet",
        }
    )
    return map


def add_to_graph(graph, id, x, y):
    graph["data"].append(
        {
            "x": x,
            "y": y,
            "fill": "tozeroy",
            "fillcolor": selected_color_opacity,
            "mode": "lines",
            "line": dict(color=selected_color_opacity, width=2),
            "name": id,
            "connectgaps": False,
            "hoverinfo": "skip",
        }
    )
    return graph


def get_graph_component(df):
    customdata = [
        f"{math.floor(pace)}:{str(round((pace%1)*60)).zfill(2)}/km"
        for pace in df.pace_smoot
    ]
    fig_timeseries = go.Figure()
    fig_timeseries.add_trace(
        go.Scatter(
            x=df.time,
            y=df.altitude,
            fill="tozeroy",
            fillcolor="rgba(224,224,224,0.5)",
            mode="lines",
            line=dict(color="rgb(160,160,160)", width=2),
            name="altitude",
            customdata=customdata,
            hovertemplate="%{y} %{_xother} %{_xother} %{_xother}",
            connectgaps=False,
        )
    )
    fig_timeseries.add_trace(
        go.Scatter(
            x=df.time,
            y=df.pace_smoot,
            mode="lines",
            line=dict(color="blue", width=1),
            name="pace",
            customdata=customdata,
            hovertemplate="%{_xother} %{customdata} %{_xother} %{_xother}",
            visible=True,
            yaxis="y2",
        )
    )
    fig_timeseries.add_trace(
        go.Scatter(
            x=df.time,
            y=df.power,
            mode="lines",
            line=dict(color="violet", width=1),
            name="power",
            hovertemplate="%{_xother} %{_xother} %{y} %{_xother}",
            visible=False,
            yaxis="y3",
        )
    )
    fig_timeseries.add_trace(
        go.Scatter(
            x=df.time,
            y=df.heartrate,
            mode="lines",
            line=dict(color="red", width=1),
            name="heartrate",
            hovertemplate="%{_xother} %{_xother} %{_xother} %{y}",
            visible=False,
            yaxis="y4",
        )
    )

    y2_scale = list(
        np.arange(
            math.floor(df.pace_smoot.min()),
            math.ceil(df.pace_smoot.max()),
            (df.pace_smoot.max() - df.pace_smoot.min()) / 6,
        )
    )
    y2_scale_text = [
        f"{math.floor(y2)}:{str(round((y2%1)*60)).zfill(2)}/km" for y2 in y2_scale
    ]

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
            fixedrange=True,
            showgrid=True,
            zeroline=True,
            showline=True,
            # linecolor='rgb(204, 204, 204)',
            gridcolor="rgb(224,224,224)",
            showticklabels=True,
            # showticksuffix='last',
            tickcolor="rgb(224,224,224)",
            ticksuffix=" m",
        ),
        yaxis2=dict(
            fixedrange=True,
            showspikes=True,
            spikecolor="blue",
            showgrid=False,
            zeroline=True,
            showline=True,
            # linecolor='rgb(204, 204, 204)',
            showticklabels=True,
            # showticksuffix='last',
            tickcolor="blue",
            autorange="reversed",
            tickvals=y2_scale,
            ticktext=y2_scale_text,
            tickfont=dict(color="blue"),
            anchor="free",
            overlaying="y",
            side="right",
            autoshift=True,
        ),
        yaxis3=dict(
            fixedrange=True,
            showspikes=True,
            spikecolor="violet",
            showgrid=False,
            zeroline=True,
            showline=True,
            # linecolor='rgb(204, 204, 204)',
            showticklabels=False,
            # showticksuffix='last',
            tickcolor="violet",
            ticksuffix=" W",
            tickfont=dict(color="violet"),
            anchor="free",
            overlaying="y",
            side="right",
            autoshift=True,
        ),
        yaxis4=dict(
            fixedrange=True,
            showspikes=True,
            spikecolor="red",
            showgrid=False,
            zeroline=True,
            showline=True,
            # linecolor='rgb(204, 204, 204)',
            showticklabels=False,
            # showticksuffix='last',
            tickcolor="red",
            ticksuffix=" bpm",
            tickfont=dict(color="red"),
            anchor="free",
            overlaying="y",
            side="right",
            autoshift=True,
        ),
        autosize=True,
        margin=dict(l=0, r=0, t=0, b=0),
        hovermode="x unified",
        showlegend=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
    )

    graph_component = dcc.Graph(
        id="time-series",
        figure=fig_timeseries,
        config={"displayModeBar": False},
        clear_on_unhover=True,
    )

    return graph_component


def get_graph_selector():
    checklist_item = dcc.Checklist(
        id="checklist",
        options=[
            {
                "label": html.Div(
                    "pace",
                    style={
                        "display": "inline",
                        "padding-left": "0.5rem",
                        "color": "blue",
                        "font-size": 20,
                    },
                ),
                "value": "pace",
            },
            {
                "label": html.Div(
                    "heartrate",
                    style={
                        "display": "inline",
                        "padding-left": "0.5rem",
                        "color": "red",
                        "font-size": 20,
                    },
                ),
                "value": "heartrate",
            },
            {
                "label": html.Div(
                    "power",
                    style={
                        "display": "inline",
                        "padding-left": "0.5rem",
                        "color": "violet",
                        "font-size": 20,
                    },
                ),
                "value": "power",
            },
        ],
        value=["pace"],
        labelStyle={"margin": "1rem"},
        style={
            "display": "flex",
            "justify-content": "center",
            "font-family": font_family,
        },
    )
    return checklist_item


def get_main_component(
    icon,
    activity,
    summary,
    aggregates,
    aggregates_columns,
    map_component,
    graph_component,
    radio_item,
):
    main_component = dbc.Container(
        [
            dbc.Row(
                [
                    dcc.Store(id="memory"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Img(
                                                src=f"assets/{icon}",
                                                width=55,
                                                height=55,
                                                style={"margin-right": 10},
                                            ),
                                            html.Div(
                                                [
                                                    html.P(
                                                        f'{activity["start"].strftime("%d %B %Y @ %H:%M")}',
                                                        style={
                                                            "vertical-align": "bottom",
                                                            "display": "inline",
                                                            "font-family": font_family,
                                                            "font-style": "normal",
                                                            "fontSize": 10,
                                                        },
                                                    ),
                                                    html.H3(
                                                        f'{activity["name"]}',
                                                        style={
                                                            "vertical-align": "top",
                                                            "color": main_text_color,
                                                            "font-weight": "bold",
                                                            "margin-bottom": 0,
                                                        },
                                                    ),
                                                ]
                                            ),
                                        ],
                                        style={"display": "flex"},
                                    ),
                                    dash_table.DataTable(
                                        summary,
                                        cell_selectable=False,
                                        style_cell={
                                            "text-align": "center",
                                            "border": "none",
                                        },
                                        style_header={
                                            "fontSize": 20,
                                            "backgroundColor": "rgb(255,255,255)",
                                            "color": main_text_color,
                                            "font-weight": "normal",
                                            "vertical-align": "bottom",
                                            "font-family": font_family,
                                        },
                                        style_data={
                                            "fontSize": 10,
                                            "vertical-align": "top",
                                            "font-family": font_family,
                                        },
                                    ),
                                    dag.AgGrid(
                                        id="intertemps",
                                        rowData=aggregates,
                                        className="ag-theme-alpine selection compact",
                                        columnDefs=aggregates_columns,
                                        defaultColDef={
                                            "resizable": False,
                                            "sortable": False,
                                            "filter": False,
                                        },
                                        columnSize="responsiveSizeToFit",
                                        dashGridOptions={
                                            "rowSelection": "multiple",
                                            "rowMultiSelectWithClick": True,
                                            "suppressCellFocus": True,
                                        },
                                        style={"height": 400, "textAlign": "center"},
                                    ),
                                ],
                                style={"margin-top": 10, "margin-left": 10},
                                # md=12,lg=12,xl=12,xxl='auto'
                            ),
                            dbc.Col(
                                [map_component],
                                style={"margin-top": 0, "margin-left": 0},
                                # md=12,lg=12,xl=12,xxl=8
                            ),
                        ],
                    ),
                    dbc.Row(
                        [graph_component, radio_item],
                        style={"height": "420px", "margin-top": 10, "margin-left": 10},
                    ),
                ]
            )
        ]
    )

    return main_component


def define_app_callback(
    app, df, positions_for_km, altitude_for_km, time_for_km, settings
):

    @app.callback(
        [
            Output("map", "children", allow_duplicate=True),
            Output("map", "viewport", allow_duplicate=True),
            Output("time-series", "figure", allow_duplicate=True),
            Output("memory", "data"),
        ],
        [
            Input("intertemps", "selectedRows"),
            State("map", "children"),
            State("time-series", "figure"),
            State("memory", "data"),
        ],
        prevent_initial_call=True,
    )
    def display_intertemps_on_map(selected_rows, fig_map, fig_timeseries, data):

        selected_list = [f"{s['km']}" for s in selected_rows]
        print(
            f"You selected the km: {', '.join(selected_list)}"
            if selected_rows
            else "No selections"
        )

        selected_kms_old_state = list(
            map(
                lambda x: x["props"]["id"],
                list(
                    filter(
                        lambda x: x["type"] == "Polyline"
                        and x["props"]["id"] != "all-gps-track",
                        fig_map,
                    )
                ),
            )
        )
        selected_kms_new_state = selected_list

        intersection = list(set(selected_kms_old_state) & set(selected_kms_new_state))
        add_list = list(set(selected_kms_new_state) - set(intersection))
        remove_list = list(set(selected_kms_old_state) - set(intersection))

        for add in add_list:
            fig_map = add_to_map(fig_map, add, positions_for_km[int(add) - 1])
            fig_timeseries = add_to_graph(
                fig_timeseries,
                add,
                time_for_km[int(add) - 1],
                altitude_for_km[int(add) - 1],
            )

        for remove in remove_list:
            del fig_map[list(map(lambda x: x["props"]["id"], fig_map)).index(remove)]
            del fig_timeseries["data"][
                list(map(lambda x: x["name"], fig_timeseries["data"])).index(remove)
            ]

        min_latitude, min_longitude, max_latitude, max_longitude = retrieve_map_bounds(
            fig_map, settings
        )

        fig_map_viewport = dict(
            bounds=[[min_latitude, min_longitude], [max_latitude, max_longitude]]
        )

        return fig_map, fig_map_viewport, fig_timeseries, data

    @app.callback(
        [
            Output("map", "children", allow_duplicate=True),
            Output("map", "viewport"),
        ],
        [
            Input("time-series", "relayoutData"),
            State("map", "children"),
        ],
        prevent_initial_call=True,
    )
    def display_selected_on_map(relayout_data, fig_map):
        if "xaxis.range[0]" in relayout_data:
            if "manual-range" in list(map(lambda x: x["props"]["id"], fig_map)):
                del fig_map[
                    list(map(lambda x: x["props"]["id"], fig_map)).index("manual-range")
                ]
            start_date = relayout_data["xaxis.range[0]"]
            end_date = relayout_data["xaxis.range[1]"]

            df_filt = df[
                df["time"]
                .dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                .between(start_date, end_date)
            ]
            positions = retrieve_positions_from_dataframe(
                df_filt.latitude.to_list(), df_filt.longitude.to_list()
            )
            fig_map = add_to_map(fig_map, "manual-range", positions)
            min_latitude, min_longitude, max_latitude, max_longitude = (
                retrieve_map_bounds(fig_map, settings)
            )
            fig_map_viewport = dict(
                bounds=[[min_latitude, min_longitude], [max_latitude, max_longitude]]
            )
            return fig_map, fig_map_viewport
        elif (
            "xaxis.autorange" in relayout_data
            and relayout_data["xaxis.autorange"]
            and "manual-range" in list(map(lambda x: x["props"]["id"], fig_map))
        ):
            del fig_map[
                list(map(lambda x: x["props"]["id"], fig_map)).index("manual-range")
            ]
            min_latitude, min_longitude, max_latitude, max_longitude = (
                retrieve_map_bounds(fig_map, settings)
            )
            fig_map_viewport = dict(
                bounds=[[min_latitude, min_longitude], [max_latitude, max_longitude]]
            )
            return fig_map, fig_map_viewport
        raise exceptions.PreventUpdate

    @app.callback(
        Output("map", "children"),
        [
            Input("time-series", "hoverData"),
            State("map", "children"),
        ],
        prevent_initial_call=True,
    )
    def display_position_on_map(hoverData, fig_map):
        if hoverData is None:
            return reset_marker(fig_map)

        lat = df.latitude[hoverData["points"][0]["pointIndex"]]
        lon = df.longitude[hoverData["points"][0]["pointIndex"]]
        return update_marker_position(fig_map, lat, lon)

    @app.callback(
        Output("time-series", "figure"),
        [
            Input("checklist", "value"),
            State("time-series", "figure"),
        ],
        prevent_initial_call=True,
    )
    def change_graph_plot(checklist_state, fig_timeseries):
        for line in fig_timeseries["data"]:
            if (
                "visible" in line
                and line["visible"]
                and not line["name"] in checklist_state
            ):
                line["visible"] = False
                fig_timeseries["layout"][f"yaxis{line['yaxis'].split('y')[1]}"][
                    "showticklabels"
                ] = False
            elif (
                "visible" in line
                and not line["visible"]
                and line["name"] in checklist_state
            ):
                line["visible"] = True
                fig_timeseries["layout"][f"yaxis{line['yaxis'].split('y')[1]}"][
                    "showticklabels"
                ] = True
        return fig_timeseries


def init_app(
    main_component, df, positions_for_km, altitude_for_km, time_for_km, settings
):
    app = Dash(external_stylesheets=[dbc.themes.MINTY])
    server = app.server

    app.layout = main_component
    print("App started!")

    define_app_callback(
        app, df, positions_for_km, altitude_for_km, time_for_km, settings
    )

    return server
