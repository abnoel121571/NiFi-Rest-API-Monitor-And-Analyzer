Schema Versioning Implementation Guide
Overview
The NiFi metrics collector uses semantic versioning (MAJOR.MINOR.PATCH) to track schema changes in output files. This ensures backward compatibility and allows the analysis tools to handle data from different versions gracefully.
Architecture
Core Components

lib/version.py - Central version management

Defines current schema version
Maintains version history
Provides compatibility checking functions


lib/storage_writer.py - Adds version metadata to output

Injects schema_version into every metric entry
Creates manifest files with version information
Logs version information during writes


lib/file_reader.py - Reads and validates versioned files

Validates schema versions when loading files
Handles legacy files without versions
Provides utilities for finding and filtering files by version



Version Format
Schema versions follow semantic versioning:
MAJOR.MINOR.PATCH
  │     │      │
  │     │      └─ Bug fixes, no schema changes
  │     └──────── New features, backward compatible
  └────────────── Breaking changes, not backward compatible
Current Version: 1.1.0
Adding New Versions
When to Bump Versions

PATCH (1.1.0 → 1.1.1): Bug fixes, no schema changes

Example: Fix calculation error in a metric


MINOR (1.1.0 → 1.2.0): New features, backward compatible

Example: Add new metric type or new fields to existing metrics
Analysis tools can still read old data


MAJOR (1.1.0 → 2.0.0): Breaking changes

Example: Remove fields, change data types, restructure format
Requires analysis tool updates
May need migration scripts



Steps to Add a New Version

Update lib/version.py:

python   # Update the version constant
   SCHEMA_VERSION = "1.2.0"
   
   # Add to version history
   VERSION_HISTORY = {
       "1.2.0": {
           "date": "2024-12-20",
           "changes": [
               "Added cluster node metrics",
               "Added network bandwidth tracking"
           ],
           "metric_types": [
               # ... all previous types ...
               "nifi_cluster_node"  # new type
           ]
       },
       # ... previous versions ...
   }

Test Compatibility:

bash   pytest tests/test_versioning.py -v

Update Documentation:

Add version to README.md version history
Document new fields/metric types
Note any breaking changes


Deploy:

Update analysis tools FIRST (they should support new and old versions)
Then update collectors



File Format
Every metric file includes version metadata:
json[
  {
    "collection_id": "uuid-here",
    "hostname": "nifi-node-01",
    "collection_timestamp": "2024-12-16T10:30:00.000000",
    "schema_version": "1.1.0",
    "id": "processor-id",
    "... other fields ..."
  }
]
Manifest files also include version:
json{
  "manifest_version": "1.0",
  "collection_id": "uuid-here",
  "schema_version": "1.1.0",
  "metric_types": {
    "nifi_processor": {"record_count": 10},
    "nifi_provenance": {"record_count": 500}
  }
}
Using the FileReader
Basic Usage
pythonfrom pathlib import Path
from lib.file_reader import FileReader

# Initialize with minimum supported version
reader = FileReader(min_supported_version="1.0.0")

# Read and validate a file
data, version = reader.read_and_validate(
    Path("/tmp/nifi_metrics/nifi_processor-metrics/2024-12-16/file.json.gz")
)

print(f"Loaded {len(data)} records from schema version {version}")
Load Complete Collection
python# Load all metrics from a collection
collection = reader.load_collection(
    base_path=Path("/tmp/nifi_metrics"),
    collection_id="550e8400-e29b-41d4-a716-446655440000",
    validate_versions=True
)

# Access different metric types
processors = collection["metrics"]["nifi_processor"]
connections = collection["metrics"]["nifi_connection"]

# Check versions
print(f"Processor data version: {collection['versions']['nifi_processor']}")
Find Files by Criteria
python# Find all processor files from a specific date
files = reader.find_collection_files(
    base_path=Path("/tmp/nifi_metrics"),
    metric_type="nifi_processor",
    date="2024-12-16"
)

