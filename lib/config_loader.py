import os
import json
import logging

def load_json_file(file_path):
    """Loads a JSON file from a given path."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found at: {file_path}")
        raise
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in configuration file: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Failed to load configuration file {file_path}: {e}")
        raise

def load_config(path="config/nifi-config.json"):
    """Loads the main configuration file."""
    abs_path = os.path.join(os.path.dirname(__file__), "..", path)
    return load_json_file(os.path.abspath(abs_path))

def load_secrets(path="config/secrets.json"):
    """Loads the secrets file."""
    abs_path = os.path.join(os.path.dirname(__file__), "..", path)
    return load_json_file(os.path.abspath(abs_path))

