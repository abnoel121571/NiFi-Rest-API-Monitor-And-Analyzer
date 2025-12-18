import requests
import logging
import time

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

def _post_request(url, auth, token, timeout, payload=None):
    """Helper function to perform a POST request and handle responses."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    headers["Content-Type"] = "application/json"
    logging.debug(f"Posting data to: {url}")
    try:
        response = requests.post(url, headers=headers, auth=auth, json=payload, timeout=timeout, verify=False)
        response.raise_for_status()
        logging.debug(f"Successfully posted data to: {url}")
        return response.json()
    except Exception as e:
        logging.error(f"Failed to post data to {url}: {e}")
        raise

def _delete_request(url, auth, token, timeout):
    """Helper function to perform a DELETE request."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    logging.debug(f"Deleting resource at: {url}")
    try:
        response = requests.delete(url, headers=headers, auth=auth, timeout=timeout, verify=False)
        response.raise_for_status()
        logging.debug(f"Successfully deleted resource at: {url}")
        return response.json() if response.text else {}
    except Exception as e:
        logging.error(f"Failed to delete resource at {url}: {e}")
        raise

def get_nifi_processors(nifi_api_url, auth=None, token=None, timeout=10, process_group_id='root'):
    """Retrieves all processors from a given process group (non-recursive)."""
    url = f"{nifi_api_url}/process-groups/{process_group_id}/processors"
    return _get_request(url, auth, token, timeout)

def get_nifi_processors_flow(nifi_api_url, auth=None, token=None, timeout=10, process_group_id='root'):
    """
    Retrieves all processors from a process group and all descendants using the /flow endpoint.
    This includes processors from nested process groups.
    
    Args:
        nifi_api_url: Base NiFi API URL
        auth: HTTP Basic Auth object
        token: Bearer token
        timeout: Request timeout
        process_group_id: Process group ID (default: 'root')
    
    Returns:
        Dictionary with 'processors' key containing list of processor objects
    """
    url = f"{nifi_api_url}/flow/process-groups/{process_group_id}"
    logging.debug(f"Fetching processors recursively from: {url}")
    
    try:
        data = _get_request(url, auth, token, timeout)
        
        # Navigate the response structure
        process_group_flow = data.get("processGroupFlow", {})
        flow = process_group_flow.get("flow", {})
        
        # Processors are directly in the flow
        processors = flow.get("processors", [])
        
        logging.info(f"Retrieved {len(processors)} processors (recursive) from process group {process_group_id}")
        
        return {"processors": processors}
        
    except Exception as e:
        logging.error(f"Failed to retrieve processors from flow endpoint: {e}")
        logging.warning("Falling back to non-recursive processor collection")
        return get_nifi_processors(nifi_api_url, auth, token, timeout, process_group_id)

def get_nifi_connections(nifi_api_url, auth=None, token=None, timeout=10, process_group_id='root'):
    """Retrieves all connections from a given process group (non-recursive)."""
    url = f"{nifi_api_url}/process-groups/{process_group_id}/connections"
    return _get_request(url, auth, token, timeout)

def get_nifi_connections_flow(nifi_api_url, auth=None, token=None, timeout=10, process_group_id='root'):
    """
    Retrieves all connections from a process group and all descendants using the /flow endpoint.
    This includes connections from nested process groups.
    
    Args:
        nifi_api_url: Base NiFi API URL
        auth: HTTP Basic Auth object
        token: Bearer token
        timeout: Request timeout
        process_group_id: Process group ID (default: 'root')
    
    Returns:
        Dictionary with 'connections' key containing list of connection objects
    """
    url = f"{nifi_api_url}/flow/process-groups/{process_group_id}"
    logging.debug(f"Fetching connections recursively from: {url}")
    
    try:
        data = _get_request(url, auth, token, timeout)
        
        # Navigate the response structure
        process_group_flow = data.get("processGroupFlow", {})
        flow = process_group_flow.get("flow", {})
        
        # Connections are directly in the flow
        connections = flow.get("connections", [])
        
        logging.info(f"Retrieved {len(connections)} connections (recursive) from process group {process_group_id}")
        
        return {"connections": connections}
        
    except Exception as e:
        logging.error(f"Failed to retrieve connections from flow endpoint: {e}")
        logging.warning("Falling back to non-recursive connection collection")
        return get_nifi_connections(nifi_api_url, auth, token, timeout, process_group_id)

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

