# NiFi Metrics Analysis Tool

## Overview

The NiFi Metrics Analysis Tool is an interactive command-line interface for troubleshooting and analyzing Apache NiFi data flows. It provides deep insights into system health, performance bottlenecks, data loss, and flow behavior using both standard metrics and provenance data.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Loading Data](#loading-data)
- [Analysis Commands](#analysis-commands)
  - [Basic Health & Status](#basic-health--status)
  - [Provenance Analysis](#provenance-analysis)
  - [Version Management](#version-management)
- [Typical Workflows](#typical-workflows)
- [Provenance Analysis Guide](#provenance-analysis-guide)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r analysis/requirements-analysis.txt

# 2. Start the analysis tool
python analysis/troubleshoot.py

# 3. Load data and analyze
(nifi-troubleshoot)> load 2024-12-16
(nifi-troubleshoot)> health-summary
(nifi-troubleshoot)> dropped-flowfiles
(nifi-troubleshoot)> bottlenecks
```

---

## Installation

### Prerequisites

- Python 3.7+
- Access to collected NiFi metrics (local, S3, or Azure)
- Configuration files: `config/nifi-config.json` and `config/secrets.json`

### Install Analysis Dependencies

```bash
# From the project root
pip install -r analysis/requirements-analysis.txt
```

This installs:
- `pandas` - Data manipulation
- `rich` - Beautiful terminal output
- `prompt_toolkit` - Interactive shell
- Storage clients (boto3, azure-storage-blob)

### Verify Installation

```bash
python analysis/troubleshoot.py
# Should see: "--- NiFi Troubleshooting Tool ---"
```

---

## Loading Data

### Load by Date

```bash
# Load single day (today if no date specified)
(nifi-troubleshoot)> load

# Load specific date
(nifi-troubleshoot)> load 2024-12-16

# Load date range
(nifi-troubleshoot)> load 2024-12-10 2024-12-16
```

**Output:**
```
Loading data for 2024-12-16...
  - Loaded 450 records for nifi_processor (15 files, 0 skipped)
    Versions: 1.1.0
  - Loaded 1250 records for nifi_provenance (5 files, 0 skipped)
    Versions: 1.1.0
Data loaded successfully.
```

### Load Specific Collection

Load all metrics from a single collection run:

```bash
(nifi-troubleshoot)> load-collection 550e8400-e29b-41d4-a716-446655440000
```

**Output:**
```
Loading collection 550e8400-e29b-41d4-a716-446655440000...
  - Loaded 45 nifi_processor records (version 1.1.0)
  - Loaded 120 nifi_connection records (version 1.1.0)
  - Loaded 501 nifi_provenance records (version 1.1.0)

Collection loaded successfully:
  Total records: 666
  Files loaded: 3
```

### Version Validation

Data is automatically validated for schema compatibility:

```bash
(nifi-troubleshoot)> data-versions

=== Data Version Summary ===
Current Tool Version: 1.1.0

Versions by Metric Type:
  nifi_processor: 1.1.0
  nifi_connection: 1.1.0
  nifi_provenance: 1.1.0

✓ All data versions are compatible with this tool.
```

---

## Analysis Commands

### Basic Health & Status

#### `health-summary`
Shows a high-level overview of system health.

```bash
(nifi-troubleshoot)> health-summary
```

**Displays:**
- Processor status counts (Running, Stopped, etc.)
- Top 5 connections by queue size
- JVM heap usage
- Cluster health (if available)

---

#### `list-stopped`
Lists all processors not in RUNNING state.

```bash
(nifi-troubleshoot)> list-stopped
```

**Use when:**
- Checking for stopped flows
- Validating deployment
- Investigating why data isn't flowing

---

#### `back-pressure [threshold]`
Finds queues nearing back pressure threshold.

```bash
(nifi-troubleshoot)> back-pressure          # Default: 80%
(nifi-troubleshoot)> back-pressure 90       # Custom threshold
```

**Use when:**
- System is slowing down
- Investigating flow bottlenecks
- Capacity planning

---

#### `slow-processors [percentile]`
Identifies processors with high average lineage duration.

```bash
(nifi-troubleshoot)> slow-processors        # 90th percentile
(nifi-troubleshoot)> slow-processors 95     # 95th percentile
```

**Use when:**
- Optimizing flow performance
- Finding processing bottlenecks
- Comparing processor efficiency

---

#### `view-bulletins [level]`
Shows recent system bulletins.

```bash
(nifi-troubleshoot)> view-bulletins         # All levels
(nifi-troubleshoot)> view-bulletins ERROR   # Errors only
(nifi-troubleshoot)> view-bulletins WARN    # Warnings only
```

**Use when:**
- Investigating errors
- Checking for warnings
- Understanding system state

---

#### `list-invalid-services`
Lists controller services not in VALID state.

```bash
(nifi-troubleshoot)> list-invalid-services
```

**Use when:**
- Troubleshooting processor issues
- Validating service configuration
- Deployment verification

---

#### `check-reporting-tasks`
Shows status of all reporting tasks.

```bash
(nifi-troubleshoot)> check-reporting-tasks
```

---

#### `cluster-health`
Displays detailed cluster health and node status.

```bash
(nifi-troubleshoot)> cluster-health
```

**Displays:**
- Overall cluster status
- Individual node health
- Active threads per node
- Disk and heap usage per node

---

#### `jvm-heap`
Shows detailed JVM heap and memory metrics.

```bash
(nifi-troubleshoot)> jvm-heap
```

**Displays:**
- Heap used/max
- Heap usage percentage
- Non-heap memory
- Per-node breakdown

---

### Provenance Analysis

Provenance commands provide deep insights into data flow behavior, data loss, and performance.

#### `dropped-flowfiles [time_window] [min_drops]`
**Identifies processors dropping FlowFiles - Critical for data loss detection.**

```bash
(nifi-troubleshoot)> dropped-flowfiles              # Last 60 min, min 5 drops
(nifi-troubleshoot)> dropped-flowfiles 120          # Last 120 minutes
(nifi-troubleshoot)> dropped-flowfiles 60 10        # Last 60 min, min 10 drops
```

**Output Example:**
```
╭─────────────────────────────────────────────────────╮
│ Processors Dropping FlowFiles (>= 5 drops)          │
├─────────────────────────────────────────────────────┤
│ Processor Name     │ Drop Count │ Total Bytes      │
│ ValidateRecord     │     245    │    1,234,567     │
│ RouteOnAttribute   │      87    │      456,789     │
╰─────────────────────────────────────────────────────╯
```

**When to use:**
- ✅ Investigating suspected data loss
- ✅ Validating filtering logic
- ✅ Monitoring data quality issues
- ✅ Finding unexpected drops

---

#### `flow-paths [top_n]`
**Shows common data flow paths through the system.**

```bash
(nifi-troubleshoot)> flow-paths       # Top 10 paths
(nifi-troubleshoot)> flow-paths 20    # Top 20 paths
```

**Output Example:**
```
╭──────────────────────────────────────────────────────────╮
│ Top 10 Data Flow Paths                                   │
├──────────────────────────────────────────────────────────┤
│ Count │ Flow Path                                        │
│  1,234│ GetFile(CREATE) → UpdateAttribute(ATTRIBUTES_...│
│    567│ ConsumeKafka(RECEIVE) → ConvertRecord(CONTENT_..│
╰──────────────────────────────────────────────────────────╯
```

**When to use:**
- ✅ Understanding data flow topology
- ✅ Validating routing logic
- ✅ Documenting data flows
- ✅ Identifying common vs rare paths

---

#### `bottlenecks [percentile]`
**Identifies processing bottlenecks by analyzing event durations.**

```bash
(nifi-troubleshoot)> bottlenecks       # 90th percentile
(nifi-troubleshoot)> bottlenecks 95    # 95th percentile
```

**Output Example:**
```
╭────────────────────────────────────────────────────────╮
│ Processing Bottlenecks (Slowest Processors)            │
├────────────────────────────────────────────────────────┤
│ Processor      │ Events │ Mean  │ 90th %│ 95th %│ Max │
│ ExecuteSQL     │ 1,234  │ 234ms │ 890ms │ 1234ms│5678ms│
│ InvokeHTTP     │   567  │ 156ms │ 456ms │ 678ms │2345ms│
╰────────────────────────────────────────────────────────╯
```

**When to use:**
- ✅ Finding slow processors
- ✅ Optimizing flow performance
- ✅ Capacity planning
- ✅ Comparing processor performance

---

#### `external-transfers`
**Analyzes SEND and RECEIVE events to track data transfers to/from external systems.**

```bash
(nifi-troubleshoot)> external-transfers
```

**Output Example:**
```
📤 Outbound Transfers (SEND)
╭─────────────────────────────────────────────────────────╮
│ Destination            │ Processor  │ Count │ Total Bytes│
│ sftp://partner.com/... │ PutSFTP    │  123  │  1,234,567 │
│ https://api.example... │ InvokeHTTP │   45  │    456,789 │
╰─────────────────────────────────────────────────────────╯

📥 Inbound Transfers (RECEIVE)
╭─────────────────────────────────────────────────────────╮
│ Source                 │ Processor   │ Count │ Total Bytes│
│ kafka://topic1         │ ConsumeKafka│  567  │  5,678,901 │
╰─────────────────────────────────────────────────────────╯
```

**When to use:**
- ✅ Auditing external connections
- ✅ Tracking data volume to partners
- ✅ Compliance and security reviews
- ✅ Identifying integration points

---

#### `trace-flowfile <uuid>`
**Traces the complete lineage of a specific FlowFile.**

```bash
(nifi-troubleshoot)> trace-flowfile 550e8400-e29b-41d4-a716-446655440000
```

**Output Example:**
```
🔍 FlowFile Lineage: 550e8400-e29b-41d4-a716-446655440000

FlowFile: 550e8400-e29b-41d4-a716-446655440000
├── CREATE @ GetFile
│   ├── Time: 2024-12-16 10:30:00
│   ├── Duration: 5ms
│   └── Size: 1,024 bytes
├── ATTRIBUTES_MODIFIED @ UpdateAttribute
│   ├── Time: 2024-12-16 10:30:01
│   ├── Duration: 2ms
│   └── Size: 1,024 bytes
├── CONTENT_MODIFIED @ ConvertRecord
│   ├── Time: 2024-12-16 10:30:05
│   ├── Duration: 234ms
│   └── Size: 2,048 bytes
└── SEND @ PutS3Object
    ├── Time: 2024-12-16 10:30:10
    ├── Duration: 456ms
    └── Size: 2,048 bytes
```

**When to use:**
- ✅ Debugging specific FlowFile issues
- ✅ Understanding why data was dropped
- ✅ Tracing data transformations
- ✅ Audit trails for compliance

**How to find FlowFile UUIDs:**
- Check NiFi UI provenance page
- Look in bulletins for UUIDs
- Use `dropped-flowfiles` command to find dropped UUIDs

---

#### `fork-join-analysis`
**Analyzes data splitting (FORK) and merging (JOIN) patterns.**

```bash
(nifi-troubleshoot)> fork-join-analysis
```

**Output Example:**
```
🔀 Data Splitting and Merging Analysis

FORK Events (Data Splitting):
╭─────────────────────────────────────────────────────╮
│ Processor      │ Fork Count │ Avg Children │ Max   │
│ SplitJson      │    1,234   │     45.2     │  567  │
│ SplitRecord    │      567   │     12.3     │   89  │
╰─────────────────────────────────────────────────────╯

JOIN Events (Data Merging):
╭─────────────────────────────────────────────────────╮
│ Processor      │ Join Count │ Avg Parents  │ Max   │
│ MergeContent   │      234   │      5.6     │   45  │
│ MergeRecord    │       89   │      3.2     │   12  │
╰─────────────────────────────────────────────────────╯
```

**When to use:**
- ✅ Understanding data fan-out patterns
- ✅ Capacity planning for downstream processors
- ✅ Analyzing data aggregation
- ✅ Identifying processors that split data

---

#### `content-modifications [top_n]`
**Shows which processors frequently modify FlowFile content or attributes.**

```bash
(nifi-troubleshoot)> content-modifications       # Top 15
(nifi-troubleshoot)> content-modifications 20    # Top 20
```

**Output Example:**
```
╭─────────────────────────────────────────────────────────╮
│ FlowFile Modification Patterns                          │
├─────────────────────────────────────────────────────────┤
│ Processor       │ Content Mod │ Attributes Mod │ Total │
│ ConvertRecord   │    1,234    │       567      │ 1,801 │
│ UpdateAttribute │       0     │     2,345      │ 2,345 │
│ JoltTransform   │      567    │       123      │   690 │
╰─────────────────────────────────────────────────────────╯
```

**When to use:**
- ✅ Identifying transformation-heavy processors
- ✅ Understanding data enrichment patterns
- ✅ Finding optimization opportunities
- ✅ Validating flow design

---

### Version Management

#### `version-info`
Shows current tool version and supported features.

```bash
(nifi-troubleshoot)> version-info
```

**Output:**
```
=== NiFi Troubleshooting Tool Version Info ===
Current Schema Version: 1.1.0
Release Date: 2024-12-16

Supported Features:
  ✓ Provenance data collection
  ✓ Event tracking and lineage
  ...

Supported Metric Types:
  - nifi_processor
  - nifi_connection
  - nifi_provenance
  ...
```

---

#### `data-versions`
Displays versions of all loaded data.

```bash
(nifi-troubleshoot)> data-versions
```

---

#### `validate-versions`
Re-validates all loaded data against current schema.

```bash
(nifi-troubleshoot)> validate-versions
```

---

## Typical Workflows

### Workflow 1: Investigating Data Loss

```bash
# 1. Load recent data
(nifi-troubleshoot)> load 2024-12-16

# 2. Check for dropped FlowFiles
(nifi-troubleshoot)> dropped-flowfiles

# Output shows: ValidateRecord dropping 245 FlowFiles

# 3. Get a UUID from the bulletin or use one found
(nifi-troubleshoot)> trace-flowfile <uuid-from-bulletins>

# 4. Check related errors
(nifi-troubleshoot)> view-bulletins ERROR

# 5. Review processor status
(nifi-troubleshoot)> health-summary

# Result: Found schema validation errors, fix schema
```

---

### Workflow 2: Performance Investigation

```bash
# 1. Load data
(nifi-troubleshoot)> load 2024-12-16

# 2. Overall health check
(nifi-troubleshoot)> health-summary

# 3. Find slow processors (two methods)
(nifi-troubleshoot)> slow-processors
(nifi-troubleshoot)> bottlenecks

# Output shows: ExecuteSQL taking 5+ seconds

# 4. Understand flow paths
(nifi-troubleshoot)> flow-paths

# 5. Check for backpressure
(nifi-troubleshoot)> back-pressure

# Result: Optimize SQL query, add connection pooling
```

---

### Workflow 3: Compliance Audit

```bash
# 1. Load relevant time period
(nifi-troubleshoot)> load 2024-12-01 2024-12-16

# 2. Document external connections
(nifi-troubleshoot)> external-transfers

# 3. Trace sensitive data FlowFile
(nifi-troubleshoot)> trace-flowfile <sensitive-data-uuid>

# 4. Show transformations
(nifi-troubleshoot)> content-modifications

# 5. Verify no unexpected drops
(nifi-troubleshoot)> dropped-flowfiles

# Result: Complete audit trail documentation
```

---

### Workflow 4: Flow Validation

```bash
# 1. Load data from test run
(nifi-troubleshoot)> load 2024-12-16

# 2. Verify data paths match design
(nifi-troubleshoot)> flow-paths

# 3. Check for unexpected drops
(nifi-troubleshoot)> dropped-flowfiles

# 4. Verify processors running
(nifi-troubleshoot)> list-stopped

# 5. Check split/merge logic
(nifi-troubleshoot)> fork-join-analysis

# Result: Flow behaves as designed
```

---

## Provenance Analysis Guide

### What is Provenance Data?

Provenance data tracks the complete history and lineage of every FlowFile as it moves through your NiFi system. Each event records:

- **What happened**: CREATE, RECEIVE, SEND, DROP, ROUTE, FORK, JOIN, etc.
- **Where**: Which processor/component
- **When**: Precise timestamp
- **How long**: Event duration
- **Relationships**: Parent and child FlowFiles
- **Context**: Transit URIs, file sizes, attributes

### Event Types

| Event Type | Description | Use Case |
|------------|-------------|----------|
| CREATE | FlowFile created | Track data origin |
| RECEIVE | Received from external system | Monitor inbound data |
| SEND | Sent to external system | Track outbound data |
| DROP | FlowFile removed/dropped | Detect data loss |
| ROUTE | Routed to relationship | Understand routing |
| FORK | Split into children | Track data fan-out |
| JOIN | Merged from parents | Track aggregation |
| CLONE | Duplicated | Track copies |
| CONTENT_MODIFIED | Content changed | Track transformations |
| ATTRIBUTES_MODIFIED | Attributes changed | Track metadata changes |

### Configuration

Enable provenance collection in `nifi-config.json`:

```json
{
  "components_to_monitor": [
    "Processor",
    "Connection",
    "Provenance"
  ],
  
  "collection_intervals_seconds": {
    "Provenance": 300
  },
  
  "provenance_config": {
    "lookback_minutes": 5,
    "max_results": 1000
  }
}
```

### Flow-Specific Configuration

Monitor specific flows with custom settings:

```json
{
  "flows_to_monitor": [
    {
      "name": "critical_data_flow",
      "process_group_id": "abc123",
      "components_to_monitor": ["Processor", "Provenance"],
      "provenance_config": {
        "lookback_minutes": 10,
        "max_results": 500,
        "event_type": "DROP"
      }
    }
  ]
}
```

### Best Practices

**Collection:**
- Use appropriate lookback windows for your data volume
- Limit max_results to balance detail and performance
- Filter by event_type only when needed
- Collect all event types for comprehensive analysis

**Analysis:**
- Start with `health-summary` for overall view
- Use `dropped-flowfiles` regularly for monitoring
- Cross-reference provenance with standard metrics
- Save interesting FlowFile UUIDs for later reference

**Performance:**
- Adjust time windows based on data volume
- Use shorter lookbacks for high-volume systems
- Consider flow-specific monitoring for critical flows
- Balance collection frequency with system load

---

## Advanced Usage

### Programmatic Access

Load data programmatically:

```python
from analysis.lib.data_loader import load_all_data
from analysis.lib.provenance_analysis import analyze_dropped_flowfiles

# Load data
config = load_config()
secrets = load_secrets()
data = load_all_data(config, secrets, "2024-12-16")

# Run analysis
analyze_dropped_flowfiles(data, time_window_minutes=120)

# Access raw DataFrames
prov_df = data.get('nifi_provenance')
dropped = prov_df[prov_df['event_type'] == 'DROP']
print(dropped.head())
```

### Custom Analysis

Create custom queries:

```python
import pandas as pd

# Load data
data = load_all_data(config, secrets, "2024-12-16")
prov_df = data['nifi_provenance']

# Custom analysis: Drops by hour
prov_df['event_time'] = pd.to_datetime(prov_df['event_time'], unit='ms')
dropped = prov_df[prov_df['event_type'] == 'DROP']
by_hour = dropped.groupby(dropped['event_time'].dt.hour).size()
print(by_hour)

# Custom analysis: Average processing time by processor
prov_df['event_duration'] = pd.to_numeric(prov_df['event_duration'], errors='coerce')
avg_duration = prov_df.groupby('component_name')['event_duration'].mean().sort_values(ascending=False)
print(avg_duration.head(10))
```

### Scripting

Automate analysis:

```bash
#!/bin/bash
# analyze_daily.sh - Daily analysis script

python3 << 'EOF'
from analysis.lib.data_loader import load_all_data
from lib.config_loader import load_config, load_secrets

config = load_config()
secrets = load_secrets()
data = load_all_data(config, secrets, "$(date +%Y-%m-%d)")

# Check for drops
prov_df = data.get('nifi_provenance')
if prov_df is not None:
    drops = prov_df[prov_df['event_type'] == 'DROP']
    if len(drops) > 10:
        print(f"ALERT: {len(drops)} FlowFiles dropped today!")
EOF
```

---

## Troubleshooting

### "No data loaded"

**Problem**: Commands return "No data loaded"

**Solutions:**
1. Use `load` command first: `load 2024-12-16`
2. Check storage location has data
3. Verify date format: YYYY-MM-DD
4. Check secrets.json for correct storage credentials

---

### "No provenance data loaded"

**Problem**: Provenance commands return no data

**Solutions:**
1. Check `"Provenance"` is in `components_to_monitor` in config
2. Run collector: `python bin/run_collector.py --once`
3. Check storage: `ls /tmp/nifi_metrics/nifi_provenance-metrics/`
4. Verify date has provenance data

---

### "FlowFile not found"

**Problem**: `trace-flowfile` can't find UUID

**Solutions:**
1. Verify UUID is correct (no typos)
2. Check loaded date range includes that FlowFile
3. FlowFile might be older than lookback window
4. Use `dropped-flowfiles` to find other UUIDs

---

### Slow Performance

**Problem**: Commands are slow

**Solutions:**
1. Load smaller date ranges
2. Use `load-collection` for specific collections
3. Reduce time windows: `dropped-flowfiles 30`
4. Increase thresholds: `dropped-flowfiles 60 10`

---

### Version Errors

**Problem**: "Incompatible schema version"

**Solutions:**
1. Check tool version: `version-info`
2. Update analysis tool: `git pull && pip install -e .`
3. Check data versions: `data-versions`
4. Use `validate-versions` to see details

---

## Command Reference

### Quick Reference Table

| Category | Command | Quick Description |
|----------|---------|-------------------|
| **Loading** | `load [start] [end]` | Load metrics by date |
| | `load-collection <id>` | Load specific collection |
| **Health** | `health-summary` | Overall health view |
| | `list-stopped` | Find stopped processors |
| | `back-pressure [%]` | Find queue backups |
| | `slow-processors [%]` | Find slow processors |
| | `view-bulletins [lvl]` | View system messages |
| | `list-invalid-services` | Find invalid services |
| | `check-reporting-tasks` | Check reporting tasks |
| | `cluster-health` | Cluster status |
| | `jvm-heap` | JVM memory |
| **Provenance** | `dropped-flowfiles` | Find data loss |
| | `flow-paths` | Common data paths |
| | `bottlenecks` | Processing slowness |
| | `external-transfers` | External send/receive |
| | `trace-flowfile <uuid>` | FlowFile lineage |
| | `fork-join-analysis` | Split/merge patterns |
| | `content-modifications` | Transformations |
| **Version** | `version-info` | Tool version info |
| | `data-versions` | Data version info |
| | `validate-versions` | Check compatibility |
| **Other** | `help` | Show all commands |
| | `exit` or `quit` | Exit tool |

---

## Summary

The NiFi Metrics Analysis Tool provides comprehensive troubleshooting capabilities:

✅ **Health Monitoring** - Overall system status and component health
✅ **Performance Analysis** - Identify bottlenecks and slow processors  
✅ **Data Loss Detection** - Find dropped FlowFiles immediately
✅ **Flow Visualization** - Understand actual data paths
✅ **Compliance** - Complete audit trails and lineage
✅ **Version Management** - Track schema compatibility

### Key Benefits

- **Fast Troubleshooting**: Minutes instead of hours
- **Proactive Monitoring**: Catch issues before users complain
- **Data-Driven Decisions**: Real metrics, not guesses
- **Complete Visibility**: From creation to delivery
- **Easy to Use**: Interactive shell with help

### Getting Help

- Type `help` in the tool for command list
- See `PROVENANCE_ANALYSIS_GUIDE.md` for detailed examples
- Check `README.md` for collector setup
- Review `VERSIONING.md` for version details

---

**Ready to troubleshoot?**

```bash
python analysis/troubleshoot.py
(nifi-troubleshoot)> help
```
