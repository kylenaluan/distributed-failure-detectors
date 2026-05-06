import json
import argparse
from pathlib import Path
from collections import defaultdict


def load_collection_config(config_path):
    # parse the collection config to get the list of node IDs
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_scenario_name(filename):
    # derive scenario name from filename by stripping node_id and _events suffix
    # e.g. Single_Node_Crash_node-1_events.json -> Single_Node_Crash
    parts = filename.stem.split('_')

    # node id is always the last two parts before _events (e.g. node-1)
    # strip trailing _events, then strip trailing node-X
    name = filename.stem
    name = name.replace('_events', '')

    # remove the node id suffix (node-1 through node-5)
    for i in range(1, 6):
        name = name.replace(f'_node-{i}', '')

    return name


def collect_log_files(local_log_dir, node_ids):
    # group all log files by scenario name across all node directories
    scenario_files = defaultdict(list)

    for node_id in node_ids:
        node_dir = Path(local_log_dir) / node_id
        if not node_dir.exists():
            print(f'Warning: log directory not found for {node_id}, skipping')
            continue

        for filepath in node_dir.glob('*.json'):
            scenario_name = get_scenario_name(filepath)
            scenario_files[scenario_name].append(filepath)

    return scenario_files


def merge_scenario_logs(filepaths):
    # load and merge all events from all nodes for one scenario
    all_events = []

    for filepath in filepaths:
        with open(filepath, 'r') as f:
            events = json.load(f)
        all_events.extend(events)

    # sort merged events by timestamp so MetricsComputer sees them in order
    all_events.sort(key=lambda e: e['timestamp'])

    return all_events


def main():
    parser = argparse.ArgumentParser(description='Merge log files from all nodes by scenario')
    parser.add_argument('--collection-config', default='collection_config.yaml', help='Path to collection config file')
    # local log dir should match the --local-log-dir used in collect_logs.py
    parser.add_argument('--local-log-dir', default='logs', help='Local directory containing collected node logs')
    # merged log dir is where Analyzer will read from
    parser.add_argument('--merged-log-dir', default='logs/merged', help='Directory to write merged log files into')
    args = parser.parse_args()

    collection_config = load_collection_config(args.collection_config)
    # extract just the node IDs from the collection config
    node_ids = [node['node_id'] for node in collection_config['nodes']]

    # group log files by scenario across all node directories
    scenario_files = collect_log_files(args.local_log_dir, node_ids)

    if not scenario_files:
        print('No log files found. Did you run collect_logs.py first?')
        return

    # write one merged file per scenario
    merged_dir = Path(args.merged_log_dir)
    merged_dir.mkdir(parents=True, exist_ok=True)

    for scenario_name, filepaths in scenario_files.items():
        print(f'Merging {len(filepaths)} log files for scenario: {scenario_name}')
        merged_events = merge_scenario_logs(filepaths)

        # write merged file using the same naming convention Analyzer expects
        output_path = merged_dir / f'{scenario_name}_events.json'
        with open(output_path, 'w') as f:
            json.dump(merged_events, f)

        print(f'Written: {output_path} ({len(merged_events)} events)')

    print(f'All scenarios merged. Run analysis pointing at {args.merged_log_dir}/')


if __name__ == '__main__':
    main()
