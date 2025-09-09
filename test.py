import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from collections import Counter
import csv


class TowerJumpAnalyzer:
    def __init__(self, file_path):
        self.df = pd.read_csv(file_path)
        self.timezone_cache = {}

    def preprocess_data(self):
        # Convert datetime strings to datetime objects
        self.df["UTCDateTime"] = pd.to_datetime(
            self.df["UTCDateTime"], format="%m/%d/%y %H:%M"
        )
        self.df["LocalDateTime"] = pd.to_datetime(
            self.df["LocalDateTime"], format="%m/%d/%y %H:%M", errors="coerce"
        )

        # Fill missing states based on coordinates when possible
        self._fill_missing_locations()

        # Sort by time
        self.df = self.df.sort_values("UTCDateTime").reset_index(drop=True)

    def _fill_missing_locations(self):
        """Try to fill missing state information based on coordinates"""
        # Create a mapping of coordinates to states for known entries
        coord_state_map = {}
        for idx, row in self.df.iterrows():
            if (
                not pd.isna(row["Latitude"])
                and row["Latitude"] != 0
                and not pd.isna(row["Longitude"])
                and row["Longitude"] != 0
            ):
                coord_key = (round(row["Latitude"], 4), round(row["Longitude"], 4))
                if not pd.isna(row["State"]) and row["State"] != "":
                    if coord_key not in coord_state_map:
                        coord_state_map[coord_key] = []
                    coord_state_map[coord_key].append(row["State"])

        # Find the most common state for each coordinate
        for coord, states in coord_state_map.items():
            coord_state_map[coord] = Counter(states).most_common(1)[0][0]

        # Fill missing states using the coordinate mapping
        for idx, row in self.df.iterrows():
            if (
                (pd.isna(row["State"]) or row["State"] == "")
                and not pd.isna(row["Latitude"])
                and row["Latitude"] != 0
                and not pd.isna(row["Longitude"])
                and row["Longitude"] != 0
            ):
                coord_key = (round(row["Latitude"], 4), round(row["Longitude"], 4))
                if coord_key in coord_state_map:
                    self.df.at[idx, "State"] = coord_state_map[coord_key]

    def analyze_tower_jumps(self, time_window_minutes=5, min_confidence=0.6):
        """Analyze the data to identify tower jumps and determine location with confidence"""
        results = []
        current_interval_start = None
        current_state = None
        state_records = []

        for idx, row in self.df.iterrows():
            # Skip records without state information
            if pd.isna(row["State"]) or row["State"] == "":
                continue

            record_time = row["UTCDateTime"]

            # Initialize the first interval
            if current_interval_start is None:
                current_interval_start = record_time
                current_state = row["State"]
                state_records = [row["State"]]
                continue

            # Check if we're still in the same time window
            time_diff = (record_time - current_interval_start).total_seconds() / 60

            if time_diff <= time_window_minutes:
                # Still in the same time window, collect state information
                state_records.append(row["State"])
            else:
                # Time to finalize the current interval and start a new one
                state_counter = Counter(state_records)
                most_common_state, count = state_counter.most_common(1)[0]
                confidence = count / len(state_records)

                # Determine if this is a tower jump
                is_tower_jump = len(state_counter) > 1 and confidence < min_confidence

                results.append(
                    {
                        "start_time": current_interval_start,
                        "end_time": record_time
                        - timedelta(minutes=1),  # End just before the new record
                        "state": most_common_state,
                        "is_tower_jump": "yes" if is_tower_jump else "no",
                        "confidence": confidence * 100,  # Convert to percentage
                    }
                )

                # Start new interval
                current_interval_start = record_time
                state_records = [row["State"]]

        # Add the last interval
        if state_records:
            state_counter = Counter(state_records)
            most_common_state, count = state_counter.most_common(1)[0]
            confidence = count / len(state_records)
            is_tower_jump = len(state_counter) > 1 and confidence < min_confidence

            results.append(
                {
                    "start_time": current_interval_start,
                    "end_time": self.df.iloc[-1]["UTCDateTime"],
                    "state": most_common_state,
                    "is_tower_jump": "yes" if is_tower_jump else "no",
                    "confidence": confidence * 100,
                }
            )

        return pd.DataFrame(results)

    def save_results(self, results_df, output_file):
        """Save results to a CSV file"""
        results_df.to_csv(
            output_file,
            index=False,
            columns=["start_time", "end_time", "state", "is_tower_jump", "confidence"],
            date_format="%Y-%m-%d %H:%M:%S",
        )

    def generate_report(self, output_file, time_window_minutes=5, min_confidence=0.6):
        """Generate the complete analysis report"""
        print("Preprocessing data...")
        self.preprocess_data()

        print("Analyzing tower jumps...")
        results = self.analyze_tower_jumps(time_window_minutes, min_confidence)

        print(f"Saving results to {output_file}...")
        self.save_results(results, output_file)

        print("Analysis complete!")
        return results


# Simple command-line interface
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze cell tower data for tower jumps"
    )
    parser.add_argument("input_file", help="Path to the input CSV file")
    parser.add_argument("output_file", help="Path to the output CSV file")
    parser.add_argument(
        "--window",
        type=int,
        default=5,
        help="Time window in minutes for analysis (default: 5)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.6,
        help="Minimum confidence threshold (default: 0.6)",
    )

    args = parser.parse_args()

    analyzer = TowerJumpAnalyzer(args.input_file)
    results = analyzer.generate_report(args.output_file, args.window, args.confidence)

    print(f"\nReport generated with {len(results)} time intervals")
    print(f"Tower jumps detected: {len(results[results['is_tower_jump'] == 'yes'])}")


if __name__ == "__main__":
    main()
