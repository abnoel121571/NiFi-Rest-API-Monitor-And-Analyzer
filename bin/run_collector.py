#!/Users/anoel/python3/myenv/bin/python
import os
import sys
import time
import uuid
import argparse
import logging
import json
from datetime import datetime
from urllib.parse import urlparse

# Add lib directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from lib.config_loader import load_config, load_secrets
    from lib.nifi_client import (
        get_nifi_processors, get_nifi_connections, get_nifi_system_diagnostics,
        get_nifi_controller_services, get_nifi_reporting_tasks, get_nifi_bulletins
    )
    from lib.metrics_parser import (
        extract_processor_metrics, extract_connection_metrics, extract_jvm_metrics,
        extract_controller_service_metrics, extract_reporting_task_metrics, extract_bulletin_metrics
    )
    from lib.system_metrics import get_system_metrics
    from lib.storage_writer import write_to_aws, write_to_azure, write_to_local
    from lib.nifi_auth import fetch_nifi_token
    import requests
    import urllib3
except ImportError as e:
    print(f"Error: A required module is missing: {e}")
    print("Please ensure you have installed the project's dependencies with 'pip install -e .'")
    sys.exit(1)

# Disable SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def setup_logging(log_level_str):
    """Configures the logging format and level."""
    numeric_level = getattr(logging, log_level_str.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="NiFi Metrics Collector")
    parser.add_argument("--hostname", default="localhost", help="Hostname of the NiFi instance to monitor. Replaces {hostname} in config. Defaults to 'localhost'.")
    parser.add_argument("--once", action="store_true", help="Run all collections once and exit.")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Override configured log level.")
    return parser.parse_args()

def process_config_template(config, hostname):
    """Replaces {hostname} placeholders in the configuration."""
    config_str = json.dumps(config)
    config_str = config_str.replace("{hostname}", hostname)
    return json.loads(config_str)

def collect_and_store(config, secrets, auth, token, components_to_run, flow_config=None):
    """Collects metrics for a given set of components and writes them to storage."""
    if not components_to_run:
        return

    collection_id = str(uuid.uuid4())
    collection_timestamp = datetime.utcnow().isoformat()
    timeout = config.get("nifi_timeout_seconds", 10)
    hostname = urlparse(config["nifi_api_url"]).hostname
    collections = {}

    pg_id = flow_config['process_group_id'] if flow_config else 'root'
    flow_name = flow_config['name'] if flow_config else None
    collection_prefix = f"{flow_name}_" if flow_name else ""

    if flow_config:
        processor_filter = flow_config.get("monitored_processor_names")
    else:
        processor_filter = config.get("monitored_processor_names")

    # --- Flow-Specific Components ---
    if "Processor" in components_to_run:
        try:
            processors = get_nifi_processors(config["nifi_api_url"], auth, token, timeout, pg_id)
            key = f"{collection_prefix}nifi_processor"
            collections[key] = extract_processor_metrics(
                processors["processors"], config["processor_metrics"], flow_name, processor_filter
            )
        except Exception as e:
            logging.error(f"Failed to collect Processor metrics for '{flow_name or 'root'}': {e}")

    if "Connection" in components_to_run:
        try:
            connections = get_nifi_connections(config["nifi_api_url"], auth, token, timeout, pg_id)
            key = f"{collection_prefix}nifi_connection"
            collections[key] = extract_connection_metrics(connections["connections"], config["connection_metrics"], flow_name)
        except Exception as e:
            logging.error(f"Failed to collect Connection metrics for '{flow_name or 'root'}': {e}")

    # --- Global Components ---
    if "System" in components_to_run:
        collections["system"] = get_system_metrics()
    
    if "SystemDiagnostics" in components_to_run:
        try:
            diagnostics = get_nifi_system_diagnostics(config["nifi_api_url"], auth, token, timeout)
            collections["nifi_jvm"] = extract_jvm_metrics(diagnostics, config["jvm_metrics"])
        except Exception as e:
            logging.error(f"Failed to collect SystemDiagnostics: {e}")

    if "ControllerServices" in components_to_run:
        try:
            services = get_nifi_controller_services(config["nifi_api_url"], auth, token, timeout)
            collections["nifi_controller_service"] = extract_controller_service_metrics(services["controllerServices"], config["controller_service_metrics"])
        except Exception as e:
            logging.error(f"Failed to collect ControllerServices: {e}")

    if "ReportingTasks" in components_to_run:
        try:
            tasks = get_nifi_reporting_tasks(config["nifi_api_url"], auth, token, timeout)
            collections["nifi_reporting_task"] = extract_reporting_task_metrics(tasks["reportingTasks"], config["reporting_task_metrics"])
        except Exception as e:
            logging.error(f"Failed to collect ReportingTasks: {e}")

    if "Bulletins" in components_to_run:
        try:
            bulletins = get_nifi_bulletins(config["nifi_api_url"], auth, token, timeout)
            collections["nifi_bulletin"] = extract_bulletin_metrics(bulletins.get("bulletinBoard", {}).get("bulletins", []))
        except Exception as e:
            logging.error(f"Failed to collect Bulletins: {e}")

    if not collections:
        return
        
    storage_type = secrets.get("storage", "local")
    writer_map = {"aws": write_to_aws, "azure": write_to_azure, "local": write_to_local}
    if storage_type in writer_map:
        writer_map[storage_type](secrets, collection_id, hostname, collection_timestamp, **collections)
    else:
        logging.warning(f"Unknown storage type '{storage_type}' specified.")


