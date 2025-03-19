# URL Checker

A Python script for bulk checking the status of multiple URLs, identifying broken links, and generating detailed reports.

## Features

- ✅ Check multiple URLs in parallel for maximum efficiency
- ✅ Handles redirects, timeouts, and connection errors
- ✅ Smart request handling - uses HEAD requests when possible, falls back to GET when needed
- ✅ Progress tracking during URL checking
- ✅ Detailed CSV report generation
- ✅ Command-line interface with customization options
- ✅ Can load URLs from a text file

## Installation

### Prerequisites

- Python 3.6 or higher
- `requests` library

### Setup

1. **Create a virtual environment** (recommended):

   **Windows:**
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

   **macOS/Linux:**
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```
   pip install requests
   ```

## Usage

### Basic Usage

Run with example URLs:
```
python url_checker.py
```

### Check URLs from a File

Create a text file with one URL per line, then:
```
python url_checker.py urls.txt
```

### Command Line Options

```
python url_checker.py [file] [options]
```

Options:
- `-t, --timeout SECONDS`: Set request timeout (default: 10)
- `-w, --workers NUMBER`: Set maximum concurrent workers (default: 10)
- `-o, --output FILENAME`: Specify output CSV file (default: url_check_results.csv)
- `-v, --verify-ssl`: Enable SSL certificate verification (default: False)

Example:
```
python url_checker.py urls.txt --timeout 5 --workers 20 --output results.csv
```

## Output

The script generates two types of output:

1. **Console output**: Shows progress and summary of working, broken, and error URLs.
2. **CSV report**: Contains detailed information about each URL check, including:
   - URL
   - Status code
   - Response reason
   - Response time
   - Error information (if any)
   - Redirect information (if any)

## Examples

### Example 1: Checking a Small List of URLs

Create a file named `urls.txt`:
```
google.com
example.com
github.com
thisisnotarealwebsite123456789.com
```

Run the check:
```
python tool.py urls.txt
```

