from utilities.manage_rest import call_rest_api, json_safe_get
from utilities.logger import log_setup, info, error
import json, os
from flask import Flask, request, jsonify
from waitress import serve
import webbrowser

log_setup("log.txt")

STRAVA_BASE_URL = "https://www.strava.com"
REDIRECT_PORT=3000
REDIRECT_URI=f"http://localhost:{REDIRECT_PORT}/redirect"

CLIENT_ID = os.getenv("CLIENT_ID","<<your_client_id>>")
CLIENT_SECRET=os.getenv("CLIENT_SECRET","<<your_client_secret>>")


def response_template(message,status,statusCode,label,result):
    response = {
        "message": message,
        "status": status,
        "statusCode": statusCode,
        "label": label,
        "result": result
    }
    return response

def get_strava_token(code):
    url = f"{STRAVA_BASE_URL}/api/v3/oauth/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&code={code}&grant_type=authorization_code"

    response = call_rest_api("POST",url,"")
    if response.status_code==200:
        return json.loads(response.content.decode("utf-8","ignore"))
    else:
        error(response.text)

def configure_routes(app):
    @app.route('/redirect') 
    def strava_redirect():
        args = request.args
        code = args['code']
        token = get_strava_token(code)
        return jsonify(response_template('The Strava authentication flow has finished successfully!','Ok',200,'STRAVA_OAUTH_FLOW',''))


webbrowser.open_new_tab(url = f"{STRAVA_BASE_URL}/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&approval_prompt=force&scope=activity:write")

app = Flask(__name__)
# app.config["EXPLAIN_TEMPLATE_LOADING"] = True # for debug purpose
configure_routes(app)
serve(app, host='0.0.0.0', port=REDIRECT_PORT)
