# Name Frequency Parser

A Python utility for parsing and processing name-frequency data from structured strings in Chinese text processing applications.

## Overview

This tool processes strings in the format `name:time:frequency` separated by semicolons, commonly found in Chinese data processing workflows. It can handle Chinese punctuation, deduplicate entries, and extract the most relevant name-frequency pairs.

## Features

- **Format Parsing**: Parses `name:time:frequency` format with semicolon separators
- **Chinese Punctuation**: Automatically converts Chinese punctuation (；：) to English equivalents
- **Deduplication**: Removes duplicate names, keeping entries with highest frequency
- **Time Handling**: Optional time information preservation and comparison
- **Flexible Input**: Auto-detects ID columns and handles various data formats
- **Top-N Results**: Returns top 2 results per ID by default

## Input Format

The parser expects strings in this format:
```
"张三:2023:5;李四:2022:3;王五:2024:2"
```

Where:
- `张三` is the name
- `2023` is the time (optional, can be empty)
- `5` is the frequency (required)
- `;` separates multiple entries

## Usage

### Basic Example

```python
import pandas as pd
from name_frequency_parser import explode_name_frequency

# Sample data
df = pd.DataFrame({
    'id': [1, 2],
    'name_output': [
        '张三:2023:5;李四:2022:3',
        '王五:2024:8;赵六:2023:2'
    ]
})

# Process the data
result = explode_name_frequency(df)
print(result)
```

Output:
```
   id name_output  frequency
0   1        张三          5
1   1        李四          3
2   2        王五          8
3   2        赵六          2
```

### Advanced Usage

```python
# With time information and custom settings
result = explode_name_frequency(
    df,
    name_col='name_output',     # Column containing name data
    id_col='id',                # ID column (auto-detected if None)
    dedup_by_name=True,         # Remove duplicate names
    keep_time=True,             # Include time in output
    drop_empty=False            # Keep rows with no parseable data
)
```

## Function Parameters

### `explode_name_frequency()`

- `df` (pd.DataFrame): Input DataFrame
- `name_col` (str): Column containing name-frequency data (default: "name_output")
- `id_col` (str, optional): ID column name (auto-detected if None)
- `dedup_by_name` (bool): Whether to deduplicate by name (default: True)
- `keep_time` (bool): Whether to include time column in output (default: False)
- `drop_empty` (bool): Whether to drop rows with no parseable data (default: False)

## Test Cases

The package includes comprehensive test cases covering:

1. **Basic Functionality**: Standard parsing of name-frequency data
2. **Time Information**: Handling of time data and missing values
3. **Deduplication**: Removing duplicate names while keeping best entries
4. **Chinese Punctuation**: Converting Chinese punctuation marks
5. **Empty Data**: Handling empty strings and None values
6. **Custom ID Columns**: Working with different ID column names

## Installation Requirements

```
pandas>=1.3.0
numpy>=1.20.0
```

To install dependencies:
```bash
pip install pandas numpy
```

## File Structure

```
workspace/
├── name_frequency_parser.py      # Main parser module
├── test_name_frequency_parser.py # Test suite
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

## Key Features Explained

### Deduplication Logic
When `dedup_by_name=True`, duplicate names are handled by:
1. Keeping the entry with highest frequency
2. If frequencies are equal, keeping the entry with most recent time
3. If times are equal or missing, keeping the first occurrence

### Time Comparison
- Missing times are treated as very early (low priority)
- Higher time values are considered more recent
- Time is optional in the input format

### Output Format
The function returns a DataFrame with columns:
- ID column (original name preserved)
- `name_output`: The parsed name
- `frequency`: The frequency value
- `time`: Time value (if `keep_time=True`)

## Error Handling

The parser gracefully handles:
- Missing or malformed data
- Invalid frequency values (non-numeric)
- Missing time values
- Chinese vs English punctuation
- Empty cells and None values

## Example Use Cases

1. **Customer Name Processing**: Parse customer preference data with frequencies
2. **Product Analysis**: Extract product names with purchase frequencies
3. **Text Mining**: Process structured text data from Chinese sources
4. **Data Cleaning**: Standardize and deduplicate name-frequency datasets

## Notes

- The parser is designed specifically for Chinese data processing workflows
- It handles both Chinese (；：) and English (;:) punctuation
- The code includes comprehensive error handling and validation
- Output is limited to top 2 results per ID to maintain relevance