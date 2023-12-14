from waitress import serve
from src.manage_fit import extract_data_from_fit
from src.manage_ui_component import get_map_component, get_graph_component, get_main_component, init_app

# file_name = "plot_fit_activity/resources/Morning_Run_Suunto.fit"
# file_name = "plot_fit_activity/resources/Morning_Run_Garmin.fit"
# file_name = "plot_fit_activity/resources/Morning_Trail_Run.fit"
file_name = "plot_fit_activity/resources/Pesaro-Cattolica.fit"

df, activity, summary, aggregates, aggregates_columns, settings, icon, latitude_for_km, longitude_for_km = extract_data_from_fit(file_name)


map_component = get_map_component(settings,df,latitude_for_km,longitude_for_km)
graph_component = get_graph_component(df)
main_component = get_main_component(icon,activity,summary,aggregates,aggregates_columns,map_component,graph_component)

server = init_app(main_component,latitude_for_km,longitude_for_km)
 

if __name__ == "__main__":
    # app.run_server(debug=True)
    # visit http://127.0.0.1:8050/ in your web browser.

    serve(server,host="localhost",port=8080)
    