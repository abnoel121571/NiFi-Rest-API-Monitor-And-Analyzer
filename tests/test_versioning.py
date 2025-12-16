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
from lib.file_reader import FileReader, VersionMismatchError


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
        assert "1.0.0" in str(info) or "date" in info
    
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


class TestFileReader:
    """Tests for the FileReader class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def reader(self):
        """Create a FileReader instance."""
        return FileReader(min_supported_version="1.0.0")
    
    def create_test_file(self, file_path: Path, data: list, compress: bool = True):
        """Helper to create test metric files."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if compress:
            with gzip.open(file_path, 'wt', encoding='utf-8') as f:
                json.dump(data, f)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
    
    def test_read_json_file_gzipped(self, temp_dir, reader):
        """Test reading a gzipped JSON file."""
        test_data = [{"id": "test", "value": 123}]
        test_file = temp_dir / "test.json.gz"
        self.create_test_file(test_file, test_data)
        
        result = reader.read_json_file(test_file)
        assert result == test_data
    
    def test_read_json_file_plain(self, temp_dir, reader):
        """Test reading a plain JSON file."""
        test_data = [{"id": "test", "value": 123}]
        test_file = temp_dir / "test.json"
        self.create_test_file(test_file, test_data, compress=False)
        
        result = reader.read_json_file(test_file)
        assert result == test_data
    
    def test_read_json_file_not_found(self, temp_dir, reader):
        """Test reading a non-existent file."""
        with pytest.raises(FileNotFoundError):
            reader.read_json_file(temp_dir / "nonexistent.json")
    
    def test_validate_file_version_valid(self, reader):
        """Test validating a file with valid version."""
        data = [{"schema_version": "1.0.0", "id": "test"}]
        is_valid, version = reader.validate_file_version(data, Path("test.json"))
        assert is_valid
        assert version == "1.0.0"
    
    def test_validate_file_version_compatible(self, reader):
        """Test validating a file with compatible version."""
        data = [{"schema_version": "1.1.0", "id": "test"}]
        is_valid, version = reader.validate_file_version(data, Path("test.json"))
        assert is_valid
        assert version == "1.1.0"
    
    def test_validate_file_version_incompatible(self, reader):
        """Test validating a file with incompatible version."""
        data = [{"schema_version": "99.0.0", "id": "test"}]
        with pytest.raises(VersionMismatchError):
            reader.validate_file_version(data, Path("test.json"))
    
    def test_validate_file_version_legacy(self, reader):
        """Test validating a file without version (legacy)."""
        data = [{"id": "test", "value": 123}]
        is_valid, version = reader.validate_file_version(data, Path("test.json"))
        assert is_valid
        assert version == "1.0.0"
    
    def test_validate_file_version_empty(self, reader):
        """Test validating an empty file."""
        data = []
        is_valid, version = reader.validate_file_version(data, Path("test.json"))
        assert is_valid
        assert version == "unknown"
    
    def test_read_and_validate(self, temp_dir, reader):
        """Test reading and validating a file."""
        test_data = [{"schema_version": "1.0.0", "id": "test", "value": 123}]
        test_file = temp_dir / "test.json.gz"
        self.create_test_file(test_file, test_data)
        
        data, version = reader.read_and_validate(test_file)
        assert data == test_data
        assert version == "1.0.0"
    
    def test_get_file_metadata(self, reader):
        """Test extracting metadata from file path."""
        file_path = Path("/tmp/nifi_metrics/nifi_processor-metrics/2024-12-16/host01_nifi_processor_uuid123.json.gz")
        metadata = reader.get_file_metadata(file_path)
        
        assert metadata["hostname"] == "host01"
        assert metadata["metric_type"] == "nifi_processor"
        assert metadata["collection_id"] == "uuid123"
        assert metadata["date"] == "2024-12-16"
    
    def test_find_collection_files(self, temp_dir, reader):
        """Test finding collection files."""
        # Create test structure
        base = temp_dir / "metrics"
        test_files = [
            base / "nifi_processor-metrics/2024-12-16/host01_nifi_processor_uuid1.json.gz",
            base / "nifi_processor-metrics/2024-12-16/host01_nifi_processor_uuid2.json.gz",
            base / "nifi_connection-metrics/2024-12-16/host01_nifi_connection_uuid1.json.gz",
        ]
        
        for file_path in test_files:
            self.create_test_file(file_path, [{"id": "test"}])
        
        # Find all processor files
        found = reader.find_collection_files(base, metric_type="nifi_processor")
        assert len(found) == 2
        
        # Find specific collection
        found = reader.find_collection_files(base, collection_id="uuid1")
        assert len(found) == 2  # processor and connection
        
        # Find by date
        found = reader.find_collection_files(base, date="2024-12-16")
        assert len(found) == 3
    
    def test_load_collection(self, temp_dir, reader):
        """Test loading a complete collection."""
        base = temp_dir / "metrics"
        collection_id = "test-collection-123"
        
        # Create test files
        processor_data = [
            {"schema_version": "1.0.0", "id": "proc1", "name": "Processor1"},
            {"schema_version": "1.0.0", "id": "proc2", "name": "Processor2"}
        ]
        connection_data = [
            {"schema_version": "1.0.0", "id": "conn1", "queuedCount": "100"}
        ]
        
        proc_file = base / f"nifi_processor-metrics/2024-12-16/host01_nifi_processor_{collection_id}.json.gz"
        conn_file = base / f"nifi_connection-metrics/2024-12-16/host01_nifi_connection_{collection_id}.json.gz"
        
        self.create_test_file(proc_file, processor_data)
        self.create_test_file(conn_file, connection_data)
        
        # Load collection
        collection = reader.load_collection(base, collection_id)
        
        assert collection["collection_id"] == collection_id
        assert "nifi_processor" in collection["metrics"]
        assert "nifi_connection" in collection["metrics"]
        assert len(collection["metrics"]["nifi_processor"]) == 2
        assert len(collection["metrics"]["nifi_connection"]) == 1
        assert collection["versions"]["nifi_processor"] == "1.0.0"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"]
