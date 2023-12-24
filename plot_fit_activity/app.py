from waitress import serve
from src.manage_fit import extract_data_from_fit
from src.manage_ui_component import get_map_component, get_graph_component, get_main_component, get_graph_selector, init_app

# file_name = "plot_fit_activity/resources/Morning_Run_Suunto.fit"
# file_name = "plot_fit_activity/resources/Morning_Run_Garmin.fit"
# file_name = "plot_fit_activity/resources/Morning_Trail_Run.fit"
# file_name = "plot_fit_activity/resources/Pesaro-Cattolica.fit"
file_name = "plot_fit_activity/resources/Prenatalizia.fit"

df, positions, positions_for_km, altitude_for_km, time_for_km, activity, summary, aggregates, aggregates_columns, settings, icon = extract_data_from_fit(file_name)


map_component = get_map_component(settings,positions)
graph_component = get_graph_component(df)
radio_item = get_graph_selector()
main_component = get_main_component(icon,activity,summary,aggregates,aggregates_columns,map_component,graph_component,radio_item)

server = init_app(main_component, df, positions_for_km, altitude_for_km, time_for_km, settings)
 

if __name__ == "__main__":
    # app.run_server(debug=True)
    # visit http://127.0.0.1:8050/ in your web browser.

    serve(server,host="0.0.0.0",port=8080,_quiet=True)
    