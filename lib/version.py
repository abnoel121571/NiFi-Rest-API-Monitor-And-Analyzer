"""
Schema versioning for NiFi metrics output files.

Version History:
- 1.0.0: Initial release with Processor, Connection, JVM, ControllerService, 
         ReportingTask, Bulletin, and System metrics
- 1.1.0: Added Provenance data collection
"""

# Current schema version
SCHEMA_VERSION = "1.1.0"

# Version changelog for reference
VERSION_HISTORY = {
    "1.0.0": {
        "date": "2024-12-01",
        "changes": [
            "Initial schema version",
            "Support for Processor metrics",
            "Support for Connection metrics",
            "Support for JVM metrics",
            "Support for Controller Service metrics",
            "Support for Reporting Task metrics",
            "Support for Bulletin metrics",
            "Support for System metrics"
        ],
        "metric_types": [
            "nifi_processor",
            "nifi_connection",
            "nifi_jvm",
            "nifi_controller_service",
            "nifi_reporting_task",
            "nifi_bulletin",
            "system"
        ]
    },
    "1.1.0": {
        "date": "2024-12-16",
        "changes": [
            "Added Provenance data collection",
            "Added provenance event tracking",
            "Added lineage and relationship information",
            "Added event type filtering support"
        ],
        "metric_types": [
            "nifi_processor",
            "nifi_connection",
            "nifi_jvm",
            "nifi_controller_service",
            "nifi_reporting_task",
            "nifi_bulletin",
            "nifi_provenance",
            "system"
        ]
    }
}

def get_schema_version():
    """Returns the current schema version."""
    return SCHEMA_VERSION

def get_version_info(version=None):
    """
    Returns information about a specific version.
    
    Args:
        version: Version string (e.g., "1.0.0"). If None, returns current version info.
    
    Returns:
        Dictionary with version information or None if version not found.
    """
    if version is None:
        version = SCHEMA_VERSION
    return VERSION_HISTORY.get(version)

def is_version_compatible(file_version, min_supported_version="1.0.0"):
    """
    Checks if a file version is compatible with the analysis tool.
    
    Args:
        file_version: Version string from a metrics file
        min_supported_version: Minimum version the tool supports
    
    Returns:
        Boolean indicating compatibility
    """
    def version_tuple(v):
        return tuple(map(int, v.split('.')))
    
    try:
        file_ver = version_tuple(file_version)
        min_ver = version_tuple(min_supported_version)
        current_ver = version_tuple(SCHEMA_VERSION)
        
        # File version must be >= minimum and <= current
        return min_ver <= file_ver <= current_ver
    except (ValueError, AttributeError):
        return False

def get_supported_metric_types(version=None):
    """
    Returns list of supported metric types for a given version.
    
    Args:
        version: Version string. If None, returns types for current version.
    
    Returns:
        List of metric type strings
    """
    if version is None:
        version = SCHEMA_VERSION
    
    version_info = VERSION_HISTORY.get(version)
    if version_info:
        return version_info.get("metric_types", [])
    return []

def get_migration_path(from_version, to_version=None):
    """
    Returns the list of versions between two versions for migration purposes.
    
    Args:
        from_version: Starting version
        to_version: Target version (defaults to current version)
    
    Returns:
        List of version strings in order
    """
    if to_version is None:
        to_version = SCHEMA_VERSION
    
    versions = sorted(VERSION_HISTORY.keys(), key=lambda v: tuple(map(int, v.split('.'))))
    
    try:
        start_idx = versions.index(from_version)
        end_idx = versions.index(to_version)
        
        if start_idx <= end_idx:
            return versions[start_idx:end_idx + 1]
        else:
            return []
    except ValueError:
        return []
