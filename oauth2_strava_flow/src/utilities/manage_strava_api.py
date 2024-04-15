from utilities.manage_rest_client import call_rest_api
from utilities.logger import error
import webbrowser
import json
import os

STRAVA_BASE_URL = "https://www.strava.com"

CLIENT_ID = os.getenv("CLIENT_ID", "<<your_client_id>>")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "<<your_client_secret>>")


def strava_auth_on_browser(REDIRECT_URI):
    webbrowser.open_new_tab(
        url=f"{STRAVA_BASE_URL}/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&approval_prompt=force&scope=activity:write"
    )


def get_strava_authorization_code(code):
    url = f"{STRAVA_BASE_URL}/api/v3/oauth/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&code={code}&grant_type=authorization_code"

    response = call_rest_api("POST", url, "")
    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8", "ignore"))
    else:
        error(response.text)


def get_strava_refresh_token(refresh_token):
    url = f"{STRAVA_BASE_URL}/api/v3/oauth/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&grant_type=refresh_token&refresh_token={refresh_token}"

    response = call_rest_api("POST", url, "")
    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8", "ignore"))
    else:
        error(response.text)


def get_strava_user(access_token):
    url = f"{STRAVA_BASE_URL}/api/v3/athlete"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = call_rest_api("GET", url, headers)
    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8", "ignore"))
    else:
        error(response.text)


def get_strava_club_activities(access_token):
    CLUB_ID = os.getenv("CLUB_ID", "<<your_club_id>>")
    retrieve_all = False
    page = 1
    activities_list = []
    while not retrieve_all:
        url = f"{STRAVA_BASE_URL}/api/v3/clubs/{CLUB_ID}/activities?page={page}&per_page={100}"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = call_rest_api("GET", url, headers)
        if response.status_code == 200:
            activities_to_add = json.loads(response.content.decode("utf-8", "ignore"))
            activities_list.extend(activities_to_add)
            if len(activities_to_add) != 100:
                retrieve_all = True
            else:
                page += 1
        else:
            error(response.text)
    return activities_list


def post_activity_on_strava(access_token, file_path):
    url = f"{STRAVA_BASE_URL}/api/v3/uploads"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = call_rest_api(
        "POST",
        url,
        headers,
        files={"file": open(file_path, "rb")},
        params={"data_type": "fit"},
    )
    if response.status_code == 201:
        return json.loads(response.content.decode("utf-8", "ignore"))
    else:
        error(response.text)
