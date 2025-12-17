# Provenance Analysis Guide

## Overview

The provenance analysis features provide deep insights into how data flows through your NiFi system, helping you identify data loss, bottlenecks, and performance issues that traditional metrics alone cannot reveal.

## What is Provenance Data?

Provenance data tracks the complete history and lineage of every FlowFile as it moves through your NiFi data flows. Each event records:

- **What happened**: CREATE, RECEIVE, SEND, DROP, ROUTE, FORK, JOIN, etc.
- **Where**: Which processor/component
- **When**: Precise timestamp
- **How long**: Event duration
- **Relationships**: Parent and child FlowFiles
- **Context**: Transit URIs, file sizes, attributes

## Available Analysis Commands

### 1. 🚨 dropped-flowfiles - Data Loss Detection

**Purpose**: Identifies processors that are dropping FlowFiles, which could indicate data loss or filtering logic issues.

**Usage**:
```
(nifi-troubleshoot)> dropped-flowfiles
(nifi-troubleshoot)> dropped-flowfiles 120          # Last 120 minutes
(nifi-troubleshoot)> dropped-flowfiles 60 10        # Last 60 min, min 10 drops
```

**Parameters**:
- `time_window_minutes` (default: 60): Look back this many minutes
- `min_drops` (default: 5): Minimum number of drops to report

**What it shows**:
- Processor name dropping FlowFiles
- Number of FlowFiles dropped
- Total bytes of data dropped
- Common reason for drops

**When to use**:
- ✅ Investigating suspected data loss
- ✅ Validating filtering logic
- ✅ Checking if RouteOnAttribute is dropping data unexpectedly
- ✅ Monitoring data quality issues

**Example output**:
```
╭─────────────────────────────────────────────────────╮
│ Processors Dropping FlowFiles (>= 5 drops)          │
├─────────────────────────────────────────────────────┤
│ Processor Name     │ Drop Count │ Total Bytes Dropped │
│ ValidateRecord     │     245    │      1,234,567      │
│ RouteOnAttribute   │      87    │        456,789      │
│ UpdateAttribute    │      12    │         23,456      │
╰─────────────────────────────────────────────────────╯
```

**Interpretation**:
- High drop counts on ValidateRecord → Data quality issues
- Drops on RouteOnAttribute → Check routing logic
- Unexpected drops → Potential bugs or misconfigurations

---

### 2. 🔀 flow-paths - Data Flow Visualization

**Purpose**: Shows the most common paths FlowFiles take through your system.

**Usage**:
```
(nifi-troubleshoot)> flow-paths
(nifi-troubleshoot)> flow-paths 20      # Top 20 paths
```

**What it shows**:
- How many FlowFiles followed each path
- Sequence of processors traversed
- Event types at each step

**When to use**:
- ✅ Understanding data flow topology
- ✅ Identifying common vs rare paths
- ✅ Validating routing logic
- ✅ Documenting data flows

**Example output**:
```
╭──────────────────────────────────────────────────────────╮
│ Top 10 Data Flow Paths                                   │
├──────────────────────────────────────────────────────────┤
│ Count │ Flow Path                                        │
│  1,234│ GetFile(CREATE) → UpdateAttribute(ATTRIBUTES_...│
│    567│ ConsumeKafka(RECEIVE) → ConvertRecord(CONTENT_..│
│    234│ ListS3(CREATE) → FetchS3(CONTENT_MODIFIED) → ...│
╰──────────────────────────────────────────────────────────╯
```

**Interpretation**:
- High count paths → Main data flows
- Low count paths → Edge cases or errors
- Unexpected paths → Routing issues

---

### 3. ⏱️ bottlenecks - Performance Bottlenecks

**Purpose**: Identifies processors that take the longest to process FlowFiles using event duration data.

**Usage**:
```
(nifi-troubleshoot)> bottlenecks
(nifi-troubleshoot)> bottlenecks 95     # Show 95th percentile
```

**What it shows**:
- Mean processing time per processor
- 90th and 95th percentile times
- Maximum processing time observed
- Number of events analyzed

**When to use**:
- ✅ Finding slow processors
- ✅ Optimizing flow performance
- ✅ Capacity planning
- ✅ Comparing processor performance

**Example output**:
```
╭────────────────────────────────────────────────────────╮
│ Processing Bottlenecks (Slowest Processors)            │
├────────────────────────────────────────────────────────┤
│ Processor      │ Events │ Mean  │ 90th %│ 95th %│ Max │
│ ExecuteSQL     │ 1,234  │ 234.5 │ 890.2 │ 1234.5│ 5678│
│ InvokeHTTP     │   567  │ 156.7 │ 456.3 │  678.9│ 2345│
│ ConvertRecord  │ 2,345  │  45.6 │ 123.4 │  234.5│  567│
╰────────────────────────────────────────────────────────╯
```

