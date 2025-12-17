
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

def extract_provenance_metrics(provenance_response, flow_name=None, process_group_id=None):
    """
    Extracts and formats provenance events from a provenance query response.
    
    Args:
        provenance_response: The response from query_nifi_provenance()
        flow_name: Optional flow name to tag events with
        process_group_id: Optional process group ID to tag events with
    
    Returns:
        List of provenance event dictionaries with selected fields
    """
    metrics = []
    
    try:
        provenance_data = provenance_response.get("provenance", {})
        results = provenance_data.get("results", {})
        events = results.get("provenanceEvents", [])
        
        logging.info(f"Processing {len(events)} provenance events")
        
        for event in events:
            try:
                # Extract key provenance fields
                entry = {
                    "event_id": event.get("eventId"),
                    "event_type": event.get("eventType"),
                    "event_time": event.get("eventTime"),
                    "event_duration": event.get("eventDuration"),
                    "lineage_start_date": event.get("lineageStartDate"),
                    "component_id": event.get("componentId"),
                    "component_type": event.get("componentType"),
                    "component_name": event.get("componentName"),
                    "flowfile_uuid": event.get("flowFileUuid"),
                    "file_size": event.get("fileSize"),
                    "file_size_bytes": event.get("fileSizeBytes"),
                    "cluster_node_id": event.get("clusterNodeId"),
                    "cluster_node_address": event.get("clusterNodeAddress"),
                    
                    # Process group information
                    "group_id": event.get("groupId"),  # From NiFi API response
                    
                    # Parent/child relationships
                    "parent_uuids": event.get("parentUuids", []),
                    "child_uuids": event.get("childUuids", []),
                    
                    # Content claims
                    "content_equal": event.get("contentEqual"),
                    "input_content_available": event.get("inputContentAvailable"),
                    "output_content_available": event.get("outputContentAvailable"),
                    
                    # Transit details (for SEND/RECEIVE events)
                    "transit_uri": event.get("transitUri"),
                    
                    # Relationship (for ROUTE events)
                    "relationship": event.get("relationship"),
                    
                    # Details field (can contain additional context)
                    "details": event.get("details"),
                    
                    # Attributes (optional - can be large)
                    # Uncomment if you need to capture FlowFile attributes
                    # "attributes": event.get("attributes", {}),
                    # "updated_attributes": event.get("updatedAttributes", {}),
                }
                
                # Add flow metadata if provided (from config)
                if flow_name:
                    entry["flow_name"] = flow_name
                if process_group_id:
                    entry["process_group_id"] = process_group_id
                
                metrics.append(entry)
                
            except Exception as e:
                logging.warning(f"Failed to extract provenance event {event.get('eventId', 'unknown')}: {e}")
                continue
        
        # Add query metadata as a summary entry
        summary = {
            "event_id": "query_summary",
            "event_type": "QUERY_SUMMARY",
            "total_count": results.get("totalCount", 0),
            "total_bytes": results.get("total", 0),
            "oldest_event": results.get("oldestEvent"),
            "query_duration_millis": provenance_data.get("results", {}).get("queryDuration"),
            "percent_completed": provenance_data.get("percentCompleted", 100),
        }
        
        # Add flow metadata to summary as well
        if flow_name:
            summary["flow_name"] = flow_name
        if process_group_id:
            summary["process_group_id"] = process_group_id
        
        metrics.append(summary)
        
        logging.info(f"Extracted {len(metrics)-1} provenance events plus 1 summary")
        
    except Exception as e:
        logging.error(f"Failed to extract provenance metrics: {e}", exc_info=True)
        return []
    
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
                "diskUsage": node.get("diskUsage"),
                "heapUsage": node.get("heapUsage"),
                "processorLoadAverage": node.get("processorLoadAverage"),
                "uptime": node.get("uptime")
            }
            metrics.append(node_entry)
    except KeyError as e:
        logging.error(f"Could not extract cluster summary metrics, payload structure issue: {e}")
    return metrics
