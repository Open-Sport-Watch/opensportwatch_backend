from utilities.logger import log_setup
from utilities.manage_redis import checkRedisConn
from utilities.manage_rest_server import init_rest_server
from utilities.manage_strava_api import strava_auth_on_browser

log_setup("log.txt")

REDIRECT_PORT=3000
REDIRECT_URI=f"http://localhost:{REDIRECT_PORT}/redirect"

# checkRedisConn()

strava_auth_on_browser(REDIRECT_URI)
init_rest_server(REDIRECT_PORT)
