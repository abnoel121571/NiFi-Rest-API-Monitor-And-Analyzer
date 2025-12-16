import requests
import logging

def _get_request(url, auth, token, timeout):
    """Helper function to perform a GET request and handle responses."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    logging.debug(f"Requesting data from: {url}")
    try:
        response = requests.get(url, headers=headers, auth=auth, timeout=timeout, verify=False)
        response.raise_for_status()
        logging.debug(f"Successfully retrieved data from: {url}")
        return response.json()
    except Exception as e:
        logging.error(f"Failed to retrieve data from {url}: {e}")
        raise

def get_nifi_processors(nifi_api_url, auth=None, token=None, timeout=10, process_group_id='root'):
    """Retrieves all processors from a given process group."""
    url = f"{nifi_api_url}/process-groups/{process_group_id}/processors"
    return _get_request(url, auth, token, timeout)

def get_nifi_connections(nifi_api_url, auth=None, token=None, timeout=10, process_group_id='root'):
    """Retrieves all connections from a given process group."""
    url = f"{nifi_api_url}/process-groups/{process_group_id}/connections"
    return _get_request(url, auth, token, timeout)

def get_nifi_system_diagnostics(nifi_api_url, auth=None, token=None, timeout=10):
    """Retrieves system diagnostics, including JVM metrics."""
    url = f"{nifi_api_url}/system-diagnostics"
    return _get_request(url, auth, token, timeout)

def get_nifi_controller_services(nifi_api_url, auth=None, token=None, timeout=10):
    """Retrieves all controller services."""
    url = f"{nifi_api_url}/flow/controller/controller-services"
    return _get_request(url, auth, token, timeout)

def get_nifi_reporting_tasks(nifi_api_url, auth=None, token=None, timeout=10):
    """Retrieves all reporting tasks."""
    url = f"{nifi_api_url}/flow/reporting-tasks"
    return _get_request(url, auth, token, timeout)

def get_nifi_bulletins(nifi_api_url, auth=None, token=None, timeout=10):
    """Retrieves the bulletin board content."""
    url = f"{nifi_api_url}/flow/bulletin-board"
    return _get_request(url, auth, token, timeout)