def main():
    """Main execution function."""
    args = parse_args()
    secrets = load_secrets()
    
    config_template = load_config()
    config = process_config_template(config_template, args.hostname)

    log_level = args.log_level or config.get("log_level", "INFO")
    setup_logging(log_level)

    logging.info(f"Starting NiFi Metrics Collector for host: {args.hostname}")
    
    auth, token, token_issued_at = None, None, None
    if config.get("use_token_auth", False):
        try:
            token = fetch_nifi_token(config["nifi_token_url"], secrets["nifi_username"], secrets["nifi_password"])
            token_issued_at = datetime.utcnow()
        except Exception as e:
            logging.error(f"Failed to acquire initial token, exiting: {e}")
            return
    else:
        from requests.auth import HTTPBasicAuth
        auth = HTTPBasicAuth(secrets["nifi_username"], secrets["nifi_password"])

    if args.once:
        logging.info("Running one-time collection for all configured components and flows.")
        collect_and_store(config, secrets, auth, token, config.get("components_to_monitor", []))
        for flow in config.get("flows_to_monitor", []):
            collect_and_store(config, secrets, auth, token, flow["components_to_monitor"], flow)
        return

    last_global_times = {}
    last_flow_times = {flow['name']: datetime.min for flow in config.get("flows_to_monitor", [])}

    while True:
        try:
            config_template = load_config()
            config = process_config_template(config_template, args.hostname)
        except Exception as e:
            logging.error(f"Failed to reload config, skipping cycle: {e}")
            time.sleep(10)
            continue
        
        if config.get("use_token_auth", False):
            if (datetime.utcnow() - token_issued_at).total_seconds() > config.get("nifi_token_lifetime_seconds", 43200) - 600:
                try:
                    token = fetch_nifi_token(config["nifi_token_url"], secrets["nifi_username"], secrets["nifi_password"])
                    token_issued_at = datetime.utcnow()
                    logging.info("Auto-renewed NiFi token.")
                except Exception as e:
                    logging.error(f"Token renewal failed: {e}")
                    time.sleep(60)
                    continue
        
        now = datetime.utcnow()
        
        global_intervals = config.get("collection_intervals_seconds", {})
        default_interval = global_intervals.get("global_default", 300)
        global_components_to_run = []
        for component in config.get("components_to_monitor", []):
            interval = global_intervals.get(component, default_interval)
            if (now - last_global_times.get(component, datetime.min)).total_seconds() >= interval:
                global_components_to_run.append(component)
        
        if global_components_to_run:
            logging.info(f"Triggering global collection for: {global_components_to_run}")
            collect_and_store(config, secrets, auth, token, global_components_to_run)
            for component in global_components_to_run:
                last_global_times[component] = now

        for flow in config.get("flows_to_monitor", []):
            flow_name = flow['name']
            interval = flow['interval_seconds']
            if (now - last_flow_times.get(flow_name, datetime.min)).total_seconds() >= interval:
                logging.info(f"Triggering flow collection for: '{flow_name}'")
                collect_and_store(config, secrets, auth, token, flow["components_to_monitor"], flow)
                last_flow_times[flow_name] = now
        
        time.sleep(1)

if __name__ == "__main__":
    main()



