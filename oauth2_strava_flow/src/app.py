from utilities.logger import log_setup
from utilities.manage_redis import (
    check_redis_conn,
    check_user_already_exist,
    get_user,
    save_user_tokens,
)
from utilities.manage_rest_server import init_rest_server
from utilities.manage_strava_api import (
    strava_auth_on_browser,
    get_strava_refresh_token,
    get_strava_user,
    # post_activity_on_strava,
    get_strava_club_activities,
    init_strava_params,
)
import os
import time
from dotenv import load_dotenv
import ntpath

log_setup("log.txt")
load_dotenv(os.path.join(ntpath.dirname(os.path.realpath(__file__)), ".env"))

REDIRECT_PORT = 3000
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/redirect"
ATHLETE_ID = os.getenv("ATHLETE_ID", "<<your_athele_id>>")

init_strava_params()
redis_cli = check_redis_conn()

if not check_user_already_exist(ATHLETE_ID):
    # first strava authorization
    strava_auth_on_browser(REDIRECT_URI)
    init_rest_server(REDIRECT_PORT)
else:
    # after the first time
    athlete = get_user(ATHLETE_ID)
    if athlete["expires_at"] < time.time():
        tokens = get_strava_refresh_token(athlete["refresh_token"])
        save_user_tokens(ATHLETE_ID, tokens)
        athlete = get_user(ATHLETE_ID)
    user = get_strava_user(athlete["access_token"])

    club_activities_list = get_strava_club_activities(athlete["access_token"])
    print(club_activities_list)

    # upload activity
    # post_activity_on_strava(athlete["access_token"],"oauth2_strava_flow/resources/14230586315_ACTIVITY.fit")
