#!/usr/bin/env python3
"""
Debug script to see what's happening with CSV parsing
"""

import csv
import ast
import re
from datetime import datetime

def convert_np_float64(value_str):
    """Convert np.float64 string to float"""
    if isinstance(value_str, str) and 'np.float64(' in value_str:
        match = re.search(r'np\.float64\(([^)]+)\)', value_str)
        if match:
            return float(match.group(1))
    return value_str

def safe_eval_list(value_str):
    """Safely evaluate stringified list of dictionaries"""
    try:
        if value_str.startswith('[') and value_str.endswith(']'):
            return ast.literal_eval(value_str)
        return []
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing: {e}")
        return []

def debug_breathing_rate():
    """Debug breathing_rate.csv parsing"""
    print("=== Debugging Breathing Rate ===")
    try:
        with open('ingest/data/breathing_rate.csv', 'r') as file:
            reader = csv.DictReader(file)
            for i, row in enumerate(reader):
                print(f"Row {i+1}:")
                print(f"  br column: {row['br'][:100]}...")
                
                br_data = safe_eval_list(row['br'])
                print(f"  Parsed data: {br_data}")
                
                if br_data:
                    timestamp_str = br_data[0].get('dateTime', '')
                    print(f"  Timestamp: {timestamp_str}")
                    
                    if timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        print(f"  Parsed timestamp: {timestamp}")
                        
                        for item in br_data:
                            print(f"  Item: {item}")
                            if 'value' in item:
                                print(f"    Value: {item['value']}")
                                if isinstance(item['value'], dict):
                                    for stage, rate_data in item['value'].items():
                                        print(f"      Stage: {stage}, Rate data: {rate_data}")
                                        if isinstance(rate_data, dict) and 'breathingRate' in rate_data:
                                            rate = convert_np_float64(rate_data['breathingRate'])
                                            print(f"        Rate: {rate}")
                                        elif isinstance(rate_data, (int, float)):
                                            rate = convert_np_float64(rate_data)
                                            print(f"        Rate: {rate}")
                
                if i >= 0:  # Only process first row for debugging
                    break
    except Exception as e:
        print(f"Error: {e}")

def debug_spo2():
    """Debug spo2.csv parsing"""
    print("\n=== Debugging SPO2 ===")
    try:
        with open('ingest/data/spo2.csv', 'r') as file:
            reader = csv.DictReader(file)
            for i, row in enumerate(reader):
                print(f"Row {i+1}:")
                print(f"  dateTime: {row['dateTime']}")
                print(f"  minutes column: {row['minutes'][:100]}...")
                
                minutes_data = safe_eval_list(row['minutes'])
                print(f"  Parsed data length: {len(minutes_data)}")
                
                if minutes_data:
                    print(f"  First item: {minutes_data[0]}")
                    
                    for j, item in enumerate(minutes_data[:3]):  # First 3 items
                        print(f"    Item {j+1}: {item}")
                        if 'value' in item and 'minute' in item:
                            value = convert_np_float64(item['value'])
                            minute_str = item['minute']
                            print(f"      Value: {value}, Minute: {minute_str}")
                            
                            try:
                                timestamp = datetime.fromisoformat(minute_str.replace('Z', '+00:00'))
                                print(f"      Parsed timestamp: {timestamp}")
                            except Exception as e:
                                print(f"      Timestamp error: {e}")
                
                if i >= 0:  # Only process first row for debugging
                    break
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_breathing_rate()
    debug_spo2() 