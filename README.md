# NiFi REST API Monitor

A modular Python application to collect, monitor, and store a wide range of Apache NiFi metrics via the REST API. It is designed for clustered environments and provides detailed insights into the health and performance of your data flows.

### Key Features:
- **Designed for NiFi Clusters**: Uses a "Distributed Agent" model with a templated configuration for easy deployment.
- **Flexible Storage Options**: Write metrics to **AWS S3**, **Azure Blob Storage**, or the **Local File System**.
- **Dynamic & Granular Scheduling**: Set unique collection intervals for each metric type and update them on the fly.
- **Targeted Monitoring**: Monitor all components, specific flows (Process Groups), or even individual processors by name.
- **Provenance Data Collection**: Track FlowFile lineage, audit data movement, and identify dropped or modified data.
- **Interactive Troubleshooting CLI**: An analysis tool to load and inspect collected metrics for point-in-time diagnostics.
- **Comprehensive Unit Tests**: Includes a `pytest` suite to ensure reliability and prevent regressions.

---

## 🚀 Deployment Model: Distributed Agent

This monitor is designed to run as a **distributed agent**, which is the recommended pattern for monitoring a NiFi cluster. An instance of the script is deployed on **every node** in the cluster.

---

## 🚀 Install the python project: 

```bash
pip install -e .
```

---

## 📦 Project Structure
```
nifi_metrics_collector/
├── bin/
│   └── run_collector.py       # Main entrypoint & scheduler
├── lib/
│   ├── config_loader.py       # Configuration file loaders
│   ├── nifi_client.py         # NiFi REST API client
│   ├── metrics_parser.py      # Metric extraction logic
│   ├── nifi_auth.py           # Authentication handlers
│   ├── storage_writer.py      # Multi-backend storage writer
│   └── system_metrics.py      # OS-level metrics collection
├── config/
│   ├── nifi-config.json       # Templated NiFi connection and metric settings
│   └── secrets.json           # Credentials & storage settings
├── tests/
│   └── ... (Test files)
├── analysis/
│   ├── lib/
│   │   └── ... (Core logic modules)
│   └── troubleshoot.py        # Analysis script for adhoc investigation
├── docs/                      # Supporting Documentation
│   ├── versions/
│   ├── provenance/
├── pyproject.toml             # Project definition
└── README.md
```

---

## ⚙️ Configuration

#### 1. `config/nifi-config.json`
This file acts as a **template**. You can use the same file across all nodes. The `{hostname}` placeholder will be dynamically replaced by the `--hostname` argument passed to the `run_collector.py` script at runtime.

```json
{
  "nifi_api_url": "https://{hostname}:8443/nifi-api",
  "nifi_token_url": "https://{hostname}:8443/nifi-api/access/token",
  "use_token_auth": true,
  "nifi_token_lifetime_seconds": 43200,
  "nifi_timeout_seconds": 10,
  "nifi_provenance_timeout_seconds": 60,
  "log_level": "INFO",

  "collection_intervals_seconds": {
    "global_default": 300,
    "Processor": 120,
    "Connection": 120,
    "ControllerServices": 600,
    "ReportingTasks": 600,
    "Bulletins": 60,
    "SystemDiagnostics": 3600,
    "System": 180,
    "Provenance": 300
  },

  "components_to_monitor": [
    "Processor",
    "Connection",
    "ControllerServices",
    "ReportingTasks",
    "Bulletins",
    "SystemDiagnostics",
    "System",
    "Provenance"
  ],
  
  "monitored_processor_names": [],
  
  "provenance_config": {
    "lookback_minutes": 5,
    "max_results": 1000
  },
  
  "flows_to_monitor": [
    {
      "name": "critical_data_flow",
      "process_group_id": "abc123-process-group-id",
      "interval_seconds": 300,
      "components_to_monitor": ["Processor", "Connection", "Provenance"],
      "monitored_processor_names": ["ProcessorA", "ProcessorB"],
      "provenance_config": {
        "lookback_minutes": 10,
        "max_results": 500,
        "event_type": "DROP"
      }
    }
  ]
}
```

#### 2. `config/secrets.json`
This file should be the **same across all nodes** to ensure they all write to the same central storage location.

