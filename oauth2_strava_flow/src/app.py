from utilities.logger import log_setup
from utilities.manage_redis import check_redis_conn, check_user_already_exist, get_user, save_user_tokens
from utilities.manage_rest_server import init_rest_server
from utilities.manage_strava_api import strava_auth_on_browser, get_strava_refresh_token, get_strava_user
import os
import time

log_setup("log.txt")

REDIRECT_PORT=3000
REDIRECT_URI=f"http://localhost:{REDIRECT_PORT}/redirect"
ATHLETE_ID=os.getenv("ATHLETE_ID")

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
        save_user_tokens(ATHLETE_ID,tokens)
        athlete = get_user(ATHLETE_ID)
    user = get_strava_user(athlete["access_token"])
    print(user)
