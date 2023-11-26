from utilities.logger import log_setup
from utilities.manage_redis import check_redis_conn, check_user_already_exist
from utilities.manage_rest_server import init_rest_server
from utilities.manage_strava_api import strava_auth_on_browser
import os

log_setup("log.txt")

REDIRECT_PORT=3000
REDIRECT_URI=f"http://localhost:{REDIRECT_PORT}/redirect"
ATHLETE_ID=os.getenv("ATHLETE_ID")

redis_cli = check_redis_conn()

if not check_user_already_exist(ATHLETE_ID):
    strava_auth_on_browser(REDIRECT_URI)
    init_rest_server(REDIRECT_PORT)