**Interpretation**:
- High mean → Consistently slow
- High 95th percentile → Occasional slowdowns
- High max → Extreme outliers
- Consider: Database queries, API calls, transformations

---

### 4. 🌐 external-transfers - External System Analysis

**Purpose**: Tracks data being sent to or received from external systems.

**Usage**:
```
(nifi-troubleshoot)> external-transfers
```

**What it shows**:
- **Outbound (SEND)**: Where data is being sent
- **Inbound (RECEIVE)**: Where data is coming from
- Transfer volumes and destinations
- Which processors handle each transfer

**When to use**:
- ✅ Auditing external connections
- ✅ Tracking data volume to partners
- ✅ Identifying integration points
- ✅ Compliance and security reviews

**Example output**:
```
📤 Outbound Transfers (SEND)
╭─────────────────────────────────────────────────────────╮
│ Destination            │ Processor  │ Count │ Total Bytes│
│ sftp://partner.com/... │ PutSFTP    │  123  │  1,234,567 │
│ https://api.example... │ InvokeHTTP │   45  │    456,789 │
╰─────────────────────────────────────────────────────────╯

📥 Inbound Transfers (RECEIVE)
╭─────────────────────────────────────────────────────────╮
│ Source                 │ Processor  │ Count │ Total Bytes│
│ kafka://topic1         │ ConsumeKafa│  567  │  5,678,901 │
│ s3://bucket/path       │ FetchS3    │  234  │  2,345,678 │
╰─────────────────────────────────────────────────────────╯
```

---

### 5. 🔍 trace-flowfile - FlowFile Lineage Tracing

**Purpose**: Shows the complete history of a specific FlowFile through the system.

**Usage**:
```
(nifi-troubleshoot)> trace-flowfile 550e8400-e29b-41d4-a716-446655440000
```

**What it shows**:
- Every event involving the FlowFile
- Parent-child relationships
- Timing and duration of each step
- Details and reasons for events

**When to use**:
- ✅ Debugging specific FlowFile issues
- ✅ Understanding why data was dropped
- ✅ Tracing data transformations
- ✅ Audit trails for compliance

**Example output**:
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

**How to find FlowFile UUIDs**:
- Check NiFi UI provenance page
- Look in bulletins for UUIDs
- Use `dropped-flowfiles` command to find dropped UUIDs

---

### 6. 🔀 fork-join-analysis - Split/Merge Pattern Analysis

**Purpose**: Analyzes how FlowFiles are split (FORK) and merged (JOIN) in your flows.

**Usage**:
```
(nifi-troubleshoot)> fork-join-analysis
```

**What it shows**:
- **FORK events**: How many children created per parent
- **JOIN events**: How many parents merged into one child
- Statistics: average, median, max ratios

**When to use**:
- ✅ Understanding data fan-out patterns
- ✅ Identifying processors that split data
- ✅ Analyzing data aggregation
- ✅ Capacity planning for downstream processors

**Example output**:
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

**Interpretation**:
- High avg children → Aggressive splitting (check downstream capacity)
- High max children → Occasional large splits
- High avg parents → Data aggregation bottleneck potential

---

### 7. ✏️ content-modifications - Transformation Analysis

**Purpose**: Shows which processors frequently modify FlowFile content or attributes.

**Usage**:
```
(nifi-troubleshoot)> content-modifications
(nifi-troubleshoot)> content-modifications 20    # Top 20 processors
```

**What it shows**:
- Processors that modify content
- Processors that modify attributes
- Total modification counts

**When to use**:
- ✅ Identifying transformation-heavy processors
- ✅ Understanding data enrichment patterns
- ✅ Finding processors that might be slow due to transformations
- ✅ Optimizing flow design

**Example output**:
```
╭─────────────────────────────────────────────────────────╮
│ FlowFile Modification Patterns                          │
├─────────────────────────────────────────────────────────┤
│ Processor       │ Content Mod │ Attributes Mod │ Total │
│ ConvertRecord   │    1,234    │       567      │ 1,801 │
│ UpdateAttribute │       0     │     2,345      │ 2,345 │
│ JoltTransform   │      567    │       123      │   690 │
│ ReplaceText     │      234    │         0      │   234 │
╰─────────────────────────────────────────────────────────╯
```

**Interpretation**:
- High content modifications → Processor doing heavy transformation
- High attribute modifications → Metadata enrichment
- Combined high counts → Complex processing (potential optimization target)

