import requests
from datetime import datetime


def check_rate_limit(token):
    url = "https://api.github.com/rate_limit"
    headers = {
        "Authorization": f"token {token}"
    }

    response = requests.get(url, headers=headers)
    json_response = response.json()

    remaining_requests = json_response["resources"]["core"]["remaining"]
    reset_timestamp = json_response["resources"]["core"]["reset"]

    if remaining_requests == 0:
        reset_time = datetime.fromtimestamp(reset_timestamp).strftime(
            "%Y-%m-%d %I:%M:%S %p")
        return reset_time
    else:
        return None
