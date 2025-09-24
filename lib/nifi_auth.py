import requests
import logging
import urllib3

# Disable SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_nifi_token(token_url, username, password):
    """
    Fetches an authentication token from the NiFi API.
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    data = {
        "username": username,
        "password": password
    }
    logging.debug(f"Fetching NiFi token from {token_url}")
    try:
        response = requests.post(token_url, headers=headers, data=data, verify=False, timeout=10)
        response.raise_for_status()
        token = response.text.strip()
        logging.debug("NiFi token fetched successfully.")
        return token
    except requests.exceptions.HTTPError as e:
        error_msg = f"Failed to fetch NiFi token (HTTP {e.response.status_code}): {e.response.text}"
        logging.error(error_msg)
        raise Exception(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch NiFi token (Connection Error): {e}"
        logging.error(error_msg)
        raise Exception(error_msg)

