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
        show_jvm_heap_metrics # Added
    )
except ImportError as e:
    print(f"Error: Failed to import necessary modules: {e}")
    print("Please ensure you have installed the project in editable mode with 'pip install -e .'")
    sys.exit(1)


def main():
    """Main function to run the interactive troubleshooting REPL."""
    print("--- NiFi Troubleshooting Tool ---")
    print("Type 'help' for a list of commands, 'exit' to quit.")

    data_cache = {}
    
    command_completer = WordCompleter([
        'load', 'health-summary', 'list-stopped', 
        'back-pressure', 'slow-processors',
        'view-bulletins', 'list-invalid-services', 'check-reporting-tasks',
        'cluster-health',
        'jvm-heap', # Added
        'help', 'exit', 'quit'
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

            if command in ['exit', 'quit']:
                print("Exiting.")
                break
            elif command == 'help':
                print("\nAvailable commands:")
                print("  load [start] [end]      - Loads metric data for a date or range (YYYY-MM-DD).")
                print("  health-summary          - Shows a high-level summary of the loaded data.")
                print("  list-stopped            - Lists all processors that are not in a RUNNING state.")
                print("  back-pressure [thresh]  - Finds queues nearing back pressure (default: 80%).")
                print("  slow-processors [perc]  - Finds processors with high lineage duration (default: 90th percentile).")
                print("  view-bulletins [lvl]    - Shows recent bulletins. Optional level: ERROR, WARN.")
                print("  list-invalid-services   - Lists controller services that are not VALID.")
                print("  check-reporting-tasks   - Shows the status of all reporting tasks.")
                print("  cluster-health          - Displays detailed NiFi cluster health and node status.")
                print("  jvm-heap                - Displays detailed JVM heap and garbage collection metrics.") # Added
                print("  exit / quit             - Exits the application.\n")
            
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
            
            elif command == 'jvm-heap': # Added
                show_jvm_heap_metrics(data_cache)

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


if __name__ == "__main__":
    main()

