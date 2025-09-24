import pytest
import requests

@pytest.fixture
def mock_processor_list():
    """Provides a mock response for the /processors endpoint."""
    return {
        "processors": [
            {
                "component": {"id": "proc-id-1", "name": "GenerateFlowFile", "type": "GenerateFlowFile"},
                "status": {"aggregateSnapshot": {"runStatus": "RUNNING", "activeThreadCount": 2, "nifi_amount_bytes_written": 1024, "nifi_amount_items_output": 10}}
            },
            {
                "component": {"id": "proc-id-2", "name": "LogAttribute", "type": "LogAttribute"},
                "status": {"aggregateSnapshot": {"runStatus": "STOPPED", "activeThreadCount": 0, "nifi_amount_bytes_written": 0, "nifi_amount_items_output": 0}}
            }
        ]
    }

@pytest.fixture
def mock_connection_list():
    """Provides a mock response for the /connections endpoint."""
    return {
        "connections": [
            {
                "id": "conn-id-1",
                "component": {"id": "conn-id-1", "name": "success"},
                "status": {"aggregateSnapshot": {"queuedCount": "100", "queuedSize": "100 KB", "bytesIn": 20000, "backPressureObjectThreshold": 10000}}
            }
        ]
    }

@pytest.fixture
def mock_system_diagnostics():
    """Provides a mock response for the /system-diagnostics endpoint with detailed metrics."""
    return {
        "systemDiagnostics": {
            "aggregateSnapshot": {
                "heapUsed": "1.2 GB", "heapUsage": "30%", "maxHeap": "4 GB", "totalHeap": "4 GB",
                "nonHeapUsed": "3.2 GB", "nonHeapUsage": ".8 GB", "threadCount": 200, "daemonThreadCount": 150,
                "uptime": "680 sec", "processorLoadAverage": 0.55,
                "flowFileRepositoryStorageUsage": {"usedSpace": "10 GB"},
                "contentRepositoryStorageUsage": [{"usedSpace": "50 GB", "identifier": "repo1"}]
            }
        }
    }

@pytest.fixture
def mock_controller_services():
    """Provides a mock response for the controller-services endpoint."""
    return {
        "controllerServices": [
            {
                "component": {"id": "cs-id-1", "name": "StandardSSLContextService", "type": "StandardSSLContextService"},
                "status": {"runStatus": "ENABLED", "validationStatus": "VALID"}
            }
        ]
    }

@pytest.fixture
def mock_reporting_tasks():
    """Provides a mock response for the reporting-tasks endpoint."""
    return {
        "reportingTasks": [
            {
                "component": {"id": "rt-id-1", "name": "StandardReportingTask", "type": "StandardReportingTask"},
                "status": {"runStatus": "RUNNING", "activeThreadCount": 1}
            }
        ]
    }

@pytest.fixture
def mock_bulletin_board():
    """Provides a mock response for the bulletin-board endpoint."""
    return {
        "bulletinBoard": {
            "bulletins": [
                {"id": 1, "message": "Test Bulletin 1", "level": "INFO"},
                {"id": 2, "message": "Test Bulletin 2", "level": "ERROR"}
            ]
        }
    }

@pytest.fixture
def mock_cluster_summary():
    """Provides a mock response for the cluster/summary endpoint."""
    return {
        "clusterSummary": {
            "clustered": True, "connectedToCluster": True, "totalNodeCount": 3,
            "connectedNodeCount": 2, "disconnectedNodeCount": 1,
            "nodes": [
                {"nodeId": "node1", "status": "CONNECTED", "activeThreadCount": 10, "queued": "100 (100 MB)", "diskUsage": [{"freeSpace": "100 GB"}], "heapUsage": "50%"},
                {"nodeId": "node2", "status": "CONNECTED", "activeThreadCount": 12, "queued": "50 (50 MB)", "diskUsage": [{"freeSpace": "120 GB"}], "heapUsage": "45%"},
                {"nodeId": "node3", "status": "DISCONNECTED", "activeThreadCount": 0, "queued": "0 (0 MB)", "diskUsage": [{"freeSpace": "0 GB"}], "heapUsage": "0%"}
            ]
        }
    }

