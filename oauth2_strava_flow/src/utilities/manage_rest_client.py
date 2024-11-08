import requests
import sys
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError

backoff_factor = 3
total = 5

# # calculate delay for each call and total delay
# total_delay=0
# delay_for_each_call = []
# for i in range(1,total+1):
#     delay_for_each_call.append(backoff_factor * (2* (i-1)))
#     total_delay = total_delay + delay_for_each_call[-1]

retry_strategy = Retry(
    total=total,
    connect=total,
    read=total,
    status=total,
    redirect=total,
    backoff_factor=backoff_factor,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST", "DELETE", "PATCH", "PUT"],
)

adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)


def call_rest_api(
    method, url, headers, data="", files=None, params=None, stream_cond=False
):
    try:
        if method == "GET":
            response = http.get(url, headers=headers)
        elif method == "POST":
            if files:
                response = http.post(url, headers=headers, files=files, params=params)
            else:
                response = http.post(url, headers=headers, data=data)
        elif method == "DELETE":
            response = http.delete(url, headers=headers)
        elif method == "PATCH":
            response = http.patch(url, headers=headers, data=data)
        elif method == "PUT":
            response = http.put(url, headers=headers, data=data)
    except HTTPError:
        raise
    except Exception:
        raise ValueError(sys.exc_info()[1])
    return response


def json_safe_get(dct, fun, *keys):
    for key in keys:
        try:
            dct = dct[key]
        except KeyError:
            raise ValueError(f"Error when try to extract key {key} from json in {fun}")
    return dct
