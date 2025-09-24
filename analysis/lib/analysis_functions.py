import pandas as pd
from rich.console import Console
from rich.table import Table
import re

def _get_latest_records(df, group_by_col='id'):
    """Helper to get the most recent record for each component, handling NaT timestamps."""
    if 'collection_timestamp' not in df.columns:
        return df
    df['collection_timestamp'] = pd.to_datetime(df['collection_timestamp'], errors='coerce')
    df.dropna(subset=['collection_timestamp'], inplace=True)
    return df.sort_values('collection_timestamp').drop_duplicates(subset=[group_by_col], keep='last')

def _parse_bytes(size_str):
    """Converts a size string like '1.2 GB' to bytes."""
    if not isinstance(size_str, str):
        return 0
    size_str = size_str.upper().strip()
    match = re.match(r'([\d\.,]+)\s*([A-Z]+)', size_str)
    if not match: return 0
    val_str, unit = match.groups()
    val = float(val_str.replace(',', ''))
    unit_map = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
    return val * unit_map.get(unit, 1)

def show_health_summary(data_cache):
    """Displays a high-level health summary of the loaded data."""
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded. Please use the 'load' command first.\n")
        return

    console = Console()
    console.print("\n[bold cyan]--- NiFi Health Summary ---[/bold cyan]")

    # Processor Status Summary
    proc_keys = [k for k in data_cache.keys() if 'processor' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if proc_keys:
        all_proc_df = pd.concat([data_cache[key] for key in proc_keys], ignore_index=True)
        df_latest = _get_latest_records(all_proc_df)
        status_counts = df_latest['runStatus'].value_counts()
        
        table = Table(title="Processor Status Counts (Latest Snapshot)")
        table.add_column("Status", style="magenta")
        table.add_column("Count", style="green", justify="right")
        for status, count in status_counts.items():
            table.add_row(status, str(count))
        console.print(table)
    else:
        console.print("[yellow]No valid processor metrics found.[/yellow]")

    # Connection Backlog Summary
    conn_keys = [k for k in data_cache.keys() if 'connection' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if conn_keys:
        all_conn_df = pd.concat([data_cache[key] for key in conn_keys], ignore_index=True)
        # Ensure 'queuedCount' is numeric for sorting, handle potential non-numeric values
        all_conn_df['queuedCount_int'] = pd.to_numeric(all_conn_df['queuedCount'].str.replace(',', ''), errors='coerce').fillna(0).astype(int)
        df_latest = _get_latest_records(all_conn_df)
        top_5_backlog = df_latest.nlargest(5, 'queuedCount_int')
        
        table = Table(title="Top 5 Connection Queues by Backlog (Latest Snapshot)")
        table.add_column("Hostname", style="yellow")
        table.add_column("Flow Name", style="blue")
        table.add_column("Connection Name", style="magenta")
        table.add_column("Queued Count", style="red", justify="right")
        
        for _, row in top_5_backlog.iterrows():
            flow_name = row.get('flow_name', 'root')
            table.add_row(row['hostname'], flow_name, row['name'], row['queuedCount'])
        console.print(table)
    else:
        console.print("[yellow]No valid connection metrics found.[/yellow]")

    # JVM Metrics Summary
    if 'nifi_jvm' in data_cache and isinstance(data_cache['nifi_jvm'], pd.DataFrame):
        jvm_df = _get_latest_records(data_cache['nifi_jvm'])
        if not jvm_df.empty:
            console.print("\n[bold green]JVM Health (Latest Snapshot)[/bold green]")
            for _, row in jvm_df.iterrows():
                console.print(f"  Hostname: [yellow]{row['hostname']}[/yellow]")
                console.print(f"  Heap Usage: [cyan]{row.get('heapUsage', 'N/A')}[/cyan] (Used: [cyan]{row.get('heapUsed', 'N/A')}[/cyan] / Max: [cyan]{row.get('maxHeap', 'N/A')}[/cyan])")
                console.print(f"  Thread Count: [cyan]{row.get('threadCount', 'N/A')}[/cyan] (Daemon: [cyan]{row.get('daemonThreadCount', 'N/A')}[/cyan])")
                console.print(f"  FlowFile Repo Used: [cyan]{row.get('flowFileRepositoryUsage', {}).get('usedSpace', 'N/A')}[/cyan]")
                if row.get('contentRepositoryUsage'):
                    for repo in row['contentRepositoryUsage']:
                        console.print(f"  Content Repo ({repo.get('identifier', 'N/A')}) Used: [cyan]{repo.get('usedSpace', 'N/A')}[/cyan]")
        else:
            console.print("[yellow]No valid JVM metrics found.[/yellow]")
    else:
        console.print("[yellow]No JVM metrics found. Ensure 'SystemDiagnostics' is in 'components_to_monitor'.[/yellow]")

    # Cluster Summary
    if 'nifi_cluster_summary' in data_cache and isinstance(data_cache['nifi_cluster_summary'], pd.DataFrame):
        cluster_df = _get_latest_records(data_cache['nifi_cluster_summary'])
        if not cluster_df.empty:
            console.print("\n[bold green]Cluster Health (Latest Snapshot)[/bold green]")
            overall_summary = cluster_df[cluster_df['id'] == 'cluster_summary'].iloc[0]
            status_color = "green" if overall_summary.get('connectedToCluster') else "red"
            console.print(f"  Clustered: [cyan]{overall_summary.get('clustered', 'N/A')}[/cyan]")
            console.print(f"  Connected to Cluster: [{status_color}]{overall_summary.get('connectedToCluster', 'N/A')}[/{status_color}]")
            console.print(f"  Total Nodes: [cyan]{overall_summary.get('totalNodeCount', 'N/A')}[/cyan]")
            console.print(f"  Connected Nodes: [green]{overall_summary.get('connectedNodeCount', 'N/A')}[/green]")
            console.print(f"  Disconnected Nodes: [red]{overall_summary.get('disconnectedNodeCount', 'N/A')}[/red]")
            console.print(f"  Heartbeat Count: [cyan]{overall_summary.get('heartbeatCount', 'N/A')}[/cyan]")
        else:
            console.print("[yellow]No valid cluster summary metrics found.[/yellow]")
    else:
        console.print("[yellow]No Cluster Summary metrics found. Ensure 'ClusterSummary' is in 'components_to_monitor'.[/yellow]")


def list_stopped_processors(data_cache):
    """Finds and lists all processors that are not in a RUNNING state."""
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
        
    proc_keys = [k for k in data_cache.keys() if 'processor' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if not proc_keys:
        print("\nNo processor data loaded. Ensure 'Processor' is in 'components_to_monitor'.\n")
        return

    console = Console()
    all_proc_df = pd.concat([data_cache[key] for key in proc_keys], ignore_index=True)
    df = _get_latest_records(all_proc_df)
    stopped_df = df[df['runStatus'] != 'RUNNING']

    if stopped_df.empty:
        console.print("\n[bold green]✓ All processors are running.[/bold green]\n")
        return

    table = Table(title="[bold red]Stopped/Non-Running Processors (Latest Snapshot)[/bold red]")
    table.add_column("Hostname", style="yellow")
    table.add_column("Flow Name", style="blue")
    table.add_column("Processor Name", style="magenta")
    table.add_column("Status", style="red")

    for _, row in stopped_df.iterrows():
        flow_name = row.get('flow_name', 'root')
        table.add_row(row['hostname'], flow_name, row['name'], row['runStatus'])
    console.print(table)

def find_back_pressure(data_cache, threshold_percent=80.0):
    """Identifies connection queues nearing their back pressure thresholds."""
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return

    conn_keys = [k for k in data_cache.keys() if 'connection' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if not conn_keys:
        print("\nNo connection data loaded. Ensure 'Connection' is in 'components_to_monitor'.\n")
        return

    console = Console()
    all_conn_df = pd.concat([data_cache[key] for key in conn_keys], ignore_index=True)
    df = _get_latest_records(all_conn_df)

    back_pressure_queues = []
    for _, row in df.iterrows():
        queued_size_bytes = _parse_bytes(row.get('queuedSize'))
        back_pressure_size_bytes = _parse_bytes(row.get('backPressureDataSizeThreshold'))
        
        # Handle object count threshold if data size is not set or zero
        queued_count = pd.to_numeric(row.get('queuedCount', '0').replace(',', ''), errors='coerce').fillna(0)
        back_pressure_count = pd.to_numeric(row.get('backPressureObjectThreshold', 0), errors='coerce').fillna(0)

        is_back_pressure_by_size = False
        if back_pressure_size_bytes > 0:
            current_percent_size = (queued_size_bytes / back_pressure_size_bytes) * 100
            if current_percent_size >= threshold_percent:
                is_back_pressure_by_size = True

        is_back_pressure_by_count = False
        if back_pressure_count > 0:
            current_percent_count = (queued_count / back_pressure_count) * 100
            if current_percent_count >= threshold_percent:
                is_back_pressure_by_count = True
        
        if is_back_pressure_by_size or is_back_pressure_by_count:
            back_pressure_queues.append(row)

    if not back_pressure_queues:
        console.print(f"\n[bold green]✓ No queues nearing back pressure ({threshold_percent:.1f}% threshold).[/bold green]\n")
        return

    table = Table(title=f"[bold red]Queues Nearing Back Pressure ({threshold_percent:.1f}% Threshold) (Latest Snapshot)[/bold red]")
    table.add_column("Hostname", style="yellow")
    table.add_column("Flow Name", style="blue")
    table.add_column("Connection Name", style="magenta")
    table.add_column("Queued", style="red")
    table.add_column("Back Pressure Size", style="red")
    table.add_column("Back Pressure Count", style="red")

    for row in back_pressure_queues:
        flow_name = row.get('flow_name', 'root')
        table.add_row(
            row['hostname'],
            flow_name,
            f"{row['name']}",
            f"{row.get('queuedCount', 'N/A')} ({row.get('queuedSize', 'N/A')})",
            row.get('backPressureDataSizeThreshold', 'N/A'),
            str(row.get('backPressureObjectThreshold', 'N/A'))
        )
    console.print(table)


def find_slow_processors(data_cache, percentile_threshold=90.0):
    """Identifies processors with unusually high average lineage duration."""
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return

    proc_keys = [k for k in data_cache.keys() if 'processor' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if not proc_keys:
        print("\nNo processor data loaded. Ensure 'Processor' is in 'components_to_monitor'.\n")
        return

    console = Console()
    all_proc_df = pd.concat([data_cache[key] for key in proc_keys], ignore_index=True)
    df = _get_latest_records(all_proc_df)

    # Ensure 'nifi_average_lineage_duration' is numeric
    df['nifi_average_lineage_duration'] = pd.to_numeric(df['nifi_average_lineage_duration'], errors='coerce')
    df.dropna(subset=['nifi_average_lineage_duration'], inplace=True)

    if df.empty:
        console.print("\n[bold yellow]No processor lineage duration data available for analysis.[/bold yellow]\n")
        return

    # Calculate the threshold based on the specified percentile
    threshold_value = df['nifi_average_lineage_duration'].quantile(percentile_threshold / 100.0)

    slow_processors_df = df[df['nifi_average_lineage_duration'] >= threshold_value].sort_values(
        'nifi_average_lineage_duration', ascending=False
    )

    if slow_processors_df.empty:
        console.print(f"\n[bold green]✓ No processors found with lineage duration above the {percentile_threshold}th percentile ({threshold_value:.2f} ms).[/bold green]\n")
        return

    table = Table(title=f"[bold red]Slow Processors (Lineage Duration >= {threshold_value:.2f} ms - {percentile_threshold}th percentile) (Latest Snapshot)[/bold red]")
    table.add_column("Hostname", style="yellow")
    table.add_column("Flow Name", style="blue")
    table.add_column("Processor Name", style="magenta")
    table.add_column("Avg Lineage Duration (ms)", style="red", justify="right")

    for _, row in slow_processors_df.iterrows():
        flow_name = row.get('flow_name', 'root')
        table.add_row(
            row['hostname'],
            flow_name,
            row['name'],
            f"{row['nifi_average_lineage_duration']:.2f}"
        )
    console.print(table)

def view_bulletins(data_cache, level_filter=None):
    """Displays bulletins from the NiFi bulletin board, with optional filtering."""
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
        
    bulletin_key = 'nifi_bulletin'
    if bulletin_key not in data_cache or not isinstance(data_cache.get(bulletin_key), pd.DataFrame):
        print("\nNo bulletin data loaded. Ensure 'Bulletins' is in 'components_to_monitor'.\n")
        return

    console = Console()
    df = data_cache[bulletin_key].copy()
    
    # Bulletins can be duplicated across collections, so we drop duplicates based on ID
    df.drop_duplicates(subset=['id'], keep='last', inplace=True)

    if level_filter:
        df = df[df['bulletin.level'].str.upper() == level_filter.upper()]

    if df.empty:
        level_msg = f" with level '{level_filter.upper()}'" if level_filter else ""
        console.print(f"\n[bold green]✓ No bulletins{level_msg} found.[/bold green]\n")
        return

    title = "[bold yellow]NiFi Bulletins (Most Recent 20)[/bold yellow]"
    if level_filter:
        title += f" (Level: {level_filter.upper()})"

    table = Table(title=title)
    table.add_column("Timestamp", style="cyan")
    table.add_column("Level", style="magenta")
    table.add_column("Source Name", style="blue")
    table.add_column("Message", style="white")

    df['bulletin.timestamp'] = pd.to_datetime(df['bulletin.timestamp'])
    for _, row in df.sort_values('bulletin.timestamp', ascending=False).head(20).iterrows():
        level = row['bulletin.level']
        level_style = "red" if level == 'ERROR' else "yellow" if level == 'WARN' else 'white'
        table.add_row(
            row['bulletin.timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            f"[{level_style}]{level}[/{level_style}]",
            row.get('bulletin.sourceName', 'N/A'),
            row['bulletin.message']
        )
    console.print(table)

def list_invalid_services(data_cache):
    """Finds and lists all controller services that are not in a VALID state."""
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
        
    service_key = 'nifi_controller_service'
    if service_key not in data_cache or not isinstance(data_cache.get(service_key), pd.DataFrame):
        print("\nNo controller service data loaded. Ensure 'ControllerServices' is in 'components_to_monitor'.\n")
        return

    console = Console()
    df = _get_latest_records(data_cache[service_key])
    invalid_df = df[df['validationStatus'] != 'VALID']

    if invalid_df.empty:
        console.print("\n[bold green]✓ All controller services are valid.[/bold green]\n")
        return

    table = Table(title="[bold red]Invalid Controller Services (Latest Snapshot)[/bold red]")
    table.add_column("Hostname", style="yellow")
    table.add_column("Service Name", style="magenta")
    table.add_column("Status", style="red")
    table.add_column("State", style="cyan")

    for _, row in invalid_df.iterrows():
        table.add_row(
            row['hostname'],
            row['name'],
            row['validationStatus'],
            row.get('runStatus', 'N/A')
        )
    console.print(table)

def check_reporting_tasks(data_cache):
    """Checks the status of all reporting tasks."""
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
        
    task_key = 'nifi_reporting_task'
    if task_key not in data_cache or not isinstance(data_cache.get(task_key), pd.DataFrame):
        print("\nNo reporting task data loaded. Ensure 'ReportingTasks' is in 'components_to_monitor'.\n")
        return

    console = Console()
    df = _get_latest_records(data_cache[task_key])
    
    table = Table(title="[bold cyan]Reporting Task Status (Latest Snapshot)[/bold cyan]")
    table.add_column("Hostname", style="yellow")
    table.add_column("Task Name", style="magenta")
    table.add_column("Status", style="white")

    for _, row in df.iterrows():
        status = row.get('runStatus', 'N/A')
        status_style = "green" if status == 'RUNNING' else "red"
        table.add_row(
            row['hostname'],
            row['name'],
            f"[{status_style}]{status}[/{status_style}]"
        )
    console.print(table)

def show_cluster_health(data_cache):
    """Displays detailed cluster health and node status."""
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    cluster_key = 'nifi_cluster_summary'
    if cluster_key not in data_cache or not isinstance(data_cache.get(cluster_key), pd.DataFrame):
        print("\nNo cluster summary data loaded. Ensure 'ClusterSummary' is in 'components_to_monitor'.\n")
        return

    console = Console()
    df = _get_latest_records(data_cache[cluster_key])

    overall_summary_df = df[df['id'] == 'cluster_summary']
    node_summary_df = df[df['id'].str.startswith('cluster_node_')]

    if overall_summary_df.empty and node_summary_df.empty:
        console.print("\n[yellow]No detailed cluster health data available.[/yellow]\n")
        return

    console.print("\n[bold cyan]--- NiFi Cluster Health ---[/bold cyan]")

    if not overall_summary_df.empty:
        overall_summary = overall_summary_df.iloc[0]
        console.print("\n[bold underline]Overall Cluster Status:[/bold underline]")
        status_color = "green" if overall_summary.get('connectedToCluster') else "red"
        console.print(f"  Clustered: [cyan]{overall_summary.get('clustered', 'N/A')}[/cyan]")
        console.print(f"  Connected to Cluster: [{status_color}]{overall_summary.get('connectedToCluster', 'N/A')}[/{status_color}]")
        console.print(f"  Total Nodes: [cyan]{overall_summary.get('totalNodeCount', 'N/A')}[/cyan]")
        console.print(f"  Connected Nodes: [green]{overall_summary.get('connectedNodeCount', 'N/A')}[/green]")
        console.print(f"  Disconnected Nodes: [red]{overall_summary.get('disconnectedNodeCount', 'N/A')}[/red]")
        console.print(f"  Heartbeat Count: [cyan]{overall_summary.get('heartbeatCount', 'N/A')}[/cyan]")
    else:
        console.print("[yellow]No overall cluster summary found.[/yellow]")

    if not node_summary_df.empty:
        console.print("\n[bold underline]Individual Node Status:[/bold underline]")
        table = Table(title="Cluster Node Details (Latest Snapshot)")
        table.add_column("Node ID", style="cyan")
        table.add_column("Address", style="blue")
        table.add_column("Status", style="magenta")
        table.add_column("Active Threads", style="green", justify="right")
        table.add_column("Queued", style="yellow")
        table.add_column("Heap Usage", style="white")
        table.add_column("Disk Usage (Root)", style="white")
        table.add_column("Uptime", style="white")

        for _, row in node_summary_df.iterrows():
            status_color = "green" if row.get('status') == 'CONNECTED' else "red"
            disk_usage_root = "N/A"
            if row.get('diskUsage') and isinstance(row['diskUsage'], list):
                root_disk = next((d for d in row['diskUsage'] if d.get('identifier') == '/'), None)
                if root_disk:
                    disk_usage_root = f"{root_disk.get('usedSpace', 'N/A')} / {root_disk.get('totalSpace', 'N/A')}"
                else: # Fallback to first disk if root not found
                    disk_usage_root = f"{row['diskUsage'][0].get('usedSpace', 'N/A')} / {row['diskUsage'][0].get('totalSpace', 'N/A')}"

            table.add_row(
                row.get('nodeId', 'N/A'),
                row.get('address', 'N/A'),
                f"[{status_color}]{row.get('status', 'N/A')}[/{status_color}]",
                str(row.get('activeThreadCount', 'N/A')),
                row.get('queued', 'N/A'),
                row.get('heapUsage', 'N/A'),
                disk_usage_root,
                row.get('uptime', 'N/A')
            )
        console.print(table)
    else:
        console.print("[yellow]No individual node summary found.[/yellow]")

def show_jvm_heap_metrics(data_cache):
    """Displays detailed JVM heap and garbage collection metrics."""
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
        
    jvm_key = 'nifi_jvm'
    if jvm_key not in data_cache or not isinstance(data_cache.get(jvm_key), pd.DataFrame):
        print("\nNo JVM data loaded. Ensure 'SystemDiagnostics' is in 'components_to_monitor'.\n")
        return

    console = Console()
    df = _get_latest_records(data_cache[jvm_key])

    if df.empty:
        console.print("\n[yellow]No JVM heap metrics available for analysis.[/yellow]\n")
        return

    console.print("\n[bold cyan]--- NiFi JVM Heap Metrics (Latest Snapshot) ---[/bold cyan]")

    table = Table(title="JVM Memory Usage")
    table.add_column("Hostname", style="yellow")
    table.add_column("Heap Used", style="magenta")
    table.add_column("Heap Max", style="cyan")
    table.add_column("Heap Usage %", style="green", justify="right")
    table.add_column("Non-Heap Used", style="magenta")
    table.add_column("Non-Heap Max", style="cyan")
    table.add_column("Non-Heap Usage %", style="green", justify="right")

    for _, row in df.iterrows():
        console.print(f"\n[bold underline]Host: {row['hostname']}[/bold underline]")
        table.add_row(
            row['hostname'],
            row.get('heapUsed', 'N/A'),
            row.get('maxHeap', 'N/A'),
            row.get('heapUsage', 'N/A'),
            row.get('nonHeapUsed', 'N/A'),
            row.get('maxNonHeap', 'N/A'),
            row.get('nonHeapUsage', 'N/A')
        )
    console.print(table)

    # Add Garbage Collection details if available (assuming these are collected)
    # The current nifi_jvm metrics in config.json.template do not include GC specifics like
    # 'totalGCTime' or 'totalGCCollectionCount' directly from the system-diagnostics.
    # If those were added to the config, they could be displayed here.
    # For now, we'll just note their potential absence.
    console.print("\n[bold yellow]Note:[/bold yellow] Detailed Garbage Collection metrics (e.g., total GC time, collection count) can be displayed here if configured in 'jvm_metrics' in nifi-config.json.")

