"""
Unit tests for the versioning system.
"""

import pytest
import json
import gzip
import tempfile
from pathlib import Path
from datetime import datetime

# Import modules to test
from lib.version import (
    get_schema_version,
    is_version_compatible,
    get_version_info,
    get_supported_metric_types,
    get_migration_path
)


class TestVersionModule:
    """Tests for the version module."""
    
    def test_get_schema_version(self):
        """Test that current version is returned correctly."""
        version = get_schema_version()
        assert version is not None
        assert isinstance(version, str)
        assert len(version.split('.')) == 3  # Should be semantic versioning
    
    def test_version_compatibility_current(self):
        """Test that current version is compatible."""
        current = get_schema_version()
        assert is_version_compatible(current, "1.0.0")
    
    def test_version_compatibility_old(self):
        """Test that old versions are compatible."""
        assert is_version_compatible("1.0.0", "1.0.0")
    
    def test_version_compatibility_future(self):
        """Test that future versions are not compatible."""
        assert not is_version_compatible("99.0.0", "1.0.0")
    
    def test_version_compatibility_too_old(self):
        """Test that versions below minimum are not compatible."""
        assert not is_version_compatible("0.9.0", "1.0.0")
    
    def test_version_compatibility_invalid(self):
        """Test that invalid version strings return False."""
        assert not is_version_compatible("invalid", "1.0.0")
        assert not is_version_compatible(None, "1.0.0")
    
    def test_get_version_info_current(self):
        """Test getting info for current version."""
        info = get_version_info()
        assert info is not None
        assert "date" in info
        assert "changes" in info
        assert "metric_types" in info
    
    def test_get_version_info_specific(self):
        """Test getting info for a specific version."""
        info = get_version_info("1.0.0")
        assert info is not None
        assert "date" in info or "changes" in info
    
    def test_get_version_info_invalid(self):
        """Test getting info for invalid version."""
        info = get_version_info("99.99.99")
        assert info is None
    
    def test_get_supported_metric_types(self):
        """Test getting supported metric types."""
        types = get_supported_metric_types()
        assert isinstance(types, list)
        assert len(types) > 0
        assert "nifi_processor" in types
    
    def test_get_supported_metric_types_old_version(self):
        """Test getting metric types for old version."""
        types = get_supported_metric_types("1.0.0")
        assert isinstance(types, list)
        # v1.0.0 shouldn't have provenance
        assert "nifi_provenance" not in types
    
    def test_get_supported_metric_types_new_version(self):
        """Test getting metric types for new version."""
        types = get_supported_metric_types("1.1.0")
        assert isinstance(types, list)
        # v1.1.0 should have provenance
        assert "nifi_provenance" in types
    
    def test_get_migration_path(self):
        """Test getting migration path between versions."""
        path = get_migration_path("1.0.0", "1.1.0")
        assert path == ["1.0.0", "1.1.0"]
    
    def test_get_migration_path_same_version(self):
        """Test migration path for same version."""
        path = get_migration_path("1.0.0", "1.0.0")
        assert path == ["1.0.0"]
    
    def test_get_migration_path_invalid(self):
        """Test migration path with invalid versions."""
        path = get_migration_path("99.0.0", "1.0.0")
        assert path == []


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