```json
{
  "nifi_username": "your-nifi-user-name",
  "nifi_password": "your-nifi-user-password",
  "aws_access_key": "your-aws-key",
  "aws_secret_key": "your-aws-secret-key",
  "azure_connection_string": "your-azure-connection-string",
  "storage": "aws",
  "s3_bucket": "your-nifi-metrics-bucket",
  "local_output_directory": "/path/to/your/metrics/output"
}
```

---

## 📊 Collected Metrics

### Core Metrics
- **Processor Metrics**: Throughput, active threads, bytes read/written, lineage duration
- **Connection Metrics**: Queue counts, sizes, and backpressure thresholds
- **System Diagnostics**: JVM heap usage, thread counts
- **Controller Services**: Run status, validation status, active threads
- **Reporting Tasks**: Run status and active threads
- **Bulletins**: System alerts and error messages
- **System Metrics**: CPU, memory, disk usage and I/O statistics

### Provenance Data (NEW!)
Track the complete history and lineage of FlowFiles as they move through your data flows:

- **Event Types**: CREATE, RECEIVE, SEND, DROP, ROUTE, FORK, JOIN, CLONE, CONTENT_MODIFIED, ATTRIBUTES_MODIFIED
- **Lineage Tracking**: Parent/child FlowFile relationships
- **Transit Information**: URIs and destinations for SEND/RECEIVE events
- **File Metadata**: Sizes, durations, timestamps
- **Component Context**: Which processor generated each event
- **Audit Trail**: Complete history for compliance and debugging

#### Provenance Configuration Options

```json
"provenance_config": {
  "lookback_minutes": 5,        // Time window to query (default: 5)
  "max_results": 1000,           // Maximum events to retrieve (default: 1000)
  "event_type": "DROP",          // Optional: filter by event type
  "component_id": "proc-abc123"  // Optional: filter by specific component
}
```

#### Common Use Cases for Provenance

1. **Data Loss Investigation**: Filter by `DROP` events to find where data is being removed
2. **External Transfer Auditing**: Track `SEND` and `RECEIVE` events for compliance
3. **Performance Analysis**: Use `event_duration` to identify slow processing
4. **Debugging Specific Processors**: Filter by `component_id` to isolate issues
5. **Lineage Verification**: Trace parent/child relationships to validate data transformations

---

## 🚀 Part 1: Metric Collection

The following steps should be performed on each node in the NiFi cluster.

#### 1. Install Collector
```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the project in editable mode
pip install -e .
```

#### 2. Run the Collector
Use the `--hostname` argument to specify which NiFi instance to monitor.

```bash
# For the distributed agent model, run on each node pointing to itself (default)
python bin/run_collector.py

# Explicitly pointing to localhost
python bin/run_collector.py --hostname localhost

# To monitor a remote node from a central server
python bin/run_collector.py --hostname nifi-node-01.your.domain.com

# Run once for debugging
python bin/run_collector.py --hostname localhost --once

# Override log level
python bin/run_collector.py --hostname localhost --log-level DEBUG
```

---

## 🔍 Part 2: Analysis & Troubleshooting

The analysis tool provides an interactive CLI for troubleshooting and analyzing collected metrics.

### Quick Start

```bash
# Install analysis dependencies
pip install -r analysis/requirements-analysis.txt

# Start the analysis tool
python analysis/troubleshoot.py

# Load data and analyze
(nifi-troubleshoot)> load 2024-12-16
(nifi-troubleshoot)> health-summary
(nifi-troubleshoot)> dropped-flowfiles
```

### Available Features

- **Health Monitoring**: System status, processor health, queue analysis
- **Performance Analysis**: Bottleneck detection, slow processor identification
- **Provenance Analysis**: Data loss detection, flow path visualization, lineage tracing
- **Cluster Management**: Node health, JVM metrics, cluster status
- **Version Management**: Schema compatibility, data validation

### Full Documentation

**See [README_ANALYSIS.md](README_ANALYSIS.md) for complete analysis documentation including:**
- Detailed command reference
- Provenance analysis guide
- Troubleshooting workflows
- Advanced usage examples
- Best practices

### Example Session

