from utilities.manage_rest_client import call_rest_api, json_safe_get
from utilities.logger import error
import webbrowser
import json
import os

STRAVA_BASE_URL = "https://www.strava.com"

CLIENT_ID = os.getenv("CLIENT_ID","<<your_client_id>>")
CLIENT_SECRET=os.getenv("CLIENT_SECRET","<<your_client_secret>>")

def strava_auth_on_browser(REDIRECT_URI):
    webbrowser.open_new_tab(url = f"{STRAVA_BASE_URL}/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&approval_prompt=force&scope=activity:write")


def get_strava_token(code):
    url = f"{STRAVA_BASE_URL}/api/v3/oauth/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&code={code}&grant_type=authorization_code"

    response = call_rest_api("POST",url,"")
    if response.status_code==200:
        return json.loads(response.content.decode("utf-8","ignore"))
    else:
        error(response.text)