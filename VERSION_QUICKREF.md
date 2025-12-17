# Schema Versioning Quick Reference

## Current Version: 1.1.0

## Quick Commands

```bash
# Check current version
python -c "from lib.version import get_schema_version; print(get_schema_version())"

# Print version info
python -c "from lib.file_reader import print_version_info; print_version_info()"

# Run version tests
pytest tests/test_versioning.py -v
```

## Common Code Snippets

### Check Version Compatibility
```python
from lib.version import is_version_compatible

if is_version_compatible("1.0.0"):
    print("Compatible!")
```

### Read Versioned File
```python
from pathlib import Path
from lib.file_reader import FileReader

reader = FileReader(min_supported_version="1.0.0")
data, version = reader.read_and_validate(Path("metrics.json.gz"))
print(f"Loaded version: {version}")
```

### Load Collection
```python
collection = reader.load_collection(
    Path("/tmp/nifi_metrics"),
    "collection-id-here"
)
print(collection["versions"])  # Version per metric type
```

### Find Files
```python
# By metric type
files = reader.find_collection_files(
    Path("/tmp/nifi_metrics"),
    metric_type="nifi_processor"
)

# By date
files = reader.find_collection_files(
    Path("/tmp/nifi_metrics"),
    date="2024-12-16"
)

# By collection ID
files = reader.find_collection_files(
    Path("/tmp/nifi_metrics"),
    collection_id="uuid-here"
)
```

### Handle Errors
```python
from lib.file_reader import VersionMismatchError

try:
    data, version = reader.read_and_validate(file_path)
except VersionMismatchError as e:
    print(f"Version incompatible: {e}")
except FileNotFoundError:
    print("File not found")
```

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| 1.1.0 | 2024-12-16 | Added provenance collection |
| 1.0.0 | 2024-12-01 | Initial release |

## Supported Metric Types by Version

### v1.1.0 (Current)
- nifi_processor
- nifi_connection
- nifi_jvm
- nifi_controller_service
- nifi_reporting_task
- nifi_bulletin
- **nifi_provenance** ⭐ NEW
- system

### v1.0.0
- nifi_processor
- nifi_connection
- nifi_jvm
- nifi_controller_service
- nifi_reporting_task
- nifi_bulletin
- system

## When to Bump Versions

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Bug fix | PATCH (1.1.0→1.1.1) | Fix metric calculation |
| New feature | MINOR (1.1.0→1.2.0) | Add new metric type |
| Breaking change | MAJOR (1.1.0→2.0.0) | Remove/rename fields |

## File Format

Every metric includes:
```json
{
  "schema_version": "1.1.0",
  "collection_id": "uuid",
  "hostname": "nifi-node-01",
  "collection_timestamp": "2024-12-16T10:30:00",
  "... metric data ..."
}
```

## FileReader API

```python
reader = FileReader(min_supported_version="1.0.0")

# Read file
data, version = reader.read_and_validate(path)

# Load collection
collection = reader.load_collection(base_path, collection_id)

# Find files
files = reader.find_collection_files(base_path, **filters)

# Read manifest
manifest = reader.read_manifest(manifest_path)

# Get file metadata
metadata = reader.get_file_metadata(file_path)
```

## Deployment Checklist

- [ ] Update `lib/version.py` with new version
- [ ] Add entry to `VERSION_HISTORY`
- [ ] Update README.md
- [ ] Run tests: `pytest tests/test_versioning.py`
- [ ] Deploy analysis tools FIRST
- [ ] Deploy collectors
- [ ] Monitor logs for version information

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Version mismatch error | Update analysis tool to support new version |
| Legacy files | Automatically handled as v1.0.0 |
| Mixed versions | Normal - each metric type tracks its own version |
| Can't find files | Check base_path and search criteria |

## Support

For questions or issues with versioning:
1. Check `VERSIONING.md` for detailed documentation
2. Review test cases in `tests/test_versioning.py`
3. Enable DEBUG logging: `--log-level DEBUG`