```bash
(nifi-troubleshoot)> load 2024-12-16
Loading data for 2024-12-16...
  - Loaded 450 records for nifi_processor
  - Loaded 1250 records for nifi_provenance
Data loaded successfully.

(nifi-troubleshoot)> health-summary
--- NiFi Health Summary ---
Processor Status: 45 Running, 0 Stopped
Top Queue: connection_abc (1,234 FlowFiles)

(nifi-troubleshoot)> dropped-flowfiles
Processors Dropping FlowFiles:
  ValidateRecord: 245 drops (1.2 MB)
  
(nifi-troubleshoot)> help
# Shows all available commands
```

### Programmatic File Loading

The analysis tool includes a `FileReader` utility for loading versioned metric files:

```python
from pathlib import Path
from lib.file_reader import FileReader

# Initialize reader
reader = FileReader(min_supported_version="1.0.0")

# Find files by criteria
files = reader.find_collection_files(
    base_path=Path("/tmp/nifi_metrics"),
    metric_type="nifi_processor",
    date="2024-12-16"
)

# Load a specific collection by ID
collection = reader.load_collection(
    base_path=Path("/tmp/nifi_metrics"),
    collection_id="550e8400-e29b-41d4-a716-446655440000",
    validate_versions=True
)

# Access the data
processor_metrics = collection["metrics"]["nifi_processor"]
manifest = collection["manifest"]
versions = collection["versions"]

# Read individual files
data, version = reader.read_and_validate(Path("path/to/file.json.gz"))
```

### Version Checking

Check schema version information:

```bash
# From Python
python -c "from lib.file_reader import print_version_info; print_version_info()"
```

Output:
```
=== Schema Version Information ===
Current Version: 1.1.0
Release Date: 2024-12-16

Changes:
  - Added Provenance data collection
  - Added provenance event tracking
  - Added lineage and relationship information
  - Added event type filtering support

Supported Metric Types:
  - nifi_processor
  - nifi_connection
  - nifi_jvm
  - nifi_controller_service
  - nifi_reporting_task
  - nifi_bulletin
  - nifi_provenance
  - system
========================================
```

---

## 📈 Output Structure & Versioning

### Directory Structure

Metrics are organized in storage with the following structure:

```
<storage-location>/
├── nifi_processor-metrics/
│   └── 2024-12-16/
│       └── hostname_nifi_processor_<uuid>.json.gz
├── nifi_connection-metrics/
│   └── 2024-12-16/
│       └── hostname_nifi_connection_<uuid>.json.gz
├── nifi_provenance-metrics/
│   └── 2024-12-16/
│       └── hostname_nifi_provenance_<uuid>.json.gz
├── nifi_jvm-metrics/
│   └── 2024-12-16/
│       └── hostname_nifi_jvm_<uuid>.json.gz
├── system-metrics/
│   └── 2024-12-16/
│       └── hostname_system_<uuid>.json.gz
├── manifests/
│   └── 2024-12-16/
│       └── hostname_manifest_<uuid>.json.gz
└── ... (other metric types)
```

### File Format & Metadata

Each JSON file is gzip-compressed and contains an array of metric objects. Every metric object includes:

- `collection_id`: Unique identifier for the collection run (UUID)
- `hostname`: The NiFi node that was monitored
- `collection_timestamp`: ISO-formatted UTC timestamp
- `schema_version`: Schema version of the data format (e.g., "1.1.0")
- Metric-specific data fields

**Example metric entry:**
```json
{
  "collection_id": "550e8400-e29b-41d4-a716-446655440000",
  "hostname": "nifi-node-01.example.com",
  "collection_timestamp": "2024-12-16T10:30:00.000000",
  "schema_version": "1.1.0",
  "id": "processor-abc123",
  "name": "ConvertRecord",
  "type": "org.apache.nifi.processors.standard.ConvertRecord",
  "runStatus": "Running",
  "nifi_amount_bytes_written": 1048576
}
```

### Manifest Files

Each collection includes a manifest file that provides metadata about what was collected:

