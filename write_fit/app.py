import datetime

from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.activity_message import ActivityMessage
from fit_tool.profile.messages.event_message import EventMessage
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.lap_message import LapMessage
from fit_tool.profile.messages.record_message import RecordMessage

import fitparse


def main():
    fitfile = fitparse.FitFile("plot_fit_activity/resources/Morning_Run_step1.fit")
    import_messages = fitfile.messages

    # Set auto_define to true, so that the builder creates the required Definition Messages for us.
    builder = FitFileBuilder(auto_define=True, min_string_size=50)

    # Read position data from a GPX file
    # gpx_file = open('../tests/data/old_stage_left_hand_lee.gpx', 'r')
    # gpx = gpxpy.parse(gpx_file)

    message = FileIdMessage()

    file_id = list(
        filter(lambda mess: mess.def_mesg.name == "file_id", import_messages)
    )[0]
    message.type = list(
        filter(lambda mess: mess.field_def.name == "type", file_id.fields)
    )[0].raw_value
    message.manufacturer = list(
        filter(lambda mess: mess.field_def.name == "manufacturer", file_id.fields)
    )[0].raw_value
    message.product = list(
        filter(lambda mess: mess.field_def.name == "product", file_id.fields)
    )[0].raw_value
    message.timeCreated = round(
        list(
            filter(lambda mess: mess.field_def.name == "time_created", file_id.fields)
        )[0]
        .value.replace(tzinfo=datetime.timezone.utc)
        .timestamp()
        * 1000
    )
    message.serialNumber = list(
        filter(lambda mess: mess.field_def.name == "serial_number", file_id.fields)
    )[0].raw_value
    builder.add(message)

    # Every FIT course file MUST contain a Activity message
    message = ActivityMessage()

    sport = list(filter(lambda mess: mess.def_mesg.name == "sport", import_messages))[0]
    message.activityName = list(
        filter(lambda mess: mess.field_def.name == "name", sport.fields)
    )[0].raw_value
    message.sport = list(
        filter(lambda mess: mess.field_def.name == "sport", sport.fields)
    )[0].raw_value
    builder.add(message)

    # Timer Events are REQUIRED for FIT course files
    # start_timestamp = round(datetime.datetime.now().timestamp() * 1000)

    events = list(filter(lambda mess: mess.def_mesg.name == "event", import_messages))
    activities_events = []
    for event in events:
        message = EventMessage()
        message.event = list(filter(lambda mess: mess.name == "event", event.fields))[
            0
        ].raw_value  # Event.TIMER
        message.event_type = list(
            filter(lambda mess: mess.name == "event_type", event.fields)
        )[
            0
        ].raw_value  # EventType.START
        message.timestamp = round(
            list(filter(lambda mess: mess.name == "timestamp", event.fields))[0]
            .value.replace(tzinfo=datetime.timezone.utc)
            .timestamp()
            * 1000
        )
        activities_events.append(message)
    builder.add_all(activities_events)

    records = list(filter(lambda mess: mess.def_mesg.name == "record", import_messages))
    activities_records = []  # track points
    for record in records:
        message = RecordMessage()
        message.position_lat = list(
            filter(lambda mess: mess.name == "position_lat", record.fields)
        )[0].raw_value * (180 / 2**31)
        message.position_long = list(
            filter(lambda mess: mess.name == "position_long", record.fields)
        )[0].raw_value * (180 / 2**31)
        message.distance = list(
            filter(lambda mess: mess.name == "distance", record.fields)
        )[0].value
        message.enhanced_altitude = list(
            filter(lambda mess: mess.name == "enhanced_altitude", record.fields)
        )[0].value
        message.enhanced_speed = list(
            filter(lambda mess: mess.name == "enhanced_speed", record.fields)
        )[0].value
        message.heart_rate = list(
            filter(lambda mess: mess.name == "heart_rate", record.fields)
        )[0].raw_value
        message.power = list(filter(lambda mess: mess.name == "power", record.fields))[
            0
        ].raw_value
        message.timestamp = round(
            list(filter(lambda mess: mess.name == "timestamp", record.fields))[0]
            .value.replace(tzinfo=datetime.timezone.utc)
            .timestamp()
            * 1000
        )
        activities_records.append(message)
    builder.add_all(activities_records)

    #  Add start and end course points (i.e. way points)
    #
    # message = CoursePointMessage()
    # message.timestamp = course_records[0].timestamp
    # message.position_lat = course_records[0].position_lat
    # message.position_long = course_records[0].position_long
    # message.type = CoursePoint.SEGMENT_START
    # message.course_point_name = 'start'
    # builder.add(message)

    # message = CoursePointMessage()
    # message.timestamp = course_records[-1].timestamp
    # message.position_lat = course_records[-1].position_lat
    # message.position_long = course_records[-1].position_long
    # message.type = CoursePoint.SEGMENT_END
    # message.course_point_name = 'end'
    # builder.add(message)

    # # stop event
    # message = EventMessage()
    # message.event = Event.TIMER
    # message.eventType = EventType.STOP_ALL
    # message.timestamp = timestamp
    # builder.add(message)

    # Every FIT course file MUST contain a Lap message
    # elapsed_time = timestamp - start_timestamp

    laps = list(filter(lambda mess: mess.def_mesg.name == "lap", import_messages))
    activities_laps = []
    for lap in laps:
        message = LapMessage()
        message.timestamp = round(
            list(filter(lambda mess: mess.name == "timestamp", lap.fields))[0]
            .value.replace(tzinfo=datetime.timezone.utc)
            .timestamp()
            * 1000
        )  # timestamp
        message.start_time = round(
            list(filter(lambda mess: mess.name == "start_time", lap.fields))[0]
            .value.replace(tzinfo=datetime.timezone.utc)
            .timestamp()
            * 1000
        )  # start_timestamp
        message.total_elapsed_time = list(
            filter(lambda mess: mess.name == "total_elapsed_time", lap.fields)
        )[
            0
        ].raw_value  # elapsed_time
        message.total_timer_time = list(
            filter(lambda mess: mess.name == "total_timer_time", lap.fields)
        )[
            0
        ].raw_value  # elapsed_time
        message.start_position_lat = list(
            filter(lambda mess: mess.name == "start_position_lat", lap.fields)
        )[0].raw_value * (180 / 2**31)
        message.start_position_long = list(
            filter(lambda mess: mess.name == "start_position_long", lap.fields)
        )[0].raw_value * (180 / 2**31)
        message.end_position_lat = list(
            filter(lambda mess: mess.name == "end_position_lat", lap.fields)
        )[0].raw_value * (180 / 2**31)
        message.end_position_long = list(
            filter(lambda mess: mess.name == "end_position_long", lap.fields)
        )[0].raw_value * (180 / 2**31)
        message.total_distance = list(
            filter(lambda mess: mess.name == "total_distance", lap.fields)
        )[0].value
        activities_laps.append(message)
    builder.add_all(activities_laps)

    # Finally build the FIT file object and write it to a file
    fit_file = builder.build()

    out_path = "write_fit/tests/old_stage_course.fit"
    fit_file.to_file(out_path)
    # csv_path = '../tests/out/old_stage_course.csv'
    # fit_file.to_csv(csv_path)


if __name__ == "__main__":
    main()
