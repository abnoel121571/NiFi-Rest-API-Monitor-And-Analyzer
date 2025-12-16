import logging

def extract_processor_metrics(processors, metric_keys, flow_name=None, processor_name_filter=None):
    """
    Extracts selected metrics from a list of processors,
    optionally filtering by a list of processor names.
    """
    metrics = []
    for proc in processors:
        try:
            component = proc.get("component", {})
            processor_name = component.get("name")

            # If a filter is provided, skip processors that are not in the list
            if processor_name_filter and processor_name not in processor_name_filter:
                continue
            
            snapshot = proc.get("status", {}).get("aggregateSnapshot", {})
            entry = {
                "id": component.get("id"),
                "name": processor_name,
                "type": component.get("type"),
                "runStatus": snapshot.get("runStatus")
            }
            if flow_name:
                entry["flow_name"] = flow_name

            for key in metric_keys:
                entry[key] = snapshot.get(key)
            metrics.append(entry)
        except KeyError as e:
            logging.warning(f"Skipping processor due to missing key: {e}")
    return metrics

def extract_connection_metrics(connections, metric_keys, flow_name=None):
    """
    Extracts queue metrics from a list of connections, optionally tagging them with a flow name.
    """
    metrics = []
    for conn in connections:
        try:
            component = conn.get("component", {})
            snapshot = conn.get("status", {}).get("aggregateSnapshot", {})
            entry = {
                "id": component.get("id"),
                "name": component.get("name")
            }
            if flow_name:
                entry["flow_name"] = flow_name
                
            for key in metric_keys:
                entry[key] = snapshot.get(key)
            metrics.append(entry)
        except KeyError as e:
            logging.warning(f"Skipping connection due to missing key: {e}")
    return metrics

def extract_jvm_metrics(diagnostics, metric_keys):
    """Extracts JVM metrics from the system diagnostics payload."""
    logging.debug(f"extract_jvm_metrics: Incoming diagnostics payload: {diagnostics}")
    try:
        system_diagnostics_data = diagnostics.get("systemDiagnostics", {})
        snapshot = None

        # Prioritize aggregateSnapshot if available (for overall cluster/node summary)
        if "aggregateSnapshot" in system_diagnostics_data:
            snapshot = system_diagnostics_data["aggregateSnapshot"]
            logging.debug("extract_jvm_metrics: Using aggregateSnapshot.")
        elif system_diagnostics_data.get("nodeSnapshots"):
            # If no aggregate, use the first node's snapshot (e.g., in a single-node setup where aggregate isn't populated)
            # Ensure there's at least one node snapshot before trying to access it
            if system_diagnostics_data["nodeSnapshots"]:
                snapshot = system_diagnostics_data["nodeSnapshots"][0]["snapshot"]
                logging.debug("extract_jvm_metrics: Using first node's snapshot.")
            else:
                logging.warning("extract_jvm_metrics: 'nodeSnapshots' found but is empty.")
        
        if snapshot is None:
            logging.error("extract_jvm_metrics: No valid JVM snapshot found in system diagnostics payload.")
            return []
            
        logging.debug(f"extract_jvm_metrics: Selected snapshot: {snapshot}")

        entry = {"id": "jvm_metrics"}
        for key in metric_keys:
            value = snapshot.get(key)
            if value is not None: # Only add if value exists
                entry[key] = value
            else:
                logging.warning(f"JVM metric '{key}' not found in the selected snapshot. Skipping this key.")
        return [entry]
    except (KeyError, IndexError) as e:
        logging.error(f"Could not extract JVM metrics due to payload structure issue: {e}. Diagnostics: {diagnostics}", exc_info=True)
        return []

def extract_controller_service_metrics(services, metric_keys):
    """Extracts metrics from a list of controller services."""
    metrics = []
    for service in services:
        try:
            component = service.get("component", {})
            status = service.get("status", {})
            entry = {
                "id": component.get("id"),
                "name": component.get("name"),
                "type": component.get("type")
            }
            for key in metric_keys:
                entry[key] = status.get(key)
            metrics.append(entry)
        except KeyError as e:
            logging.warning(f"Skipping controller service due to missing key: {e}")
    return metrics

def extract_reporting_task_metrics(tasks, metric_keys):
    """Extracts metrics from a list of reporting tasks."""
    metrics = []
    for task in tasks:
        try:
            component = task.get("component", {})
            status = task.get("status", {})
            entry = {
                "id": component.get("id"),
                "name": component.get("name"),
                "type": component.get("type")
            }
            for key in metric_keys:
                entry[key] = status.get(key)
            metrics.append(entry)
        except KeyError as e:
            logging.warning(f"Skipping reporting task due to missing key: {e}")
    return metrics

def extract_bulletin_metrics(bulletins):
    """Extracts and formats bulletin messages."""
    metrics = []
    for bulletin in bulletins:
        # The bulletin object itself contains all the useful information.
        # We can just append it directly.
        metrics.append(bulletin)
    return metrics

def extract_cluster_summary_metrics(cluster_summary):
    """Extracts key metrics from the cluster summary payload."""
    metrics = []
    try:
        cluster_details = cluster_summary.get("clusterSummary", {})
        entry = {
            "id": "cluster_summary",
            "clustered": cluster_details.get("clustered"),
            "connectedToCluster": cluster_details.get("connectedToCluster"),
            "totalNodeCount": cluster_details.get("totalNodeCount"),
            "connectedNodeCount": cluster_details.get("connectedNodeCount"),
            "disconnectedNodeCount": cluster_details.get("disconnectedNodeCount"),
            "heartbeatCount": cluster_details.get("heartbeatCount")
        }
        metrics.append(entry)

        # Optionally, extract metrics for each node in the cluster
        for node in cluster_details.get("nodes", []):
            node_entry = {
                "id": f"cluster_node_{node.get('nodeId')}",
                "nodeId": node.get("nodeId"),
                "address": node.get("address"),
                "apiPort": node.get("apiPort"),
                "status": node.get("status"),
                "roles": node.get("roles"),
                "activeThreadCount": node.get("activeThreadCount"),
                "queued": node.get("queued"),
                "flowFilesReceived": node.get("flowFilesReceived"),
                "bytesReceived": node.get("bytesReceived"),
                "flowFilesSent": node.get("flowFilesSent"),
                "bytesSent": node.get("bytesSent"),
                "flowFilesTransferred": node.get("flowFilesTransferred"),
                "bytesTransferred": node.get("bytesTransferred"),
                "bytesRead": node.get("bytesRead"),
                "bytesWritten": node.get("bytesWritten"),
                "diskUsage": node.get("diskUsage"), # This is a list of objects
                "heapUsage": node.get("heapUsage"),
                "processorLoadAverage": node.get("processorLoadAverage"),
                "uptime": node.get("uptime")
            }
            metrics.append(node_entry)
    except KeyError as e:
        logging.error(f"Could not extract cluster summary metrics, payload structure issue: {e}")
    return metrics

