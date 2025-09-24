import os
import gzip
import json
import boto3
from azure.storage.blob import BlobServiceClient
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO

def _get_expected_metric_types(config):
    """
    Generates a list of expected metric folder names based on the collector's configuration.
    """
    expected_types = []
    type_map = {
        "Processor": "nifi_processor", "Connection": "nifi_connection",
        "SystemDiagnostics": "nifi_jvm", "System": "system"
    }
    for component in config.get("components_to_monitor", []):
        if component in type_map:
            expected_types.append(type_map[component])
    for flow in config.get("flows_to_monitor", []):
        flow_name = flow.get("name")
        for component in flow.get("components_to_monitor", []):
            if component in type_map:
                expected_types.append(f"{flow_name}_{type_map[component]}")
    return list(set(expected_types))

def _parse_and_extend_records(file_handle, records, file_identifier):
    """
    Safely parses a JSON file and extends the records list.
    Handles files containing a single object or a list of objects.
    """
    try:
        content = json.load(file_handle)
        if isinstance(content, list):
            records.extend(content)
        elif isinstance(content, dict):
            records.append(content)
        # Silently ignore if content is not a list or dict (e.g., just a string)
    except (json.JSONDecodeError, gzip.BadGzipFile) as e:
        print(f"Warning: Could not read or decode {file_identifier}: {e}")

def _load_records_from_storage(storage_client, storage_type, location, full_prefix):
    """Helper function to fetch and decode records from a specific storage path."""
    records = []
    if storage_type == 'aws':
        paginator = storage_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=location, Prefix=full_prefix)
        for page in pages:
            for obj in page.get('Contents', []):
                key = obj['Key']
                response = storage_client.get_object(Bucket=location, Key=key)
                with gzip.open(BytesIO(response['Body'].read()), 'rt', encoding='utf-8') as f:
                    _parse_and_extend_records(f, records, f"s3://{location}/{key}")
    elif storage_type == 'azure':
        blob_list = storage_client.list_blobs(name_starts_with=full_prefix)
        for blob in blob_list:
            blob_client_instance = storage_client.get_blob_client(blob)
            downloader = blob_client_instance.download_blob()
            with gzip.open(BytesIO(downloader.readall()), 'rt', encoding='utf-8') as f:
                _parse_and_extend_records(f, records, f"blob {blob.name}")
    return records

def load_all_data(config, secrets, start_date_str, end_date_str=None):
    """
    Factory function to load data from the configured storage backend for a date or date range.
    """
    storage_type = secrets.get("storage", "local")
    expected_metric_types = _get_expected_metric_types(config)
    all_data_accumulator = {metric_type: [] for metric_type in expected_metric_types}

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else start_date
    except ValueError:
        print(f"Error: Invalid date format. Please use YYYY-MM-DD.")
        return {}
    
    if end_date < start_date:
        print("Error: End date cannot be before start date.")
        return {}

    storage_client, location = None, None
    if storage_type == "aws":
        storage_client = boto3.client("s3", aws_access_key_id=secrets["aws_access_key"], aws_secret_access_key=secrets["aws_secret_key"])
        location = secrets["s3_bucket"]
    elif storage_type == "azure":
        blob_service_client = BlobServiceClient.from_connection_string(secrets["azure_connection_string"])
        location = secrets.get("azure_container_name", "nifi-metrics")
        storage_client = blob_service_client.get_container_client(location)
    elif storage_type != "local":
        print(f"Error: Unsupported storage type '{storage_type}'")
        return None

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"Loading data for {date_str}...")

        for metric_type in expected_metric_types:
            records = []
            if storage_type == "local":
                base_path = secrets.get("local_output_directory", "/tmp/nifi_metrics")
                metric_path = os.path.join(base_path, f"{metric_type}-metrics", date_str)
                if os.path.isdir(metric_path):
                    for filename in os.listdir(metric_path):
                        if filename.endswith(".json.gz"):
                            full_path = os.path.join(metric_path, filename)
                            with gzip.open(full_path, 'rt', encoding='utf-8') as f:
                                _parse_and_extend_records(f, records, filename)
            else:
                full_prefix = f"{metric_type}-metrics/{date_str}/"
                records = _load_records_from_storage(storage_client, storage_type, location, full_prefix)
            
            if records:
                all_data_accumulator[metric_type].extend(records)
        
        current_date += timedelta(days=1)

    final_data = {}
    for metric_type, all_records in all_data_accumulator.items():
        if all_records:
            final_data[metric_type] = pd.DataFrame(all_records)
            print(f"  - Loaded a total of {len(all_records)} records for {metric_type}")

    return final_data