---

## Typical Troubleshooting Workflows

### Workflow 1: Investigating Data Loss

```
1. dropped-flowfiles                      # Find which processors are dropping
2. trace-flowfile <uuid>                  # Trace a specific dropped FlowFile
3. view-bulletins ERROR                   # Check for related errors
4. health-summary                         # Overall system state
```

### Workflow 2: Performance Investigation

```
1. bottlenecks                            # Find slow processors
2. slow-processors                        # Cross-reference with standard metrics
3. flow-paths                             # Understand common paths
4. fork-join-analysis                     # Check if splitting causing issues
```

### Workflow 3: External Integration Audit

```
1. external-transfers                     # See all external connections
2. view-bulletins                         # Check for transfer errors
3. back-pressure                          # Check if external systems are slow
```

### Workflow 4: Data Flow Documentation

```
1. flow-paths                             # Common flow paths
2. fork-join-analysis                     # Splitting/merging patterns
3. content-modifications                  # Transformation points
4. external-transfers                     # Integration points
```

## Best Practices

### Collection Configuration

For effective provenance analysis, configure appropriate collection settings:

```json
{
  "provenance_config": {
    "lookback_minutes": 60,        // Balance between data and performance
    "max_results": 1000,           // Enough for analysis, not too many
    "event_type": null             // Collect all types (don't filter)
  }
}
```

### Analysis Tips

1. **Start Broad**: Use `health-summary` first, then drill down
2. **Time Windows**: Adjust time windows based on your data volume
3. **Cross-Reference**: Compare provenance with standard metrics
4. **Regular Checks**: Run `dropped-flowfiles` regularly as part of monitoring
5. **Document Findings**: Save interesting FlowFile UUIDs for later reference

### Performance Considerations

- **Large datasets**: Use shorter time windows or filter by event type
- **Slow queries**: Consider using `load-collection` for specific periods
- **Memory usage**: Limit provenance collection intervals in high-volume systems

## Common Issues and Solutions

### "No provenance data loaded"

**Problem**: Provenance commands return "No provenance data loaded"

**Solutions**:
1. Check that `"Provenance"` is in `components_to_monitor` in config
2. Verify provenance collection is running: `python bin/run_collector.py --once`
3. Check storage location for provenance files
4. Try loading a different date: `load 2024-12-16`

### "FlowFile not found"

**Problem**: `trace-flowfile` can't find the UUID

**Solutions**:
1. Verify UUID is correct (no typos)
2. Check the date range loaded includes when that FlowFile existed
3. FlowFile might be older than your lookback window
4. Use `flow-paths` to find other FlowFiles to trace

### Too much data / slow analysis

**Problem**: Commands are slow or return too much data

**Solutions**:
1. Reduce time window: `dropped-flowfiles 30` instead of 60
2. Load specific dates: `load 2024-12-16` instead of date ranges
3. Increase `min_drops` threshold
4. Use `load-collection` for specific collection runs

## Integration with Standard Metrics

Provenance analysis works best when combined with standard metrics:

| Provenance Command | Complement With | Insight |
|-------------------|-----------------|---------|
| `bottlenecks` | `slow-processors` | Confirms slow processing with lineage data |
| `dropped-flowfiles` | `list-stopped` | Dropped data + stopped processors = issue |
| `external-transfers` | `back-pressure` | External slowness causing backups |
| `flow-paths` | `health-summary` | Common paths align with processor activity |

## Advanced Usage

### Scripting with Data

Export findings for further analysis:

```python
from analysis.lib.data_loader import load_all_data
from analysis.lib.provenance_analysis import analyze_dropped_flowfiles

# Load data
data = load_all_data(config, secrets, "2024-12-16")

# Run analysis programmatically
analyze_dropped_flowfiles(data, time_window_minutes=120, min_drops=10)
```

### Custom Queries

Access raw provenance DataFrames:

```python
# Get provenance data
prov_df = data_cache.get('nifi_provenance')

# Custom analysis
dropped = prov_df[prov_df['event_type'] == 'DROP']
by_hour = dropped.groupby(dropped['event_time'].dt.hour).size()
print(by_hour)
```

## Summary

Provenance analysis provides unprecedented visibility into your data flows:

✅ **Data Loss Detection** - Find dropped FlowFiles immediately
✅ **Performance Analysis** - Identify bottlenecks with real event data
✅ **Flow Understanding** - Visualize actual data paths
✅ **Compliance & Audit** - Complete lineage tracing
✅ **Optimization** - Data-driven flow improvements

Use these tools regularly to maintain healthy, efficient data flows!