def query_nifi_provenance(nifi_api_url, auth=None, token=None, timeout=30, query_params=None):
    """
    Queries provenance data from NiFi.
    
    This is a two-step process:
    1. Submit a provenance query
    2. Poll the query status until complete
    3. Retrieve the results
    4. Delete the query
    
    Args:
        nifi_api_url: Base NiFi API URL
        auth: HTTP Basic Auth object
        token: Bearer token for authentication
        timeout: Request timeout in seconds
        query_params: Dictionary with query parameters such as:
            - startDate: Start time for query (format: "MM/dd/yyyy HH:mm:ss")
            - endDate: End time for query (format: "MM/dd/yyyy HH:mm:ss")
            - maxResults: Maximum number of results (default: 1000)
            - componentId: Filter by specific component ID
            - eventType: Filter by event type (e.g., CREATE, RECEIVE, SEND, DROP, etc.)
    
    Returns:
        Dictionary containing provenance events and query metadata
    """
    # Build the query request payload
    query_payload = {
        "provenance": {
            "request": {
                "maxResults": query_params.get("maxResults", 1000) if query_params else 1000,
                "summarize": False,
                "incrementalResults": False
            }
        }
    }
    
    # Add optional query parameters
    if query_params:
        search_terms = {}
        if "startDate" in query_params:
            search_terms["startDate"] = query_params["startDate"]
        if "endDate" in query_params:
            search_terms["endDate"] = query_params["endDate"]
        if "componentId" in query_params:
            search_terms["ProcessorID"] = query_params["componentId"]
        if "eventType" in query_params:
            search_terms["EventType"] = query_params["eventType"]
        
        if search_terms:
            query_payload["provenance"]["request"]["searchTerms"] = search_terms
    
    # Step 1: Submit the provenance query
    submit_url = f"{nifi_api_url}/provenance"
    logging.info(f"Submitting provenance query with params: {query_params}")
    
    try:
        query_response = _post_request(submit_url, auth, token, timeout, query_payload)
        query_id = query_response["provenance"]["id"]
        logging.debug(f"Provenance query submitted with ID: {query_id}")
        
        # Step 2: Poll for query completion
        status_url = f"{nifi_api_url}/provenance/{query_id}"
        max_polls = 30  # Maximum number of polling attempts
        poll_interval = 2  # Seconds between polls
        
        for attempt in range(max_polls):
            status_response = _get_request(status_url, auth, token, timeout)
            finished = status_response["provenance"]["finished"]
            percent_complete = status_response["provenance"].get("percentCompleted", 0)
            
            logging.debug(f"Provenance query {query_id} - {percent_complete}% complete")
            
            if finished:
                logging.info(f"Provenance query {query_id} completed successfully")
                
                # Step 3: Clean up - delete the query
                try:
                    _delete_request(status_url, auth, token, timeout)
                    logging.debug(f"Deleted provenance query {query_id}")
                except Exception as e:
                    logging.warning(f"Failed to delete provenance query {query_id}: {e}")
                
                return status_response
            
            time.sleep(poll_interval)
        
        # If we get here, the query timed out
        logging.error(f"Provenance query {query_id} timed out after {max_polls * poll_interval} seconds")
        
        # Try to delete the query anyway
        try:
            _delete_request(status_url, auth, token, timeout)
        except Exception as e:
            logging.warning(f"Failed to delete timed-out provenance query {query_id}: {e}")
        
        raise TimeoutError(f"Provenance query did not complete in time")
        
    except Exception as e:
        logging.error(f"Failed to query provenance data: {e}")
        raise

