import os
import sys
from datetime import datetime
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter

# Add parent directory to path to find the 'lib' module for config loading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from lib.config_loader import load_config, load_secrets
    from analysis.lib.data_loader import load_all_data
    from analysis.lib.analysis_functions import (
        show_health_summary, 
        list_stopped_processors,
        find_back_pressure,
        find_slow_processors,
        view_bulletins,
        list_invalid_services,
        check_reporting_tasks,
        show_cluster_health,
        show_jvm_heap_metrics
    )
    from analysis.lib.provenance_analysis import (
        analyze_dropped_flowfiles,
        analyze_data_flow_paths,
        analyze_processing_bottlenecks,
        analyze_external_transfers,
        trace_flowfile_lineage,
        analyze_fork_join_patterns,
        analyze_content_modifications
    )
    from analysis.lib.advanced_analysis import (
        analyze_processor_trends,
        compare_time_periods,
        find_correlations,
        analyze_queue_buildup,
        show_system_resource_summary,
        export_summary_report
    )
except ImportError as e:
    print(f"Error: Failed to import necessary modules: {e}")
    print("Please ensure you have installed the project in editable mode with 'pip install -e .'")
    sys.exit(1)


def main():
    """Main function to run the interactive troubleshooting REPL."""
    print("=" * 70)
    print("  NiFi Troubleshooting Tool - Enhanced Edition")
    print("=" * 70)
    print("Type 'help' for a list of commands, 'exit' to quit.")
    print()

    data_cache = {}
    
    # Enhanced command list with all features
    command_completer = WordCompleter([
        # Data Loading
        'load', 'load-collection',
        
        # Health & Status
        'health-summary', 'list-stopped', 'back-pressure', 'slow-processors',
        'view-bulletins', 'list-invalid-services', 'check-reporting-tasks',
        'cluster-health', 'jvm-heap', 'system-resources',
        
        # Provenance Analysis
        'dropped-flowfiles', 'flow-paths', 'bottlenecks', 'external-transfers',
        'trace-flowfile', 'fork-join-analysis', 'content-modifications',
        
        # Advanced Analysis (NEW)
        'processor-trends', 'compare-periods', 'find-correlations',
        'queue-buildup', 'export-report',
        
        # Version Management
        'version-info', 'data-versions', 'validate-versions',
        
        # Utility
        'help', 'exit', 'quit', 'clear'
    ], ignore_case=True)

    session = PromptSession(
        history=FileHistory('.troubleshoot_history'),
        auto_suggest=AutoSuggestFromHistory(),
        completer=command_completer
    )
    
    try:
        secrets = load_secrets()
        config = load_config()
    except FileNotFoundError as e:
        print(f"\nERROR: Configuration file not found. {e}")
        print("Please ensure config/secrets.json and config/nifi-config.json exist.")
        return

    while True:
        try:
            command_line = session.prompt('(nifi-troubleshoot)> ')
            parts = command_line.strip().split()
            if not parts:
                continue

            command = parts[0].lower()
            args = parts[1:]

            # ============================================================
            # SYSTEM COMMANDS
            # ============================================================
            
            if command in ['exit', 'quit']:
                print("Exiting.")
                break
                
            elif command == 'clear':
                os.system('clear' if os.name != 'nt' else 'cls')
                continue
                
            elif command == 'help':
                print("\n" + "=" * 70)
                print("  AVAILABLE COMMANDS")
                print("=" * 70)
                
                print("\n📊 DATA LOADING")
                print("  load [start] [end]          Load metrics by date (YYYY-MM-DD)")
                print("  load-collection <id>        Load specific collection by ID")
                
                print("\n💚 HEALTH & STATUS")
                print("  health-summary              High-level system overview")
                print("  list-stopped                Processors not in RUNNING state")
                print("  back-pressure [thresh]      Queues nearing back pressure (default: 80%)")
                print("  slow-processors [perc]      High lineage duration (default: 90th percentile)")
                print("  view-bulletins [level]      Recent bulletins (ERROR, WARN)")
                print("  list-invalid-services       Controller services not VALID")
                print("  check-reporting-tasks       Status of reporting tasks")
                print("  cluster-health              Detailed cluster and node status")
                print("  jvm-heap                    JVM heap and memory metrics")
                print("  system-resources            System resource utilization summary")
                
                print("\n🔍 PROVENANCE ANALYSIS")
                print("  dropped-flowfiles [min] [n] FlowFiles being dropped (time window, min drops)")
                print("  flow-paths [top_n]          Most common data flow paths")
                print("  bottlenecks [percentile]    Processing bottlenecks by duration")
                print("  external-transfers          SEND/RECEIVE to external systems")
                print("  trace-flowfile <uuid>       Complete lineage of specific FlowFile")
                print("  fork-join-analysis          Data splitting and merging patterns")
                print("  content-modifications [n]   Processors modifying content/attributes")
                
                print("\n📈 ADVANCED ANALYSIS")
                print("  processor-trends [name] [metric] [hrs]")
                print("                              Analyze trends for processor metrics")
                print("                              Examples:")
                print("                                processor-trends")
                print("                                processor-trends ConvertRecord")
                print("                                processor-trends ExecuteSQL bytesRead 48")
                print("  compare-periods [type] [p1] [p2]")
                print("                              Compare two time periods")
                print("                              Example: compare-periods nifi_processor 24 48")
                print("  find-correlations [min]     Find metric correlations (min correlation)")
                print("                              Example: find-correlations 0.7")
                print("  queue-buildup [rate]        Analyze growing queues (min growth rate/hour)")
                print("                              Example: queue-buildup 0.1")
                print("  export-report [file]        Export summary report to file")
                print("                              Example: export-report weekly_report.txt")
                
                print("\n🔖 VERSION MANAGEMENT")
                print("  version-info                Current tool version and features")
                print("  data-versions               Versions of loaded data")
                print("  validate-versions           Re-validate loaded data")
                
                print("\n🛠️  UTILITY")
                print("  help                        Show this help message")
                print("  clear                       Clear the screen")
                print("  exit / quit                 Exit the application")
                print("\n" + "=" * 70 + "\n")
            
            # ============================================================
            # DATA LOADING
            # ============================================================
            
            elif command == 'load':
                start_date_str = None
                end_date_str = None
                if len(args) == 0:
                    start_date_str = datetime.utcnow().strftime("%Y-%m-%d")
                elif len(args) == 1:
                    start_date_str = args[0]
                elif len(args) == 2:
                    start_date_str = args[0]
                    end_date_str = args[1]
                else:
                    print("Usage: load [start_date] [end_date]")
                    continue
                
                print(f"Loading data from {start_date_str}{' to ' + end_date_str if end_date_str else ''}...")
                data_cache = load_all_data(config, secrets, start_date_str, end_date_str)
                if data_cache:
                    print("Data loaded successfully.")
                else:
                    print("Failed to load data or no data found for the specified date range.")
            
            elif command == 'load-collection':
                if len(args) != 1:
                    print("Usage: load-collection <collection_id>")
                    continue
                collection_id = args[0]
                print(f"Loading collection {collection_id}...")
                # This would need to be implemented in data_loader.py
                print("Note: load-collection feature needs to be implemented in data_loader.py")
            
            # ============================================================
            # HEALTH & STATUS
            # ============================================================
            
            elif command == 'health-summary':
                show_health_summary(data_cache)
            
            elif command == 'list-stopped':
                list_stopped_processors(data_cache)

            elif command == 'back-pressure':
                threshold = float(args[0]) if args else 80.0
                find_back_pressure(data_cache, threshold)

            elif command == 'slow-processors':
                percentile = float(args[0]) if args else 90.0
                find_slow_processors(data_cache, percentile)
            
            elif command == 'view-bulletins':
                level = args[0] if args else None
                view_bulletins(data_cache, level)

            elif command == 'list-invalid-services':
                list_invalid_services(data_cache)

            elif command == 'check-reporting-tasks':
                check_reporting_tasks(data_cache)
            
            elif command == 'cluster-health':
                show_cluster_health(data_cache)
            
            elif command == 'jvm-heap':
                show_jvm_heap_metrics(data_cache)
            
            elif command == 'system-resources':
                show_system_resource_summary(data_cache)
            
            # ============================================================
            # PROVENANCE ANALYSIS
            # ============================================================
            
            elif command == 'dropped-flowfiles':
                time_window = int(args[0]) if len(args) >= 1 else 60
                min_drops = int(args[1]) if len(args) >= 2 else 5
                analyze_dropped_flowfiles(data_cache, time_window, min_drops)
            
            elif command == 'flow-paths':
                top_n = int(args[0]) if args else 10
                analyze_data_flow_paths(data_cache, top_n)
            
            elif command == 'bottlenecks':
                percentile = int(args[0]) if args else 90
                analyze_processing_bottlenecks(data_cache, percentile)
            
            elif command == 'external-transfers':
                analyze_external_transfers(data_cache)
            
            elif command == 'trace-flowfile':
                if not args:
                    print("Usage: trace-flowfile <flowfile_uuid>")
                    continue
                flowfile_uuid = args[0]
                trace_flowfile_lineage(data_cache, flowfile_uuid)
            
            elif command == 'fork-join-analysis':
                analyze_fork_join_patterns(data_cache)
            
            elif command == 'content-modifications':
                top_n = int(args[0]) if args else 15
                analyze_content_modifications(data_cache, top_n)
            
            # ============================================================
            # ADVANCED ANALYSIS (NEW)
            # ============================================================
            
            elif command == 'processor-trends':
                processor_name = args[0] if len(args) >= 1 else None
                metric = args[1] if len(args) >= 2 else 'bytesWritten'
                hours = int(args[2]) if len(args) >= 3 else 24
                
                print(f"\nAnalyzing trends for {'all processors' if not processor_name else processor_name}...")
                print(f"Metric: {metric}, Time window: {hours} hours\n")
                
                analyze_processor_trends(data_cache, processor_name, metric, hours)
            
            elif command == 'compare-periods':
                metric_type = args[0] if len(args) >= 1 else 'nifi_processor'
                period1 = int(args[1]) if len(args) >= 2 else 24
                period2 = int(args[2]) if len(args) >= 3 else 48
                
                print(f"\nComparing time periods for {metric_type}...")
                print(f"Period 1: Last {period1} hours")
                print(f"Period 2: {period2}-{period1} hours ago\n")
                
                compare_time_periods(data_cache, metric_type, period1, period2)
            
            elif command == 'find-correlations':
                min_correlation = float(args[0]) if args else 0.7
                
                print(f"\nFinding correlations (minimum: {min_correlation})...\n")
                find_correlations(data_cache, min_correlation)
            
            elif command == 'queue-buildup':
                threshold_rate = float(args[0]) if args else 0.1
                
                print(f"\nAnalyzing queue buildup (minimum rate: {threshold_rate}/hour)...\n")
                analyze_queue_buildup(data_cache, threshold_rate)
            
            elif command == 'export-report':
                output_file = args[0] if args else 'nifi_summary_report.txt'
                
                print(f"\nExporting summary report to {output_file}...\n")
                export_summary_report(data_cache, output_file)
            
            # ============================================================
            # VERSION MANAGEMENT
            # ============================================================
            
            elif command == 'version-info':
                from lib.version import get_schema_version, get_version_info
                
                version = get_schema_version()
                info = get_version_info()
                
                print("\n" + "=" * 70)
                print("  NiFi Troubleshooting Tool Version Info")
                print("=" * 70)
                print(f"\nCurrent Schema Version: {version}")
                print(f"Release Date: {info['date']}")
                print("\nChanges in this version:")
                for change in info['changes']:
                    print(f"  • {change}")
                print("\nSupported Metric Types:")
                for metric_type in info['metric_types']:
                    print(f"  • {metric_type}")
                print("\n" + "=" * 70 + "\n")
            
            elif command == 'data-versions':
                if not data_cache:
                    print("\nNo data loaded. Use 'load' command first.\n")
                    continue
                
                print("\n" + "=" * 70)
                print("  Data Version Summary")
                print("=" * 70)
                
                from lib.version import get_schema_version
                current_version = get_schema_version()
                print(f"\nCurrent Tool Version: {current_version}\n")
                
                print("Versions by Metric Type:")
                has_version_info = False
                for key, df in data_cache.items():
                    if hasattr(df, 'columns') and 'schema_version' in df.columns:
                        versions = df['schema_version'].unique()
                        print(f"  {key}: {', '.join(str(v) for v in versions)}")
                        has_version_info = True
                
                if not has_version_info:
                    print("  No version information found in loaded data (legacy format)")
                
                print("\n" + "=" * 70 + "\n")
            
            elif command == 'validate-versions':
                if not data_cache:
                    print("\nNo data loaded. Use 'load' command first.\n")
                    continue
                
                print("\n" + "=" * 70)
                print("  Validating Data Versions")
                print("=" * 70 + "\n")
                
                from lib.version import is_version_compatible, get_schema_version
                current_version = get_schema_version()
                
                all_compatible = True
                for key, df in data_cache.items():
                    if hasattr(df, 'columns') and 'schema_version' in df.columns:
                        versions = df['schema_version'].unique()
                        for version in versions:
                            compatible = is_version_compatible(str(version))
                            status = "✓" if compatible else "✗"
                            color = "green" if compatible else "red"
                            print(f"{status} {key}: version {version} - {'COMPATIBLE' if compatible else 'INCOMPATIBLE'}")
                            if not compatible:
                                all_compatible = False
                
                if all_compatible:
                    print("\n✓ All data versions are compatible with this tool.")
                else:
                    print("\n⚠ Some data has incompatible versions. Consider updating the tool.")
                
                print("\n" + "=" * 70 + "\n")
            
            else:
                print(f"Unknown command: '{command}'. Type 'help' for options.")

        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            print("\nExiting.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
