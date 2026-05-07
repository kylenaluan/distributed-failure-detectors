import argparse
import time
import yaml
from pathlib import Path

from experiments.scenarios import (
    stable_baseline,
    single_node_crash,
    rolling_crash,
    moderate_congestion,
    moderate_congestion_with_crash,
    high_congestion,
    high_congestion_with_crash,
    heavy_congestion,
    heavy_congestion_with_crash,
    spike_and_recovery,
    spike_and_recovery_with_crash
)
from experiments.runner import ExperimentRunner
from analysis.analyze import Analyzer


def load_config(config_path):
    # parse config.yaml into a dict using PyYAML
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def build_node_map(config):
    # build node_id -> (host, port) mapping for Analyzer
    return {
        node['node_id']: (node['host'], node['port'])
        for node in config['nodes']
    }


def wait_for_start(start_time):
    # sleep until the synchronized start time so all nodes begin together
    now = time.time()
    if start_time > now:
        wait = start_time - now
        print(f'Waiting {wait:.1f}s for synchronized start...')
        time.sleep(wait)


def main():
    parser = argparse.ArgumentParser(description='Failure Detector Comparison System')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    parser.add_argument('--output', default='results/results.csv', help='Path for CSV output')
    # node_id identifies which physical node this process is running on
    parser.add_argument('--node', required=True, help='Node ID for this machine (e.g. node-1)')
    # start_time is a Unix timestamp so all nodes begin experiments simultaneously
    parser.add_argument('--start-time', type=float, default=None, help='Unix timestamp for synchronized start')
    args = parser.parse_args()

    config = load_config(args.config)

    # run all scenarios in sequence
    scenarios = [
        stable_baseline,
        single_node_crash,
        rolling_crash,
        moderate_congestion,
        moderate_congestion_with_crash,
        high_congestion,
        high_congestion_with_crash,
        heavy_congestion,
        heavy_congestion_with_crash,
        spike_and_recovery,
        spike_and_recovery_with_crash
    ]

    # wait for synchronized start if a start time was provided
    if args.start_time is not None:
        wait_for_start(args.start_time)

    for scenario in scenarios:
        print(f'Running scenario: {scenario.name}')
        # pass node_id so runner only instantiates this node
        runner = ExperimentRunner(scenario, config, args.node)
        runner.run()
        print(f'Finished scenario: {scenario.name}')
        time.sleep(5)  # brief pause between scenarios to allow clean shutdown

if __name__ == '__main__':
    main()