import argparse
import yaml
from pathlib import Path

from analysis.analyze import Analyzer


def load_config(config_path):
    # parse config.yaml to get node definitions for building node_map
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def build_node_map(config):
    # build node_id -> (host, port) mapping for MetricsComputer
    return {
        node['node_id']: (node['host'], node['port'])
        for node in config['nodes']
    }


def main():
    parser = argparse.ArgumentParser(description='Analyze merged log files and produce results CSV')
    parser.add_argument('--config', default='config_ci_10.yaml', help='Path to config file')
    # log dir should point at the merged logs produced by merge_logs.py
    parser.add_argument('--log-dir', default='logs/merged', help='Directory containing merged log files')
    parser.add_argument('--output', default='results/results.csv', help='Path for CSV output')
    args = parser.parse_args()

    config = load_config(args.config)
    node_map = build_node_map(config)

    # create results directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f'Reading logs from {args.log_dir}/')
    analyzer = Analyzer(args.log_dir, node_map)
    analyzer.run(output_path)
    print(f'Results written to {args.output}')


if __name__ == '__main__':
    main()
