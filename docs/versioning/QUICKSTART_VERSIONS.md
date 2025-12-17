# Version System Quick Start Guide

## 5-Minute Overview

The NiFi metrics collector now includes **automatic schema versioning** for all collected data. This guide gets you up and running quickly.

## What You Get

✅ Every metric file includes a `schema_version` field  
✅ Automatic validation when loading data  
✅ Compatible with old data (v1.0.0)  
✅ Version info in analysis tool  
✅ No configuration changes needed!

## Quick Start

### 1. Check Current Version

```bash
python -c "from lib.version import get_schema_version; print(get_schema_version())"
# Output: 1.1.0
```

### 2. Collect Metrics (Already Versioned!)

```bash
# Collect once
python bin/run_collector.py --hostname localhost --once

# Or run continuously (versions added automatically)
python bin/run_collector.py --hostname localhost
```

Your metrics now include version information - no changes needed!

### 3. Verify Versioned Output

```bash
# Check a collected file
zcat /tmp/nifi_metrics/nifi_processor-metrics/2024-12-16/*.json.gz | jq '.[0] | {schema_version, hostname, collection_timestamp}'

# Output:
# {
#   "schema_version": "1.1.0",
#   "hostname": "nifi-node-01",
#   "collection_timestamp": "2024-12-16T10:30:00.000000"
# }
```

### 4. Analyze with Version Info

```bash
python analysis/troubleshoot.py
```

```
(nifi-troubleshoot)> version-info
Current Schema Version: 1.1.0
Supported Features:
  ✓ Provenance data collection
  ✓ Event tracking and lineage
  ...

(nifi-troubleshoot)> load 2024-12-16
Loading data for 2024-12-16...
  - Loaded 450 records for nifi_processor (15 files, 0 skipped)
    Versions: 1.1.0
Data loaded successfully.

(nifi-troubleshoot)> data-versions
=== Data Version Summary ===
Current Tool Version: 1.1.0
Versions by Metric Type:
  nifi_processor: 1.1.0
  nifi_connection: 1.1.0
  nifi_provenance: 1.1.0
✓ All data versions are compatible with this tool.

(nifi-troubleshoot)> health-summary
[... normal analysis continues ...]
```

## That's It!

The versioning system works automatically. Continue using the tool as normal - versions are handled behind the scenes.

## Common Scenarios

### Scenario 1: Upgrading from Old Version

**You have**: Old data from before versioning was added

**What happens**: 
- Old files are detected as "legacy" 
- Assumed to be v1.0.0
- Work perfectly with current tool

```
(nifi-troubleshoot)> load 2024-11-15
Loading data for 2024-11-15...
Warning: No schema_version in file.json.gz, assuming v1.0.0
  - Loaded 300 records for nifi_processor
    Versions: 1.0.0 (legacy)
✓ All data versions are compatible with this tool.
```

### Scenario 2: Mixed Version Data

**You have**: Data from multiple collector versions

**What happens**:
- Each file's version is tracked separately
- All compatible versions load successfully
- Version summary shows the mix

```
(nifi-troubleshoot)> load 2024-12-01 2024-12-16
Loading data for 2024-12-01...
  - Loaded 300 records for nifi_processor
    Versions: 1.0.0
Loading data for 2024-12-16...
  - Loaded 450 records for nifi_processor
    Versions: 1.1.0

Versions found in data: 1.0.0, 1.1.0
```

### Scenario 3: Loading Specific Collection

**You want**: All metrics from one collection run

**How**:
```
(nifi-troubleshoot)> load-collection 550e8400-e29b-41d4-a716-446655440000
Loading collection 550e8400-e29b-41d4-a716-446655440000...
  - Loaded 45 nifi_processor records (version 1.1.0)
  - Loaded 120 nifi_connection records (version 1.1.0)
  - Loaded 501 nifi_provenance records (version 1.1.0)

Collection loaded successfully:
  Total records: 666
  Files loaded: 3
```

## New Analysis Commands

### Check Tool Version
```
(nifi-troubleshoot)> version-info
```
Shows current tool version and all supported features.

### Check Data Versions
```
(nifi-troubleshoot)> data-versions
```
Shows versions of all loaded data.

### Validate Compatibility
```
(nifi-troubleshoot)> validate-versions
```
Checks if all loaded data is compatible with current tool.

## When to Check Versions

### ✅ Check versions when:
- After upgrading the collector or analysis tool
- Loading data from different time periods
- Troubleshooting data loading issues
- Documenting your data for compliance

### ❌ Don't need to check:
- During normal daily operations
- When everything is working fine
- Before every analysis command

## Version Numbers Explained

```
1.1.0
│ │ │
│ │ └─ PATCH: Bug fixes only
│ └─── MINOR: New features (backward compatible)
└───── MAJOR: Breaking changes
```

**Current**: v1.1.0 (Added provenance collection)  
**Previous**: v1.0.0 (Initial release)

### Compatibility Rules

| Tool Version | Can Read Data Versions | Notes |
|--------------|------------------------|-------|
| 1.1.0 | 1.0.0, 1.1.0 | Current version |
| 1.0.0 | 1.0.0 | Legacy version |
| 2.0.0 (future) | 1.0.0, 1.1.0, 2.0.0 | Would be backward compatible |

## Troubleshooting

### "Version module not found"

**Problem**: Can't import version utilities

**Fix**:
```bash
# Ensure you're in the right directory
cd nifi_metrics_collector

# Reinstall in editable mode
pip install -e .

# Verify
python -c "from lib.version import get_schema_version; print('OK')"
```

### All Data Shows "1.0.0 (legacy)"

**Problem**: Not seeing v1.1.0 data

**Cause**: Running old collector

**Fix**: Update and restart collector:
```bash
git pull
pip install -e .
python bin/run_collector.py --hostname localhost --once
```

### "Incompatible schema version" Error

**Problem**: Can't load some files

**Cause**: Tool is older than data (rare)

**Fix**: Update the analysis tool:
```bash
git pull
pip install -e .
```

## Best Practices

### ✅ DO:
- Let the system handle versions automatically
- Check `data-versions` after major upgrades
- Keep analysis tool up-to-date
- Use `validate-versions` if something seems wrong

### ❌ DON'T:
- Manually edit version fields in files
- Worry about versions during normal operations
- Downgrade collectors without checking compatibility
- Mix production and development versions

## Need More Info?

- **Detailed docs**: See `VERSIONING.md`
- **Integration details**: See `INTEGRATION_SUMMARY.md`
- **API reference**: See `lib/version.py`
- **Test examples**: See `tests/test_versioning.py`

## Summary

🎉 **Versioning is automatic and transparent!**

You can continue using the collector and analysis tool exactly as before. The version system works quietly in the background, ensuring your data is always compatible and well-documented.

Just remember:
1. Update analysis tools before updating collectors
2. Check versions occasionally with `version-info` and `data-versions`
3. Old data works fine with new tools
4. Versions are helpful during troubleshooting

That's all you need to know to use the versioning system effectively!