# Find all files from a specific collection
files = reader.find_collection_files(
    base_path=Path("/tmp/nifi_metrics"),
    collection_id="550e8400-e29b-41d4-a716-446655440000"
)
Handle Version Incompatibilities
pythonfrom lib.file_reader import VersionMismatchError

try:
    data, version = reader.read_and_validate(file_path)
except VersionMismatchError as e:
    print(f"File version not compatible: {e}")
    # Handle gracefully - skip file, convert, etc.
Compatibility Matrix
Collector VersionAnalysis Tool Min VersionNotes1.0.01.0.0Initial release1.1.01.0.0Added provenance, backward compatible2.0.0 (future)2.0.0Would require tool update
Migration Strategies
Reading Mixed-Version Data
The FileReader can handle files from different versions in the same collection:
pythoncollection = reader.load_collection(base_path, collection_id)

# Check versions of different metric types
for metric_type, version in collection["versions"].items():
    print(f"{metric_type}: {version}")
    
    # Handle version-specific logic
    if version == "1.0.0":
        # Old format - provenance not available
        pass
    elif version == "1.1.0":
        # New format - provenance available
        pass
Upgrading Analysis Tools
When upgrading tools to support new versions:

Keep support for old versions (backward compatibility)
Add handlers for new fields/types
Test with data from all supported versions

pythondef process_processor_metrics(data, version):
    """Process processor metrics, handling different versions."""
    for entry in data:
        # Common fields (all versions)
        processor_id = entry["id"]
        name = entry["name"]
        
        # Version-specific fields
        if version >= "1.1.0":
            # New field added in 1.1.0
            lineage_duration = entry.get("nifi_average_lineage_duration")
Testing
Run the comprehensive test suite:
bash# All versioning tests
pytest tests/test_versioning.py -v

# Specific test class
pytest tests/test_versioning.py::TestVersionModule -v

# With coverage
pytest tests/test_versioning.py --cov=lib.version --cov=lib.file_reader
Best Practices

Always Add Version Metadata: The storage writer automatically adds it, don't skip
Version Before Deploy: Update version.py before releasing new features
Document Changes: Keep VERSION_HISTORY up to date
Test Compatibility: Run tests with data from all supported versions
Plan for Migration: For major versions, provide migration scripts or clear upgrade paths
Gradual Rollout: Update analysis tools before updating collectors
Monitor Versions: Log and track which versions are being written/read

Troubleshooting
"Incompatible schema version" Error
Problem: Analysis tool rejects files with newer versions
Solution:

Check current tool version: python -c "from lib.version import get_schema_version; print(get_schema_version())"
Update the analysis tool to support the new version
Or, filter files by version when loading

Legacy Files Without Versions
Problem: Old files don't have schema_version field
Solution: FileReader automatically assumes version 1.0.0 for legacy files
python# Legacy files are handled automatically
data, version = reader.read_and_validate(legacy_file)
# version will be "1.0.0"
Mixed Version Collections
Problem: Collection has files from different versions
Solution: This is normal and supported. The FileReader tracks versions per metric type:
pythoncollection = reader.load_collection(base_path, collection_id)
# Different metric types may have different versions
versions = collection["versions"]  # {"nifi_processor": "1.0.0", "nifi_provenance": "1.1.0"}
Future Enhancements
Potential improvements to the versioning system:

Migration Scripts: Auto-convert old format to new format
Version Negotiation: Collectors query analysis tool for supported versions
Schema Validation: JSON schema files for each version
Deprecation Warnings: Warn when reading old versions
Version Analytics: Track which versions are in use across fleet

References

Semantic Versioning: https://semver.org/
Version module: lib/version.py
File reader: lib/file_reader.py
Tests: tests/test_versioning.py


Semantic Versioning: https://semver.org/
Version module: lib/version.py
File reader: lib/file_reader.py
Tests: tests/test_versioning.py

