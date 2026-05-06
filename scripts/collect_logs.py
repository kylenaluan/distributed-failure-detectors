import argparse
import subprocess
import yaml
from pathlib import Path


def load_collection_config(config_path):
    # parse the collection config containing node IPs and SSH key path
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def collect_from_node(node_id, floating_ip, ssh_key, remote_log_dir, local_log_dir):
    # create local directory for this node's logs
    node_log_dir = Path(local_log_dir) / node_id
    node_log_dir.mkdir(parents=True, exist_ok=True)

    # build scp command to pull all log files from this node
    remote_path = f'cc@{floating_ip}:{remote_log_dir}/*_{node_id}_events.json'
    local_path = str(node_log_dir)

    print(f'Collecting logs from {node_id} ({floating_ip})...')
    result = subprocess.run(
        ['scp', '-i', ssh_key, '-o', 'StrictHostKeyChecking=no', remote_path, local_path],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f'Successfully collected logs from {node_id}')
    else:
        # print stderr to help diagnose connection or path issues
        print(f'Warning: failed to collect logs from {node_id}: {result.stderr.strip()}')


def main():
    parser = argparse.ArgumentParser(description='Collect log files from all Chameleon nodes')
    # collection config contains floating IPs and SSH key, separate from experiment config
    parser.add_argument('--collection-config', default='collection_config.yaml', help='Path to collection config file')
    # remote log dir should match the logs.directory value in config.yaml on each node
    parser.add_argument('--remote-log-dir', default='failure-detectors/logs', help='Path to logs directory on remote nodes')
    # local log dir is where all collected logs will be stored before merging
    parser.add_argument('--local-log-dir', default='logs', help='Local directory to collect logs into')
    args = parser.parse_args()

    collection_config = load_collection_config(args.collection_config)
    ssh_key = collection_config['ssh_key']
    nodes = collection_config['nodes']

    # collect logs from each node sequentially
    for node in nodes:
        collect_from_node(
            node['node_id'],
            node['floating_ip'],
            ssh_key,
            args.remote_log_dir,
            args.local_log_dir
        )

    print(f'All logs collected to {args.local_log_dir}/')
    print('Run merge_logs.py next to combine logs by scenario before analysis.')


if __name__ == '__main__':
    main()