```json
{
  "manifest_version": "1.0",
  "collection_id": "550e8400-e29b-41d4-a716-446655440000",
  "hostname": "nifi-node-01.example.com",
  "collection_timestamp": "2024-12-16T10:30:00.000000",
  "schema_version": "1.1.0",
  "metric_types": {
    "nifi_processor": {
      "record_count": 45,
      "has_flow_name": true
    },
    "nifi_provenance": {
      "record_count": 1001,
      "has_flow_name": false
    }
  },
  "total_records": 1046
}
```

### Schema Versioning

The output format uses semantic versioning (MAJOR.MINOR.PATCH) to track schema changes:

#### Version History

**v1.1.0** (Current - 2024-12-16)
- Added Provenance data collection
- Added event tracking and lineage information
- Backward compatible with v1.0.0

**v1.0.0** (Initial - 2024-12-01)
- Initial release with core metrics
- Processor, Connection, JVM, Controller Services, Reporting Tasks, Bulletins, System metrics

#### Version Compatibility

The analysis tool (`troubleshoot.py`) automatically validates schema versions when loading files:

- **Compatible versions**: Files with versions between the minimum supported version and current version
- **Legacy files**: Files without version information are assumed to be v1.0.0
- **Future versions**: Files with versions newer than the tool's current version will be rejected

To check version compatibility programmatically:

```python
from lib.version import is_version_compatible, get_schema_version

current_version = get_schema_version()  # Returns "1.1.0"
is_compatible = is_version_compatible("1.0.0")  # Returns True
```

### Schema Evolution & Migration

When upgrading between versions:

1. **Backward Compatibility**: New versions maintain backward compatibility within the same major version (e.g., 1.0.0 → 1.1.0)
2. **Analysis Tool**: Update your analysis tool before updating collectors to ensure compatibility
3. **Mixed Versions**: The system can handle metrics from different schema versions simultaneously
4. **Version Filtering**: Use the FileReader to filter files by version if needed

```python
from lib.version import get_migration_path

# Get versions between two releases
versions = get_migration_path("1.0.0", "1.1.0")
# Returns: ["1.0.0", "1.1.0"]
```

**Breaking Changes** (major version bumps) will be clearly documented and require:
- Migration scripts (if provided)
- Updated analysis tools
- Potential reprocessing of historical data

---

## ⚡ Performance Considerations

### Provenance Queries
Provenance queries can be resource-intensive. Consider these best practices:

- **Collection Intervals**: Don't set intervals too low (recommended: 300+ seconds)
- **Lookback Windows**: Use shorter windows (5-10 minutes) for high-volume flows
- **Result Limits**: Keep `max_results` under 1000 for most use cases
- **Event Filtering**: Use `event_type` or `component_id` filters to reduce result size
- **Timeout Settings**: Increase `nifi_provenance_timeout_seconds` if queries timeout

### General Tips
- Use flow-specific monitoring for critical process groups
- Monitor only necessary processors using `monitored_processor_names`
- Adjust collection intervals based on your monitoring needs
- Use local storage for testing, cloud storage for production

---

## 🔒 Security Notes

- SSL verification is disabled by default for self-signed certificates
- Store credentials securely in `secrets.json` with appropriate file permissions
- Use token-based authentication for production environments
- Tokens auto-renew 10 minutes before expiration
- Consider using environment variables or secret management systems for sensitive data

---

## ✅ Testing

Run the test suite to ensure everything is working correctly:

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest tests/

# Run with verbose output
pytest -v tests/

# Run specific test file
pytest tests/test_metrics_parser.py
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: `Failed to acquire initial token`
- **Solution**: Verify credentials in `secrets.json` and ensure NiFi is accessible

**Issue**: `Provenance query timed out`
- **Solution**: Increase `nifi_provenance_timeout_seconds` or reduce `lookback_minutes`

**Issue**: `No valid JVM snapshot found`
- **Solution**: Check if NiFi is in a clustered configuration and review API response format

**Issue**: Storage write failures
- **Solution**: Verify AWS/Azure credentials and bucket/container permissions

### Debug Mode

Enable debug logging for detailed information:

```bash
python bin/run_collector.py --hostname localhost --log-level DEBUG
```

---

## 📝 License

[Add your license information here]

---

## 🤝 Contributing

Contributions are welcome! Please ensure all tests pass before submitting pull requests.

---

## 📧 Support

[Add your support contact information here]
