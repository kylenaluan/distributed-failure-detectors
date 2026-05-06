# Configuration Guide

This document explains the configuration files used by the failure detector system and how to set them up for local testing and Chameleon Cloud deployment.

---

## config_ci_10.yaml

The main experiment configuration file. It is committed to the repository and defines all experiment parameters including node addresses, heartbeat timing, detector thresholds, and log/results directories.

### Node IP Addresses

The `nodes` section defines the identity and address of each node in the cluster. For local testing, all five nodes use `127.0.0.1` (localhost) with different ports. For Chameleon deployment, the `host` field for each node must be replaced with the private IP assigned to that node on the `failure-detector-net` isolated VLAN interface.

```yaml
nodes:
  - node_id: node-1
    host: 127.0.0.1
    port: 5001
  - node_id: node-2
    host: 127.0.0.1
    port: 5002
  - node_id: node-3
    host: 127.0.0.1
    port: 5003
  - node_id: node-4
    host: 127.0.0.1
    port: 5004
  - node_id: node-5
    host: 127.0.0.1
    port: 5005
```
> **Important:** The same `config_ci_10.yaml` must be deployed to all five nodes with identical content. Every node needs the full list of all five node addresses so it can add the others as peers.

### Other Parameters

The remaining parameters in `config_ci_10.yaml` are tuned and should not need to be changed for Chameleon deployment:

- `heartbeat.interval` — how often each node sends heartbeats (1.0s)
- `heartbeat.check_interval` — how often detectors check for failures (0.5s)
- `detectors` — threshold and window size parameters for each of the four detectors
- `logs.directory` — where experiment log files are written on each node

---

## config_ci_20.yaml and config_ci_30.yaml

These are supplementary configs used for the CI-FD window size comparison experiment. They are identical to `config_ci_10.yaml` except for `confidence_interval.window_size` (20 and 30 respectively) and `logs.directory` (pointing to `logs_ci_20/` and `logs_ci_30/` to keep runs separate).

When running these on Chameleon, update the node `host` fields in the same way as `config_ci_10.yaml`.

---

## collection_config_ci_10.yaml

This file is **not in the repository** — it is listed in `.gitignore` and must be created manually on your local machine before collecting logs from Chameleon nodes.

### Why it is not committed

`collection_config_ci_10.yaml` contains a SSH private key path and the floating IPs of your Chameleon nodes. Floating IPs change every time a new lease is created, so the file would be stale immediately after any lease renewal. More importantly, exposing SSH key paths alongside node addresses in a public or shared repository is a security risk. For these reasons the file is intentionally excluded from version control.

### Format

Create `collection_config_ci_10.yaml` in the project root with the following structure:

```yaml
ssh_key: ~/.ssh/your-key.pem

nodes:
  - node_id: node-1
    floating_ip: 129.xxx.xxx.xxx
  - node_id: node-2
    floating_ip: 129.xxx.xxx.xxx
  - node_id: node-3
    floating_ip: 129.xxx.xxx.xxx
  - node_id: node-4
    floating_ip: 129.xxx.xxx.xxx
  - node_id: node-5
    floating_ip: 129.xxx.xxx.xxx
```

### What goes in each field

- `ssh_key` — path to the `.pem` file you downloaded when creating your Chameleon key pair. On Windows use a full path like `C:/Users/yourname/.ssh/your-key.pem`.
- `floating_ip` — the public floating IP associated with each node's `sharednet1` interface. Find these under Network → Floating IPs in the Chameleon dashboard. These are the IPs you use to SSH into each node, not the private `failure-detector-net` IPs.

### Usage

`collection_config_ci_10.yaml` is read by `scripts/collect_logs.py` after experiments finish. It tells the script which nodes to connect to and how to authenticate:

python scripts/collect_logs.py

This pulls each node's log files to your local machine into `logs/{node_id}/` directories, after which you can run `scripts/merge_logs.py` and `analyze.py` to produce results.