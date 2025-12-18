"""
Advanced analysis functions for time-series and correlation analysis.
"""

import pandas as pd
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime, timedelta
from collections import defaultdict


def analyze_processor_trends(data_cache, processor_name=None, metric='bytesWritten', hours=24):
    """
    Shows trends for a specific processor or all processors over time.
    
    Args:
        data_cache: Dictionary of loaded data
        processor_name: Specific processor name (None for all)
        metric: Metric to analyze (bytesWritten, bytesRead, activeThreadCount, etc.)
        hours: Number of hours to analyze
    """
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    proc_keys = [k for k in data_cache.keys() if 'processor' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if not proc_keys:
        print("\nNo processor data loaded.\n")
        return
    
    console = Console()
    all_proc_df = pd.concat([data_cache[key] for key in proc_keys], ignore_index=True)
    
    # Convert timestamp and filter by time window
    all_proc_df['collection_timestamp'] = pd.to_datetime(all_proc_df['collection_timestamp'], errors='coerce')
    all_proc_df.dropna(subset=['collection_timestamp'], inplace=True)
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    df = all_proc_df[all_proc_df['collection_timestamp'] >= cutoff_time]
    
    if df.empty:
        console.print(f"\n[yellow]No data found in the last {hours} hours.[/yellow]\n")
        return
    
    # Filter by processor name if specified
    if processor_name:
        df = df[df['name'] == processor_name]
        if df.empty:
            console.print(f"\n[yellow]No data found for processor '{processor_name}'.[/yellow]\n")
            return
    
    # Convert metric to numeric
    metric_key = f'nifi_amount_{metric}' if not metric.startswith('nifi_') else metric
    df[metric_key] = pd.to_numeric(df.get(metric_key, 0), errors='coerce')
    
    # Group by time and processor
    df_sorted = df.sort_values('collection_timestamp')
    
    if processor_name:
        # Single processor trend
        console.print(f"\n[bold cyan]📈 Trend Analysis: {processor_name} ({metric})[/bold cyan]\n")
        
        # Calculate statistics
        stats = {
            "Mean": df[metric_key].mean(),
            "Min": df[metric_key].min(),
            "Max": df[metric_key].max(),
            "Std Dev": df[metric_key].std(),
            "Trend": "📈 Increasing" if df[metric_key].iloc[-1] > df[metric_key].iloc[0] else "📉 Decreasing"
        }
        
        table = Table(title="Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        for key, value in stats.items():
            if key == "Trend":
                table.add_row(key, value)
            else:
                table.add_row(key, f"{value:.2f}")
        
        console.print(table)
        
        # Show recent values
        recent = df_sorted.tail(10)[['collection_timestamp', 'name', metric_key]]
        console.print("\n[bold]Recent Values:[/bold]")
        for _, row in recent.iterrows():
            timestamp = row['collection_timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            console.print(f"  {timestamp}: {row[metric_key]:.2f}")
    
    else:
        # Multiple processors - show comparison
        console.print(f"\n[bold cyan]📊 Processor Comparison ({metric})[/bold cyan]\n")
        
        # Get latest value for each processor
        latest_values = df_sorted.groupby('name').tail(1)
        top_processors = latest_values.nlargest(15, metric_key)
        
        table = Table(title=f"Top 15 Processors by {metric}")
        table.add_column("Processor", style="magenta")
        table.add_column("Latest Value", style="green", justify="right")
        table.add_column("Mean", style="cyan", justify="right")
        table.add_column("Max", style="red", justify="right")
        
        for _, row in top_processors.iterrows():
            proc_data = df[df['name'] == row['name']]
            table.add_row(
                row['name'],
                f"{row[metric_key]:.2f}",
                f"{proc_data[metric_key].mean():.2f}",
                f"{proc_data[metric_key].max():.2f}"
            )
        
        console.print(table)
    
    console.print()


def compare_time_periods(data_cache, metric_type='nifi_processor', period1_hours_ago=24, period2_hours_ago=48):
    """
    Compares two time periods to identify changes in behavior.
    
    Args:
        data_cache: Dictionary of loaded data
        metric_type: Type of metric to compare
        period1_hours_ago: Hours ago for period 1 (more recent)
        period2_hours_ago: Hours ago for period 2 (baseline)
    """
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    metric_keys = [k for k in data_cache.keys() if metric_type in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if not metric_keys:
        print(f"\nNo {metric_type} data loaded.\n")
        return
    
    console = Console()
    all_df = pd.concat([data_cache[key] for key in metric_keys], ignore_index=True)
    
    # Convert timestamp
    all_df['collection_timestamp'] = pd.to_datetime(all_df['collection_timestamp'], errors='coerce')
    all_df.dropna(subset=['collection_timestamp'], inplace=True)
    
    now = datetime.utcnow()
    
    # Define time periods
    period1_start = now - timedelta(hours=period1_hours_ago)
    period2_start = now - timedelta(hours=period2_hours_ago)
    period2_end = now - timedelta(hours=period1_hours_ago)
    
    period1_data = all_df[all_df['collection_timestamp'] >= period1_start]
    period2_data = all_df[(all_df['collection_timestamp'] >= period2_start) & 
                          (all_df['collection_timestamp'] < period2_end)]
    
    if period1_data.empty or period2_data.empty:
        console.print("\n[yellow]Insufficient data for comparison.[/yellow]\n")
        return
    
    console.print(f"\n[bold cyan]📊 Time Period Comparison[/bold cyan]")
    console.print(f"Period 1 (Recent): Last {period1_hours_ago} hours ({len(period1_data)} records)")
    console.print(f"Period 2 (Baseline): {period2_hours_ago}-{period1_hours_ago} hours ago ({len(period2_data)} records)\n")
    
    # Count comparison
    if metric_type == 'nifi_processor':
        # Compare processor counts by status
        period1_status = period1_data.groupby('runStatus').size()
        period2_status = period2_data.groupby('runStatus').size()
        
        table = Table(title="Processor Status Comparison")
        table.add_column("Status", style="cyan")
        table.add_column("Period 1", style="green", justify="right")
        table.add_column("Period 2", style="yellow", justify="right")
        table.add_column("Change", style="magenta", justify="right")
        
        all_statuses = set(period1_status.index) | set(period2_status.index)
        for status in all_statuses:
            p1 = period1_status.get(status, 0)
            p2 = period2_status.get(status, 0)
            change = p1 - p2
            change_str = f"+{change}" if change > 0 else str(change)
            table.add_row(status, str(p1), str(p2), change_str)
        
        console.print(table)
    
    console.print()


def find_correlations(data_cache, min_correlation=0.7):
    """
    Finds correlations between different metrics.
    
    Args:
        data_cache: Dictionary of loaded data
        min_correlation: Minimum correlation coefficient to report
    """
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    console = Console()
    
    # Try to find processor and connection data
    proc_keys = [k for k in data_cache.keys() if 'processor' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    conn_keys = [k for k in data_cache.keys() if 'connection' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    
    if not proc_keys or not conn_keys:
        console.print("\n[yellow]Need both processor and connection data for correlation analysis.[/yellow]\n")
        return
    
    proc_df = pd.concat([data_cache[key] for key in proc_keys], ignore_index=True)
    conn_df = pd.concat([data_cache[key] for key in conn_keys], ignore_index=True)
    
    # Convert timestamps
    proc_df['collection_timestamp'] = pd.to_datetime(proc_df['collection_timestamp'], errors='coerce')
    conn_df['collection_timestamp'] = pd.to_datetime(conn_df['collection_timestamp'], errors='coerce')
    
    # Get numeric columns
    proc_numeric = proc_df.select_dtypes(include=[np.number])
    conn_numeric = conn_df.select_dtypes(include=[np.number])
    
    if proc_numeric.empty or conn_numeric.empty:
        console.print("\n[yellow]Insufficient numeric data for correlation analysis.[/yellow]\n")
        return
    
    # Calculate correlations within processor metrics
    proc_corr = proc_numeric.corr()
    
    # Find strong correlations
    strong_corr = []
    for i in range(len(proc_corr.columns)):
        for j in range(i+1, len(proc_corr.columns)):
            corr_value = proc_corr.iloc[i, j]
            if abs(corr_value) >= min_correlation:
                strong_corr.append({
                    'metric1': proc_corr.columns[i],
                    'metric2': proc_corr.columns[j],
                    'correlation': corr_value
                })
    
    if not strong_corr:
        console.print(f"\n[yellow]No correlations found above {min_correlation} threshold.[/yellow]\n")
        return
    
    console.print(f"\n[bold cyan]🔗 Strong Correlations (>= {min_correlation})[/bold cyan]\n")
    
    table = Table(title="Correlated Metrics")
    table.add_column("Metric 1", style="cyan")
    table.add_column("Metric 2", style="magenta")
    table.add_column("Correlation", style="green", justify="right")
    table.add_column("Type", style="yellow")
    
    for corr in sorted(strong_corr, key=lambda x: abs(x['correlation']), reverse=True)[:15]:
        corr_type = "Positive" if corr['correlation'] > 0 else "Negative"
        table.add_row(
            corr['metric1'],
            corr['metric2'],
            f"{corr['correlation']:.3f}",
            corr_type
        )
    
    console.print(table)
    console.print("\n[yellow]💡 Tip: Strong correlations can help identify related performance issues[/yellow]\n")


def analyze_queue_buildup(data_cache, threshold_rate=0.1):
    """
    Analyzes queue buildup rates to identify growing queues.
    
    Args:
        data_cache: Dictionary of loaded data
        threshold_rate: Minimum growth rate per hour to report
    """
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    conn_keys = [k for k in data_cache.keys() if 'connection' in k and isinstance(data_cache.get(k), pd.DataFrame)]
    if not conn_keys:
        print("\nNo connection data loaded.\n")
        return
    
    console = Console()
    all_conn_df = pd.concat([data_cache[key] for key in conn_keys], ignore_index=True)
    
    # Convert timestamp and sort
    all_conn_df['collection_timestamp'] = pd.to_datetime(all_conn_df['collection_timestamp'], errors='coerce')
    all_conn_df.dropna(subset=['collection_timestamp'], inplace=True)
    all_conn_df = all_conn_df.sort_values('collection_timestamp')
    
    # Convert queue count to numeric
    all_conn_df['queuedCount_int'] = pd.to_numeric(
        all_conn_df['queuedCount'].str.replace(',', ''), 
        errors='coerce'
    ).fillna(0).astype(int)
    
    # Calculate growth rate for each connection
    growing_queues = []
    
    for conn_id in all_conn_df['id'].unique():
        conn_data = all_conn_df[all_conn_df['id'] == conn_id].copy()
        
        if len(conn_data) < 2:
            continue
        
        # Calculate rate of change
        first_time = conn_data.iloc[0]['collection_timestamp']
        last_time = conn_data.iloc[-1]['collection_timestamp']
        first_count = conn_data.iloc[0]['queuedCount_int']
        last_count = conn_data.iloc[-1]['queuedCount_int']
        
        time_diff_hours = (last_time - first_time).total_seconds() / 3600
        
        if time_diff_hours > 0:
            growth_rate = (last_count - first_count) / time_diff_hours
            
            if growth_rate >= threshold_rate:
                growing_queues.append({
                    'name': conn_data.iloc[0]['name'],
                    'flow_name': conn_data.iloc[0].get('flow_name', 'root'),
                    'first_count': first_count,
                    'last_count': last_count,
                    'growth_rate': growth_rate,
                    'time_hours': time_diff_hours
                })
    
    if not growing_queues:
        console.print(f"\n[bold green]✓ No queues with growth rate >= {threshold_rate}/hour found.[/bold green]\n")
        return
    
    console.print(f"\n[bold red]⚠️  Growing Queues (>= {threshold_rate}/hour)[/bold red]\n")
    
    table = Table(title="Queue Buildup Analysis")
    table.add_column("Connection", style="magenta")
    table.add_column("Flow", style="blue")
    table.add_column("Initial", style="green", justify="right")
    table.add_column("Current", style="yellow", justify="right")
    table.add_column("Growth Rate/hr", style="red", justify="right")
    table.add_column("Period (hrs)", style="cyan", justify="right")
    
    for queue in sorted(growing_queues, key=lambda x: x['growth_rate'], reverse=True):
        table.add_row(
            queue['name'],
            queue['flow_name'],
            str(queue['first_count']),
            str(queue['last_count']),
            f"{queue['growth_rate']:.1f}",
            f"{queue['time_hours']:.1f}"
        )
    
    console.print(table)
    console.print("\n[yellow]💡 Tip: Growing queues may indicate downstream bottlenecks[/yellow]\n")


def show_system_resource_summary(data_cache):
    """
    Shows system resource utilization summary across all nodes.
    """
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    if 'system' not in data_cache or not isinstance(data_cache['system'], pd.DataFrame):
        print("\nNo system metrics loaded. Ensure 'System' is in 'components_to_monitor'.\n")
        return
    
    console = Console()
    df = data_cache['system']
    
    # Get latest record for each hostname
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df_latest = df.sort_values('timestamp').drop_duplicates(subset=['hostname'], keep='last')
    
    if df_latest.empty:
        console.print("\n[yellow]No system metrics available.[/yellow]\n")
        return
    
    console.print("\n[bold cyan]💻 System Resource Summary[/bold cyan]\n")
    
    # CPU Summary
    cpu_table = Table(title="CPU Utilization")
    cpu_table.add_column("Hostname", style="yellow")
    cpu_table.add_column("CPU %", style="red", justify="right")
    cpu_table.add_column("Cores (Logical)", style="cyan", justify="right")
    cpu_table.add_column("Cores (Physical)", style="cyan", justify="right")
    
    for _, row in df_latest.iterrows():
        cpu_pct = row.get('cpu_percent', 0)
        cpu_style = "red" if cpu_pct > 80 else "yellow" if cpu_pct > 60 else "green"
        cpu_table.add_row(
            row['hostname'],
            f"[{cpu_style}]{cpu_pct:.1f}%[/{cpu_style}]",
            str(row.get('cpu_cores_logical', 'N/A')),
            str(row.get('cpu_cores_physical', 'N/A'))
        )
    
    console.print(cpu_table)
    
    # Memory Summary
    mem_table = Table(title="Memory Utilization")
    mem_table.add_column("Hostname", style="yellow")
    mem_table.add_column("Memory %", style="red", justify="right")
    mem_table.add_column("Used (MB)", style="cyan", justify="right")
    mem_table.add_column("Total (MB)", style="cyan", justify="right")
    
    for _, row in df_latest.iterrows():
        mem_pct = row.get('memory_percent', 0)
        mem_style = "red" if mem_pct > 80 else "yellow" if mem_pct > 60 else "green"
        mem_table.add_row(
            row['hostname'],
            f"[{mem_style}]{mem_pct:.1f}%[/{mem_style}]",
            f"{row.get('memory_used_mb', 0):.0f}",
            f"{row.get('memory_total_mb', 0):.0f}"
        )
    
    console.print(mem_table)
    
    # Disk Summary
    disk_table = Table(title="Disk Utilization")
    disk_table.add_column("Hostname", style="yellow")
    disk_table.add_column("Disk %", style="red", justify="right")
    disk_table.add_column("Used (GB)", style="cyan", justify="right")
    disk_table.add_column("Total (GB)", style="cyan", justify="right")
    
    for _, row in df_latest.iterrows():
        disk_pct = row.get('disk_percent', 0)
        disk_style = "red" if disk_pct > 80 else "yellow" if disk_pct > 60 else "green"
        disk_table.add_row(
            row['hostname'],
            f"[{disk_style}]{disk_pct:.1f}%[/{disk_style}]",
            f"{row.get('disk_used_gb', 0):.1f}",
            f"{row.get('disk_total_gb', 0):.1f}"
        )
    
    console.print(disk_table)
    console.print()


def export_summary_report(data_cache, output_file='nifi_summary_report.txt'):
    """
    Exports a text summary report of all key findings.
    
    Args:
        data_cache: Dictionary of loaded data
        output_file: Output filename
    """
    if not isinstance(data_cache, dict) or not data_cache:
        print("\nNo data loaded.\n")
        return
    
    from io import StringIO
    import sys
    
    # Capture output
    old_stdout = sys.stdout
    sys.stdout = report = StringIO()
    
    print("=" * 80)
    print("NiFi Health Summary Report")
    print(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 80)
    print()
    
    # Include key sections
    print("PROCESSOR STATUS")
    print("-" * 80)
    show_health_summary(data_cache)
    print()
    
    print("STOPPED PROCESSORS")
    print("-" * 80)
    list_stopped_processors(data_cache)
    print()
    
    print("BACK PRESSURE")
    print("-" * 80)
    find_back_pressure(data_cache, 70.0)
    print()
    
    print("SLOW PROCESSORS")
    print("-" * 80)
    find_slow_processors(data_cache, 90.0)
    print()
    
    # Restore stdout
    sys.stdout = old_stdout
    
    # Write to file
    try:
        with open(output_file, 'w') as f:
            f.write(report.getvalue())
        print(f"\n✓ Report exported to: {output_file}\n")
    except Exception as e:
        print(f"\n❌ Failed to export report: {e}\n")
