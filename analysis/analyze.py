import json
import csv
from pathlib import Path
from analysis.metrics import MetricsComputer

class Analyzer:

    def __init__(self, log_dir, node_map):
        self.log_dir = Path(log_dir)
        self.node_map = node_map

    def _get_log_files(self):
        return list(self.log_dir.glob("*.json"))

    def _analyze_log_file(self, filepath):
        # derive scenario name from filename
        scenario_name = filepath.stem.replace('_events', '').replace('_', ' ')

        # create a MetricsComputer from this log file
        computer = MetricsComputer.from_log_file(filepath, self.node_map)

        # compute metrics for each detector found in the file
        results = []
        for detector_name in computer._get_detector_names():
            result = computer.compute_all(detector_name)
            result['scenario'] = scenario_name
            results.append(result)

        return results

    def run(self, output_path):
        # collect results from all log files into one flat list
        all_results = []
        for filepath in self._get_log_files():
            results = self._analyze_log_file(filepath)
            all_results.extend(results)

        # write results to csv
        fieldnames = ['scenario', 'detector', 'false_positive_rate', 'detection_time', 'mistake_rate']
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)