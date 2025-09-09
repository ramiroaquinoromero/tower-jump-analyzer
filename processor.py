import csv
from datetime import datetime, timedelta
from collections import defaultdict, Counter


class TowerJumpAnalyzer:
    def __init__(self, filename):
        self.filename = filename
        self.data = []
        self.time_window_minutes = 5  # Time window for analysis
        self.min_confidence = 0.6  # Minimum confidence threshold

    def load_data(self):
        """Load data from CSV file"""
        print("Loading data...")
        with open(self.filename, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Convert and clean the data
                processed_row = self._process_row(row)
                if processed_row:
                    self.data.append(processed_row)

        print(f"Data loaded: {len(self.data)} records")

    def _process_row(self, row):
        """Process a row of data and convert types as needed"""
        try:
            # Convert dates
            utc_dt = self._parse_datetime(row["UTCDateTime"])
            local_dt = self._parse_datetime(row["LocalDateTime"])

            # Convert coordinates
            lat = float(row["Latitude"]) if row["Latitude"] else 0.0
            lon = float(row["Longitude"]) if row["Longitude"] else 0.0

            # Create new processed record
            processed = {
                "page": int(row["Page"]),
                "item": int(row["Item"]),
                "utc_datetime": utc_dt,
                "local_datetime": local_dt,
                "latitude": lat,
                "longitude": lon,
                "timezone": row["TimeZone"],
                "city": row["City"],
                "county": row["County"],
                "state": row["State"],
                "country": row["Country"],
                "cell_type": row["CellType"],
            }

            return processed
        except (ValueError, KeyError) as e:
            print(f"Error processing row: {e}")
            return None

    def _parse_datetime(self, dt_str):
        """Convert date/time string to datetime object"""
        try:
            # Format: month/day/year hour:minute
            return datetime.strptime(dt_str, "%m/%d/%y %H:%M")
        except ValueError:
            # Try alternative format if needed
            try:
                return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"Could not parse date: {dt_str}")
                return None

    def fill_missing_states(self):
        """Fill missing states based on known coordinates"""
        print("Filling missing states...")

        # Create a coordinate to state mapping
        coord_to_state = {}
        for record in self.data:
            if (
                record["state"]
                and record["state"].strip()
                and record["latitude"] != 0
                and record["longitude"] != 0
            ):
                # Round coordinates to group nearby locations
                coord_key = (
                    round(record["latitude"], 3),
                    round(record["longitude"], 3),
                )
                if coord_key not in coord_to_state:
                    coord_to_state[coord_key] = []
                coord_to_state[coord_key].append(record["state"])

        # Find the most common state for each coordinate
        for coord, states in coord_to_state.items():
            counter = Counter(states)
            coord_to_state[coord] = counter.most_common(1)[0][0]

        # Fill missing states
        filled_count = 0
        for record in self.data:
            if not record["state"] or not record["state"].strip():
                if record["latitude"] != 0 and record["longitude"] != 0:
                    coord_key = (
                        round(record["latitude"], 3),
                        round(record["longitude"], 3),
                    )
                    if coord_key in coord_to_state:
                        record["state"] = coord_to_state[coord_key]
                        filled_count += 1

        print(f"States filled: {filled_count}")

    def analyze_tower_jumps(self):
        """Analyze the data to identify tower jumps"""
        print("Analyzing tower jumps...")

        # Sort data by time
        sorted_data = sorted(self.data, key=lambda x: x["utc_datetime"])

        results = []
        current_interval = None

        for record in sorted_data:
            # Skip records without state
            if not record["state"] or not record["state"].strip():
                continue

            if current_interval is None:
                # Start the first interval
                current_interval = {
                    "start_time": record["utc_datetime"],
                    "end_time": record["utc_datetime"],
                    "states": [record["state"]],
                    "records": [record],
                }
            else:
                # Check if we're within the current time window
                time_diff = (
                    record["utc_datetime"] - current_interval["end_time"]
                ).total_seconds() / 60

                if time_diff <= self.time_window_minutes:
                    # Add to current interval
                    current_interval["end_time"] = record["utc_datetime"]
                    current_interval["states"].append(record["state"])
                    current_interval["records"].append(record)
                else:
                    # Finalize current interval and start a new one
                    result = self._process_interval(current_interval)
                    results.append(result)

                    # Start new interval
                    current_interval = {
                        "start_time": record["utc_datetime"],
                        "end_time": record["utc_datetime"],
                        "states": [record["state"]],
                        "records": [record],
                    }

        # Process the last interval
        if current_interval:
            result = self._process_interval(current_interval)
            results.append(result)

        return results

    def _process_interval(self, interval):
        """Process a time interval and determine state and confidence"""
        state_counter = Counter(interval["states"])
        total_records = len(interval["states"])

        # Find the most common state
        most_common_state, count = state_counter.most_common(1)[0]
        confidence = count / total_records

        # Determine if it's a tower jump
        is_tower_jump = len(state_counter) > 1 and confidence < self.min_confidence

        return {
            "start_time": interval["start_time"],
            "end_time": interval["end_time"],
            "state": most_common_state,
            "is_tower_jump": "yes" if is_tower_jump else "no",
            "confidence_percentage": round(confidence * 100, 2),
            "total_records": total_records,
            "states_count": dict(state_counter),
        }

    def generate_report(self, output_filename):
        """Generate the final report in CSV"""
        print("Generating report...")

        # Fill missing states first
        self.fill_missing_states()

        # Analyze tower jumps
        results = self.analyze_tower_jumps()

        # Write results to CSV
        with open(output_filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "start_time",
                "end_time",
                "state",
                "is_tower_jump",
                "confidence_percentage",
                "total_records",
                "states_count",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for result in results:
                # Convert state count dictionary to string for CSV
                result_copy = result.copy()
                result_copy["states_count"] = str(result["states_count"])
                writer.writerow(result_copy)

        print(f"Report saved as: {output_filename}")
        return results


# Main function to run the analysis
def main():
    # Configure parameters
    input_file = "20250709_4245337_CarrierData_new.csv"
    output_file = "tower_jump_analysis_report.csv"

    # Create analyzer and execute
    analyzer = TowerJumpAnalyzer(input_file)
    analyzer.load_data()
    results = analyzer.generate_report(output_file)

    # Show summary
    total_intervals = len(results)
    tower_jumps = sum(1 for r in results if r["is_tower_jump"] == "yes")

    print(f"\nAnalysis Summary:")
    print(f"Total intervals: {total_intervals}")
    print(f"Tower jumps detected: {tower_jumps}")
    print(f"Jump percentage: {round(tower_jumps/total_intervals*100, 2)}%")

    # Show some examples
    print("\nFirst 5 intervals:")
    for i, result in enumerate(results[:5]):
        print(
            f"{i+1}. {result['start_time']} to {result['end_time']}: "
            f"{result['state']} (Conf: {result['confidence_percentage']}%, "
            f"Tower Jump: {result['is_tower_jump']})"
        )


if __name__ == "__main__":
    main()
