"""
Advanced provenance analysis functions for troubleshooting.
"""

import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from collections import defaultdict, Counter
from datetime import datetime, timedelta


def analyze_dropped_flowfiles(data_cache, time_window_minutes=60, min_drops=5):
    """
    Identifies processors that are dropping FlowFiles, potentially indicating data loss.
    
    Args:
        data_cache: Dictionary of loaded data
        time_window_minutes: Look at drops in the last N minutes
        min_drops: Minimum number of drops to report
    """
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    prov_keys = [k for k in data_cache.keys() if 'provenance' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if not prov_keys:
        print("\nNo provenance data loaded. Ensure 'Provenance' is in 'components_to_monitor'.\n")
        return
    
    console = Console()
    all_prov_df = pd.concat([data_cache[key] for key in prov_keys], ignore_index=True)
    
    # Filter to DROP events only
    drop_df = all_prov_df[all_prov_df['event_type'] == 'DROP'].copy()
    
    if drop_df.empty:
        console.print("\n[bold green]✓ No DROP events found in provenance data.[/bold green]\n")
        return
    
    # Convert timestamps
    drop_df['event_time'] = pd.to_datetime(drop_df['event_time'], unit='ms', errors='coerce')
    drop_df.dropna(subset=['event_time'], inplace=True)
    
    # Filter by time window if specified
    if time_window_minutes:
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        drop_df = drop_df[drop_df['event_time'] >= cutoff_time]
    
    # Group by component
    drop_summary = drop_df.groupby(['component_name', 'component_id']).agg({
        'event_id': 'count',
        'file_size_bytes': 'sum',
        'details': lambda x: x.mode()[0] if not x.empty and x.mode().size > 0 else 'N/A'
    }).reset_index()
    
    drop_summary.columns = ['component_name', 'component_id', 'drop_count', 'total_bytes_dropped', 'common_reason']
    drop_summary = drop_summary[drop_summary['drop_count'] >= min_drops].sort_values('drop_count', ascending=False)
    
    if drop_summary.empty:
        console.print(f"\n[bold green]✓ No processors with {min_drops}+ drops found.[/bold green]\n")
        return
    
    table = Table(title=f"[bold red]Processors Dropping FlowFiles (>= {min_drops} drops)[/bold red]")
    table.add_column("Processor Name", style="magenta")
    table.add_column("Drop Count", style="red", justify="right")
    table.add_column("Total Bytes Dropped", style="red", justify="right")
    table.add_column("Common Reason", style="yellow")
    
    for _, row in drop_summary.iterrows():
        bytes_dropped = f"{row['total_bytes_dropped']:,}" if pd.notna(row['total_bytes_dropped']) else "N/A"
        table.add_row(
            row['component_name'],
            str(row['drop_count']),
            bytes_dropped,
            str(row['common_reason'])[:80]
        )
    
    console.print(table)
    console.print(f"\n[yellow]💡 Tip: Use 'trace-flowfile <uuid>' to see the full lineage of a specific FlowFile[/yellow]\n")


def analyze_data_flow_paths(data_cache, top_n=10):
    """
    Analyzes the most common data flow paths through the system.
    Shows which processor sequences FlowFiles typically follow.
    """
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    prov_keys = [k for k in data_cache.keys() if 'provenance' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if not prov_keys:
        print("\nNo provenance data loaded.\n")
        return
    
    console = Console()
    all_prov_df = pd.concat([data_cache[key] for key in prov_keys], ignore_index=True)
    
    # Build flow paths by FlowFile
    paths = defaultdict(list)
    for _, row in all_prov_df.sort_values('event_time').iterrows():
        flowfile_uuid = row['flowfile_uuid']
        if pd.notna(flowfile_uuid) and flowfile_uuid != 'query_summary':
            component = row['component_name']
            event_type = row['event_type']
            if pd.notna(component):
                paths[flowfile_uuid].append((component, event_type))
    
    # Convert paths to strings and count
    path_strings = []
    for flowfile, events in paths.items():
        if len(events) > 1:  # Only multi-step paths
            path_str = " → ".join([f"{comp}({evt})" for comp, evt in events[:10]])  # Limit to first 10
            path_strings.append(path_str)
    
    if not path_strings:
        console.print("\n[yellow]No multi-step flow paths found. Data may not show complete lineage.[/yellow]\n")
        return
    
    path_counts = Counter(path_strings).most_common(top_n)
    
    table = Table(title=f"[bold cyan]Top {top_n} Data Flow Paths[/bold cyan]")
    table.add_column("Count", style="green", justify="right")
    table.add_column("Flow Path", style="white")
    
    for path, count in path_counts:
        table.add_row(str(count), path)
    
    console.print(table)


def analyze_processing_bottlenecks(data_cache, percentile=90):
    """
    Identifies processing bottlenecks by analyzing event durations.
    Shows which processors take the longest to process FlowFiles.
    """
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    prov_keys = [k for k in data_cache.keys() if 'provenance' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if not prov_keys:
        print("\nNo provenance data loaded.\n")
        return
    
    console = Console()
    all_prov_df = pd.concat([data_cache[key] for key in prov_keys], ignore_index=True)
    
    # Filter out summary records and records without duration
    all_prov_df = all_prov_df[all_prov_df['event_type'] != 'QUERY_SUMMARY'].copy()
    all_prov_df['event_duration'] = pd.to_numeric(all_prov_df['event_duration'], errors='coerce')
    all_prov_df.dropna(subset=['event_duration'], inplace=True)
    
    if all_prov_df.empty:
        console.print("\n[yellow]No event duration data available for analysis.[/yellow]\n")
        return
    
    # Calculate stats by processor
    duration_stats = all_prov_df.groupby(['component_name', 'component_id'])['event_duration'].agg([
        'count', 'mean', 'median', 'std',
        ('p90', lambda x: x.quantile(0.90)),
        ('p95', lambda x: x.quantile(0.95)),
        ('max', 'max')
    ]).reset_index()
    
    duration_stats = duration_stats[duration_stats['count'] >= 10]  # At least 10 events
    duration_stats = duration_stats.sort_values('p90', ascending=False).head(15)
    
    if duration_stats.empty:
        console.print("\n[yellow]Insufficient event data for bottleneck analysis.[/yellow]\n")
        return
    
    table = Table(title="[bold red]Processing Bottlenecks (Slowest Processors)[/bold red]")
    table.add_column("Processor", style="magenta")
    table.add_column("Events", style="cyan", justify="right")
    table.add_column("Mean (ms)", style="yellow", justify="right")
    table.add_column("90th %ile", style="red", justify="right")
    table.add_column("95th %ile", style="red", justify="right")
    table.add_column("Max (ms)", style="red", justify="right")
    
    for _, row in duration_stats.iterrows():
        table.add_row(
            row['component_name'],
            str(int(row['count'])),
            f"{row['mean']:.2f}",
            f"{row['p90']:.2f}",
            f"{row['p95']:.2f}",
            f"{row['max']:.2f}"
        )
    
    console.print(table)
    console.print("\n[yellow]💡 Higher percentiles indicate longer worst-case processing times[/yellow]\n")


def analyze_external_transfers(data_cache):
    """
    Analyzes SEND and RECEIVE events to track data transfers to/from external systems.
    """
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    prov_keys = [k for k in data_cache.keys() if 'provenance' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if not prov_keys:
        print("\nNo provenance data loaded.\n")
        return
    
    console = Console()
    all_prov_df = pd.concat([data_cache[key] for key in prov_keys], ignore_index=True)
    
    # Filter to SEND and RECEIVE events
    transfer_df = all_prov_df[all_prov_df['event_type'].isin(['SEND', 'RECEIVE'])].copy()
    
    if transfer_df.empty:
        console.print("\n[yellow]No SEND/RECEIVE events found. No external transfers detected.[/yellow]\n")
        return
    
    # Analyze by event type and transit URI
    transfer_summary = transfer_df.groupby(['event_type', 'transit_uri', 'component_name']).agg({
        'event_id': 'count',
        'file_size_bytes': 'sum'
    }).reset_index()
    
    transfer_summary.columns = ['event_type', 'transit_uri', 'component_name', 'count', 'total_bytes']
    transfer_summary = transfer_summary.sort_values(['event_type', 'count'], ascending=[True, False])
    
    # Split into sends and receives
    sends = transfer_summary[transfer_summary['event_type'] == 'SEND']
    receives = transfer_summary[transfer_summary['event_type'] == 'RECEIVE']
    
    if not sends.empty:
        console.print("\n[bold cyan]📤 Outbound Transfers (SEND)[/bold cyan]")
        send_table = Table()
        send_table.add_column("Destination", style="blue")
        send_table.add_column("Processor", style="magenta")
        send_table.add_column("Count", style="green", justify="right")
        send_table.add_column("Total Bytes", style="green", justify="right")
        
        for _, row in sends.head(10).iterrows():
            total_bytes = f"{row['total_bytes']:,}" if pd.notna(row['total_bytes']) else "N/A"
            uri = str(row['transit_uri'])[:60] if pd.notna(row['transit_uri']) else "N/A"
            send_table.add_row(uri, row['component_name'], str(row['count']), total_bytes)
        
        console.print(send_table)
    
    if not receives.empty:
        console.print("\n[bold cyan]📥 Inbound Transfers (RECEIVE)[/bold cyan]")
        recv_table = Table()
        recv_table.add_column("Source", style="blue")
        recv_table.add_column("Processor", style="magenta")
        recv_table.add_column("Count", style="green", justify="right")
        recv_table.add_column("Total Bytes", style="green", justify="right")
        
        for _, row in receives.head(10).iterrows():
            total_bytes = f"{row['total_bytes']:,}" if pd.notna(row['total_bytes']) else "N/A"
            uri = str(row['transit_uri'])[:60] if pd.notna(row['transit_uri']) else "N/A"
            recv_table.add_row(uri, row['component_name'], str(row['count']), total_bytes)
        
        console.print(recv_table)
    
    console.print()


def trace_flowfile_lineage(data_cache, flowfile_uuid):
    """
    Traces the complete lineage of a specific FlowFile through the system.
    Shows parent-child relationships and all events.
    """
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    prov_keys = [k for k in data_cache.keys() if 'provenance' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if not prov_keys:
        print("\nNo provenance data loaded.\n")
        return
    
    console = Console()
    all_prov_df = pd.concat([data_cache[key] for key in prov_keys], ignore_index=True)
    
    # Find all events for this FlowFile
    flowfile_events = all_prov_df[all_prov_df['flowfile_uuid'] == flowfile_uuid].copy()
    
    if flowfile_events.empty:
        console.print(f"\n[red]FlowFile {flowfile_uuid} not found in provenance data.[/red]\n")
        return
    
    # Sort by event time
    flowfile_events['event_time'] = pd.to_datetime(flowfile_events['event_time'], unit='ms', errors='coerce')
    flowfile_events = flowfile_events.sort_values('event_time')
    
    console.print(f"\n[bold cyan]🔍 FlowFile Lineage: {flowfile_uuid}[/bold cyan]\n")
    
    # Create a tree visualization
    tree = Tree(f"[bold]FlowFile: {flowfile_uuid}[/bold]")
    
    for idx, row in flowfile_events.iterrows():
        event_time = row['event_time'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row['event_time']) else 'N/A'
        event_type = row['event_type']
        component = row['component_name']
        duration = f"{row['event_duration']}ms" if pd.notna(row['event_duration']) else 'N/A'
        size = f"{row['file_size_bytes']:,} bytes" if pd.notna(row['file_size_bytes']) else 'N/A'
        
        event_color = {
            'CREATE': 'green',
            'RECEIVE': 'cyan',
            'SEND': 'blue',
            'DROP': 'red',
            'ROUTE': 'yellow',
            'FORK': 'magenta',
            'JOIN': 'magenta',
            'CONTENT_MODIFIED': 'yellow',
            'ATTRIBUTES_MODIFIED': 'yellow'
        }.get(event_type, 'white')
        
        node = tree.add(f"[{event_color}]{event_type}[/{event_color}] @ {component}")
        node.add(f"Time: {event_time}")
        node.add(f"Duration: {duration}")
        node.add(f"Size: {size}")
        
        if pd.notna(row['details']):
            node.add(f"Details: {row['details']}")
        
        # Show parent/child relationships
        if pd.notna(row['parent_uuids']) and row['parent_uuids']:
            parents = str(row['parent_uuids'])[:100]
            node.add(f"[dim]Parents: {parents}[/dim]")
        
        if pd.notna(row['child_uuids']) and row['child_uuids']:
            children = str(row['child_uuids'])[:100]
            node.add(f"[dim]Children: {children}[/dim]")
    
    console.print(tree)
    console.print()


def analyze_fork_join_patterns(data_cache):
    """
    Analyzes FORK and JOIN events to identify data splitting and merging patterns.
    """
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    prov_keys = [k for k in data_cache.keys() if 'provenance' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if not prov_keys:
        print("\nNo provenance data loaded.\n")
        return
    
    console = Console()
    all_prov_df = pd.concat([data_cache[key] for key in prov_keys], ignore_index=True)
    
    # Analyze FORK events
    fork_df = all_prov_df[all_prov_df['event_type'] == 'FORK'].copy()
    join_df = all_prov_df[all_prov_df['event_type'] == 'JOIN'].copy()
    
    if fork_df.empty and join_df.empty:
        console.print("\n[yellow]No FORK/JOIN events found in provenance data.[/yellow]\n")
        return
    
    console.print("\n[bold cyan]🔀 Data Splitting and Merging Analysis[/bold cyan]\n")
    
    if not fork_df.empty:
        # Calculate fork ratios (1 parent -> N children)
        fork_df['num_children'] = fork_df['child_uuids'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )
        
        fork_summary = fork_df.groupby('component_name')['num_children'].agg([
            'count', 'mean', 'median', 'max'
        ]).reset_index()
        
        fork_summary.columns = ['component_name', 'fork_count', 'avg_children', 'median_children', 'max_children']
        fork_summary = fork_summary.sort_values('fork_count', ascending=False)
        
        console.print("[bold]FORK Events (Data Splitting):[/bold]")
        fork_table = Table()
        fork_table.add_column("Processor", style="magenta")
        fork_table.add_column("Fork Count", style="green", justify="right")
        fork_table.add_column("Avg Children", style="yellow", justify="right")
        fork_table.add_column("Max Children", style="red", justify="right")
        
        for _, row in fork_summary.head(10).iterrows():
            fork_table.add_row(
                row['component_name'],
                str(int(row['fork_count'])),
                f"{row['avg_children']:.1f}",
                str(int(row['max_children']))
            )
        
        console.print(fork_table)
    
    if not join_df.empty:
        # Calculate join ratios (N parents -> 1 child)
        join_df['num_parents'] = join_df['parent_uuids'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )
        
        join_summary = join_df.groupby('component_name')['num_parents'].agg([
            'count', 'mean', 'median', 'max'
        ]).reset_index()
        
        join_summary.columns = ['component_name', 'join_count', 'avg_parents', 'median_parents', 'max_parents']
        join_summary = join_summary.sort_values('join_count', ascending=False)
        
        console.print("\n[bold]JOIN Events (Data Merging):[/bold]")
        join_table = Table()
        join_table.add_column("Processor", style="magenta")
        join_table.add_column("Join Count", style="green", justify="right")
        join_table.add_column("Avg Parents", style="yellow", justify="right")
        join_table.add_column("Max Parents", style="red", justify="right")
        
        for _, row in join_summary.head(10).iterrows():
            join_table.add_row(
                row['component_name'],
                str(int(row['join_count'])),
                f"{row['avg_parents']:.1f}",
                str(int(row['max_parents']))
            )
        
        console.print(join_table)
    
    console.print()


def analyze_content_modifications(data_cache, top_n=15):
    """
    Identifies processors that frequently modify FlowFile content or attributes.
    """
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    prov_keys = [k for k in data_cache.keys() if 'provenance' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if not prov_keys:
        print("\nNo provenance data loaded.\n")
        return
    
    console = Console()
    all_prov_df = pd.concat([data_cache[key] for key in prov_keys], ignore_index=True)
    
    # Filter to modification events
    mod_df = all_prov_df[all_prov_df['event_type'].isin([
        'CONTENT_MODIFIED', 'ATTRIBUTES_MODIFIED'
    ])].copy()
    
    if mod_df.empty:
        console.print("\n[yellow]No content/attribute modification events found.[/yellow]\n")
        return
    
    # Summarize by processor and event type
    mod_summary = mod_df.groupby(['component_name', 'event_type']).agg({
        'event_id': 'count'
    }).reset_index()
    
    mod_summary.columns = ['component_name', 'event_type', 'count']
    
    # Pivot to show both types side by side
    mod_pivot = mod_summary.pivot_table(
        index='component_name',
        columns='event_type',
        values='count',
        fill_value=0
    ).reset_index()
    
    mod_pivot['total'] = mod_pivot.get('CONTENT_MODIFIED', 0) + mod_pivot.get('ATTRIBUTES_MODIFIED', 0)
    mod_pivot = mod_pivot.sort_values('total', ascending=False).head(top_n)
    
    table = Table(title="[bold cyan]FlowFile Modification Patterns[/bold cyan]")
    table.add_column("Processor", style="magenta")
    table.add_column("Content Modified", style="yellow", justify="right")
    table.add_column("Attributes Modified", style="cyan", justify="right")
    table.add_column("Total", style="green", justify="right")
    
    for _, row in mod_pivot.iterrows():
        table.add_row(
            row['component_name'],
            str(int(row.get('CONTENT_MODIFIED', 0))),
            str(int(row.get('ATTRIBUTES_MODIFIED', 0))),
            str(int(row['total']))
        )
    
    console.print(table)
    console.print("\n[yellow]💡 High modification counts may indicate transformation-heavy processors[/yellow]\n")
