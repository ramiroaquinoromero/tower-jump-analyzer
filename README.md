# Tower Jump Analyzer

A Python application for analyzing tower jump data from CSV files. This project provides two implementations: one using the standard Python library and another using pandas for data processing.

## Project Structure

```
tower-jump-analyzer/
├── processor.py          # Standard library implementation
├── test.py              # Pandas implementation
├── requirements.txt     # Project dependencies
├── README.md           # This file
└── data/               # Directory for CSV files (create this)
    └── your_data.csv   # Your tower jump data file
```

## Prerequisites

- Python 3.6 or higher
- pip (Python package manager)

## Installation

1. Clone or download this project to your local machine
2. Navigate to the project directory in your terminal/command prompt
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

If you don't have a requirements.txt file yet, install pandas directly:

```bash
pip install pandas
```

## Usage

### Using the Standard Library Implementation (processor.py)

1. Place your CSV file in the data directory
2. Run the processor:

```bash
python processor.py
```

### Using the Pandas Implementation (test.py)

1. Place your CSV file in the data directory
2. Run the test script:

```bash
python test.py
```

## CSV File Format

Your CSV file should have the following columns:
- UTCDateTime: Date and time in UTC format
- LocalDateTime: Date and time in local timezone format
- Latitude: Latitude coordinate
- Longitude: Longitude coordinate
- Timezone: Timezone information
- City: City name
- County: County name
- Page: Page reference
- Item: Item reference

## Features

- Loads and processes tower jump data from CSV files
- Converts data types and handles missing values
- Analyzes jumps within configurable time windows
- Filters data based on confidence thresholds
- Provides both standard library and pandas implementations

## Configuration

You can adjust the following parameters in the code:
- `time_window_stands`: Time window for analysis (default: 5 minutes)
- `min_confidence`: Minimum confidence threshold (default: 0.0)

## Output

The application will process the data and display:
- Number of records loaded
- Analysis results based on the configured parameters

## Notes

- Make sure your CSV file uses UTF-8 encoding
- The application handles missing coordinate values by setting them to 0.0
- Date/time parsing assumes standard formats but can be adjusted in the code if needed