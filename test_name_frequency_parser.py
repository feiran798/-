"""
Test script for name_frequency_parser.py

This script demonstrates the usage of the name frequency parser with various test cases.
"""

import pandas as pd
from name_frequency_parser import explode_name_frequency


def test_basic_functionality():
    """Test basic parsing functionality."""
    print("=== Test 1: Basic Functionality ===")
    
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'name_output': [
            '张三:2023:5;李四:2022:3;王五:2024:2',
            '赵六:2023:10;孙七:2022:1',
            '周八:2024:7'
        ]
    })
    
    print("Input:")
    print(df)
    print("\nOutput:")
    result = explode_name_frequency(df)
    print(result)
    print()


def test_with_time():
    """Test with time information preserved."""
    print("=== Test 2: With Time Information ===")
    
    df = pd.DataFrame({
        'id': [1, 2],
        'name_output': [
            '张三:2023:5;李四:2022:3',
            '王五::8;赵六:2024:2'  # Missing time for 王五
        ]
    })
    
    result = explode_name_frequency(df, keep_time=True)
    print("Input:")
    print(df)
    print("\nOutput with time:")
    print(result)
    print()


def test_deduplication():
    """Test name deduplication."""
    print("=== Test 3: Name Deduplication ===")
    
    df = pd.DataFrame({
        'id': [1],
        'name_output': ['张三:2023:5;张三:2022:3;张三:2024:4']  # Same name with different freq/time
    })
    
    print("Input (duplicate names):")
    print(df)
    print("\nOutput (deduplicated, keeping highest frequency):")
    result = explode_name_frequency(df, dedup_by_name=True, keep_time=True)
    print(result)
    print()


def test_chinese_punctuation():
    """Test Chinese punctuation handling."""
    print("=== Test 4: Chinese Punctuation ===")
    
    df = pd.DataFrame({
        'id': [1],
        'name_output': ['张三：2023：5；李四：2022：3']  # Using Chinese punctuation
    })
    
    print("Input (Chinese punctuation):")
    print(df)
    print("\nOutput (normalized):")
    result = explode_name_frequency(df)
    print(result)
    print()


def test_empty_data():
    """Test handling of empty data."""
    print("=== Test 5: Empty Data Handling ===")
    
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'name_output': ['张三:2023:5', '', None]  # Normal, empty, and None
    })
    
    print("Input (with empty/None values):")
    print(df)
    print("\nOutput (drop_empty=False):")
    result1 = explode_name_frequency(df, drop_empty=False)
    print(result1)
    print("\nOutput (drop_empty=True):")
    result2 = explode_name_frequency(df, drop_empty=True)
    print(result2)
    print()


def test_different_id_column():
    """Test with different ID column names."""
    print("=== Test 6: Different ID Column ===")
    
    df = pd.DataFrame({
        'uuid': ['a1', 'b2'],
        'name_output': ['张三:2023:5', '李四:2022:3']
    })
    
    print("Input (with uuid as ID):")
    print(df)
    print("\nOutput:")
    result = explode_name_frequency(df, id_col='uuid')
    print(result)
    print()


if __name__ == "__main__":
    print("Name Frequency Parser - Test Suite")
    print("=" * 50)
    
    test_basic_functionality()
    test_with_time()
    test_deduplication()
    test_chinese_punctuation()
    test_empty_data()
    test_different_id_column()
    
    print("All tests completed!")