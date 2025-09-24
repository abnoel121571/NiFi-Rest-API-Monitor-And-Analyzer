from lib.metrics_parser import (
    extract_processor_metrics,
    extract_connection_metrics,
    extract_jvm_metrics,
    extract_controller_service_metrics,
    extract_reporting_task_metrics,
    extract_bulletin_metrics,
    extract_cluster_summary_metrics
)

def test_extract_processor_metrics(mock_processor_list):
    """Tests that processor metrics are extracted correctly."""
    processors = mock_processor_list["processors"]
    metric_keys = ["nifi_amount_bytes_written", "activeThreadCount"]
    result = extract_processor_metrics(processors, metric_keys)
    assert len(result) == 2
    assert result[0]["name"] == "GenerateFlowFile"
    assert result[0]["nifi_amount_bytes_written"] == 1024
    assert result[0]["activeThreadCount"] == 2

def test_extract_connection_metrics(mock_connection_list):
    """Tests that connection metrics are extracted correctly."""
    connections = mock_connection_list["connections"]
    metric_keys = ["queuedCount", "bytesIn", "backPressureObjectThreshold"]
    result = extract_connection_metrics(connections, metric_keys)
    assert len(result) == 1
    assert result[0]["name"] == "success"
    assert result[0]["bytesIn"] == 20000
    assert result[0]["backPressureObjectThreshold"] == 10000

def test_extract_jvm_metrics(mock_system_diagnostics):
    """Tests that detailed JVM metrics are extracted correctly."""
    diagnostics = mock_system_diagnostics
    metric_keys = ["heapUsed", "heapUsage", "threadCount", "flowFileRepositoryStorageUsage"]
    result = extract_jvm_metrics(diagnostics, metric_keys)
    assert len(result) == 1
    assert result[0]["id"] == "jvm_metrics"
    assert result[0]["heapUsage"] == "30%"
    assert result[0]["threadCount"] == 200
    assert result[0]["flowFileRepositoryStorageUsage"]["usedSpace"] == "10 GB"

def test_extract_controller_service_metrics(mock_controller_services):
    """Tests that controller service metrics are extracted correctly."""
    services = mock_controller_services["controllerServices"]
    metric_keys = ["runStatus", "validationStatus"]
    result = extract_controller_service_metrics(services, metric_keys)
    assert len(result) == 1
    assert result[0]["name"] == "StandardSSLContextService"
    assert result[0]["validationStatus"] == "VALID"

def test_extract_reporting_task_metrics(mock_reporting_tasks):
    """Tests that reporting task metrics are extracted correctly."""
    tasks = mock_reporting_tasks["reportingTasks"]
    metric_keys = ["runStatus", "activeThreadCount"]
    result = extract_reporting_task_metrics(tasks, metric_keys)
    assert len(result) == 1
    assert result[0]["name"] == "StandardReportingTask"
    assert result[0]["activeThreadCount"] == 1

def test_extract_bulletin_metrics(mock_bulletin_board):
    """Tests that bulletin metrics are extracted correctly."""
    bulletins = mock_bulletin_board["bulletinBoard"]["bulletins"]
    result = extract_bulletin_metrics(bulletins)
    assert len(result) == 2
    assert result[0]["message"] == "Test Bulletin 1"
    assert result[1]["level"] == "ERROR"

def test_extract_cluster_summary_metrics(mock_cluster_summary):
    """Tests that cluster summary metrics are extracted correctly."""
    cluster_summary = mock_cluster_summary
    result = extract_cluster_summary_metrics(cluster_summary)
    assert len(result) == 4  # 1 overall + 3 nodes
    assert result[0]["id"] == "cluster_summary"
    assert result[0]["connectedNodeCount"] == 2
    # CORRECTED: Use .get() to safely access the key, preventing a KeyError
    # on the summary object which does not have a 'nodeId'.
    node3_metrics = next(item for item in result if item.get("nodeId") == "node3")
    assert node3_metrics["status"] == "DISCONNECTED"

