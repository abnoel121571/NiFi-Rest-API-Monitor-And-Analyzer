import os
import boto3
import gzip
import json
import uuid
import logging
from datetime import datetime
from io import BytesIO
from azure.storage.blob import BlobServiceClient

def _compress_json(data):
    """Compresses a list of dictionaries into a gzipped JSON byte string."""
    out = BytesIO()
    with gzip.GzipFile(fileobj=out, mode='wb') as f:
        f.write(json.dumps(data).encode('utf-8'))
    return out.getvalue()

def _write_metrics(storage_type, client, path_prefix, collection_id, hostname, collection_timestamp, **metric_collections):
    """Generic function to write multiple metric collections to cloud storage or local disk."""
    date_path = datetime.utcnow().strftime("%Y-%m-%d")

    for name, data in metric_collections.items():
        if not data:
            logging.info(f"Skipping empty metric collection: {name}")
            continue
        
        for entry in data:
            entry["collection_id"] = collection_id
            entry["hostname"] = hostname
            entry["collection_timestamp"] = collection_timestamp

        file_path_suffix = f"{name}-metrics/{date_path}/{hostname}_{name}_{collection_id}.json.gz"
        compressed_data = _compress_json(data)
        
        try:
            if storage_type == "aws":
                client.put_object(Bucket=path_prefix, Key=file_path_suffix, Body=compressed_data)
                print(f"[AWS] Wrote {name} metrics to s3://{path_prefix}/{file_path_suffix}")
            elif storage_type == "azure":
                blob_client = client.get_blob_client(container=path_prefix, blob=file_path_suffix)
                blob_client.upload_blob(compressed_data, overwrite=True)
                print(f"[Azure] Wrote {name} metrics to {path_prefix}/{file_path_suffix}")
            elif storage_type == "local":
                full_path = os.path.join(path_prefix, file_path_suffix)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'wb') as f:
                    f.write(compressed_data)
                print(f"[Local] Wrote {name} metrics to {full_path}")

        except Exception as e:
            logging.error(f"Failed to write '{name}' metrics to {storage_type}: {e}")

def write_to_aws(secrets, collection_id, hostname, collection_timestamp, **metric_collections):
    """Writes metrics to AWS S3."""
    s3 = boto3.client("s3", aws_access_key_id=secrets["aws_access_key"], aws_secret_access_key=secrets["aws_secret_key"])
    bucket = secrets.get("s3_bucket", "nifi-metrics")
    _write_metrics("aws", s3, bucket, collection_id, hostname, collection_timestamp, **metric_collections)

def write_to_azure(secrets, collection_id, hostname, collection_timestamp, **metric_collections):
    """Writes metrics to Azure Blob Storage."""
    blob_service = BlobServiceClient.from_connection_string(secrets["azure_connection_string"])
    container = secrets.get("azure_container_name", "nifi-metrics")
    _write_metrics("azure", blob_service, container, collection_id, hostname, collection_timestamp, **metric_collections)

def write_to_local(secrets, collection_id, hostname, collection_timestamp, **metric_collections):
    """Writes metrics to the local filesystem."""
    output_directory = secrets.get("local_output_directory", "/tmp/nifi_metrics")
    _write_metrics("local", None, output_directory, collection_id, hostname, collection_timestamp, **metric_collections)

