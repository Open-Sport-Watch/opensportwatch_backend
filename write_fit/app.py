import datetime
from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.sport_message import SportMessage
from fit_tool.profile.messages.event_message import EventMessage
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.lap_message import LapMessage
from fit_tool.profile.messages.record_message import RecordMessage
import fitparse


def extract_data_message_from_key(key, data_message_list, filt="all"):
    return_value = list(
        filter(lambda mess: mess.def_mesg.name == key, data_message_list)
    )
    if filt == "first":
        return_value = return_value[0]

    return return_value


def extract_subfield_from_key(key, data_message_list, value=None):
    return_value = list(
        filter(lambda mess: mess.field_def.name == key, data_message_list)
    )[0]
    if value == "raw_value":
        return_value = return_value.raw_value
    elif value == "value":
        return_value = return_value.value
    elif value == "timestamp":
        return_value = round(
            return_value.value.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000
        )
    elif value == "gps":
        return_value = (
            return_value.raw_value * (180 / 2**31)
            if return_value.raw_value is not None
            else None
        )
    return return_value


def main(path_fit_files):

    previous_activity_distance = 0

    # Set auto_define to true, so that the builder creates the required Definition Messages for us.
    builder = FitFileBuilder(auto_define=True, min_string_size=50)

    for xx, path in enumerate(path_fit_files):

        import_messages = fitparse.FitFile(path).messages

        if xx == 0:
            file_id = extract_data_message_from_key("file_id", import_messages, "first")
            message = FileIdMessage()
            message.type = extract_subfield_from_key(
                "type", file_id.fields, "raw_value"
            )
            message.manufacturer = extract_subfield_from_key(
                "manufacturer", file_id.fields, "raw_value"
            )
            message.product = extract_subfield_from_key(
                "product", file_id.fields, "raw_value"
            )
            message.time_created = extract_subfield_from_key(
                "time_created", file_id.fields, "timestamp"
            )
            message.serial_number = extract_subfield_from_key(
                "serial_number", file_id.fields, "raw_value"
            )
            builder.add(message)

            # Every FIT course file MUST contain a Activity message
            sport = extract_data_message_from_key("sport", import_messages, "first")
            message = SportMessage()
            message.sport_name = extract_subfield_from_key(
                "name", sport.fields, "raw_value"
            )
            message.sport = extract_subfield_from_key(
                "sport", sport.fields, "raw_value"
            )
            message.sub_sport = extract_subfield_from_key(
                "sub_sport", sport.fields, "raw_value"
            )
            builder.add(message)

        events = extract_data_message_from_key("event", import_messages)
        activities_events = []
        for event in events:
            message = EventMessage()
            message.event = extract_subfield_from_key(
                "event", event.fields, "raw_value"
            )
            message.event_type = extract_subfield_from_key(
                "event_type", event.fields, "raw_value"
            )
            message.timestamp = extract_subfield_from_key(
                "timestamp", event.fields, "timestamp"
            )
            activities_events.append(message)
        builder.add_all(activities_events)

        records = extract_data_message_from_key("record", import_messages)
        activities_records = []  # track points
        for record in records:
            message = RecordMessage()
            message.position_lat = extract_subfield_from_key(
                "position_lat", record.fields, "gps"
            )
            message.position_long = extract_subfield_from_key(
                "position_long", record.fields, "gps"
            )
            distance = extract_subfield_from_key("distance", record.fields, "value")
            message.distance = distance + previous_activity_distance

            message.enhanced_altitude = extract_subfield_from_key(
                "enhanced_altitude", record.fields, "value"
            )
            message.enhanced_speed = extract_subfield_from_key(
                "enhanced_speed", record.fields, "value"
            )
            message.heart_rate = extract_subfield_from_key(
                "heart_rate", record.fields, "raw_value"
            )
            message.power = extract_subfield_from_key(
                "power", record.fields, "raw_value"
            )
            message.timestamp = extract_subfield_from_key(
                "timestamp", record.fields, "timestamp"
            )
            activities_records.append(message)
        previous_activity_distance = message.distance
        builder.add_all(activities_records)

        laps = extract_data_message_from_key("lap", import_messages)
        activities_laps = []
        for lap in laps:
            message = LapMessage()
            message.timestamp = extract_subfield_from_key(
                "timestamp", lap.fields, "timestamp"
            )
            message.start_time = extract_subfield_from_key(
                "start_time", lap.fields, "timestamp"
            )
            message.total_elapsed_time = extract_subfield_from_key(
                "total_elapsed_time", lap.fields, "raw_value"
            )

            message.total_timer_time = extract_subfield_from_key(
                "total_timer_time", lap.fields, "raw_value"
            )
            message.start_position_lat = extract_subfield_from_key(
                "start_position_lat", lap.fields, "gps"
            )
            message.start_position_long = extract_subfield_from_key(
                "start_position_long", lap.fields, "gps"
            )
            message.end_position_lat = extract_subfield_from_key(
                "end_position_lat", lap.fields, "gps"
            )
            message.end_position_long = extract_subfield_from_key(
                "end_position_long", lap.fields, "gps"
            )
            message.total_distance = extract_subfield_from_key(
                "total_distance", lap.fields, "value"
            )
            activities_laps.append(message)
        builder.add_all(activities_laps)

    # Finally build the FIT file object and write it to a file
    fit_file = builder.build()

    out_path = "write_fit/tests/join_activities.fit"
    fit_file.to_file(out_path)
    # csv_path = '../tests/out/old_stage_course.csv'
    # fit_file.to_csv(csv_path)


if __name__ == "__main__":
    fit_files = [
        "plot_fit_activity/resources/Morning_Run_step1.fit",
        "plot_fit_activity/resources/Morning_Run_step2.fit",
    ]
    main(fit_files)
