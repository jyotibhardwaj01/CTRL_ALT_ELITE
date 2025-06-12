import csv
import json
import os

# Define file paths
csv_file_path = os.path.join('Dataset', 'Dataset.CSV')
json_file_path = os.path.join('input', 'Dataset.json')

# Read CSV and convert to list of dictionaries
data = []
try:
    with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            data.append(row)
except FileNotFoundError:
    print(f"Error: The file {csv_file_path} was not found.")
    exit()
except Exception as e:
    print(f"An error occurred while reading the CSV file: {e}")
    exit()

# Ensure the output directory exists
output_dir = os.path.dirname(json_file_path)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Write JSON data
try:
    with open(json_file_path, mode='w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Successfully converted {csv_file_path} to {json_file_path}")
except Exception as e:
    print(f"An error occurred while writing the JSON file: {e}")
    exit()
