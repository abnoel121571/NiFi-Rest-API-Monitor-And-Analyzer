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

## 🔍 Part 2: Interactive Troubleshooting Tool

The `troubleshoot.py` script provides an interactive CLI to load and analyze the JSON metrics generated by the collector.

#### 1. Install Analysis Dependencies
```bash
# From your activated virtual environment
pip install -r analysis/requirements-analysis.txt
```

#### 2. Run the Analysis Tool
```bash
python analysis/troubleshoot.py
```

The troubleshooting tool can help you:
- Load and inspect metrics from specific time periods
- Identify performance bottlenecks
- Analyze queue buildup and backpressure events
- Review provenance data for dropped or modified FlowFiles
- Correlate metrics across multiple components

---

## 📈 Output Structure

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
└── ... (other metric types)
```

Each JSON file is gzip-compressed and contains:
- `collection_id`: Unique identifier for the collection run
- `hostname`: The NiFi node that was monitored
- `collection_timestamp`: ISO-formatted UTC timestamp
- Metric-specific data fields

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

