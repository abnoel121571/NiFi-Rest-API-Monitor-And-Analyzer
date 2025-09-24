import json
import pytest
from lib.config_loader import load_config, load_secrets

def test_load_config_success(mocker):
    """Tests successful loading of the main config file."""
    mock_data = {"nifi_api_url": "http://fake-nifi"}
    # Mock the open call to return our fake data
    mocker.patch("builtins.open", mocker.mock_open(read_data=json.dumps(mock_data)))
    # Mock the path to avoid filesystem dependency
    mocker.patch("os.path.abspath", return_value="/fake/path/config/nifi-config.json")

    config = load_config()
    assert config["nifi_api_url"] == "http://fake-nifi"

def test_load_secrets_file_not_found(mocker):
    """Tests that FileNotFoundError is raised when secrets file is missing."""
    mocker.patch("builtins.open", side_effect=FileNotFoundError)
    mocker.patch("os.path.abspath", return_value="/fake/path/config/secrets.json")

    with pytest.raises(FileNotFoundError):
        load_secrets()

def test_load_config_invalid_json(mocker):
    """Tests that JSONDecodeError is handled correctly for malformed JSON."""
    mocker.patch("builtins.open", mocker.mock_open(read_data="{invalid_json}"))
    mocker.patch("os.path.abspath", return_value="/fake/path/config/nifi-config.json")

    # The underlying json.load() will raise the error
    with pytest.raises(json.JSONDecodeError):
        load_config()

