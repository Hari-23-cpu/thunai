import os
import csv
from collections import Counter

def inspect_data():
    raw_dir = 'data/raw/'
    csv_files = [f for f in os.listdir(raw_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in data/raw/")
        return

    # Select the largest CSV file that isn't sample.csv if others exist
    actual_csv = None
    if len(csv_files) > 1:
        csv_files_with_size = [(f, os.path.getsize(os.path.join(raw_dir, f))) for f in csv_files]
        # Filter out sample.csv and pick the largest
        candidates = [f for f in csv_files if f != 'sample.csv']
        if candidates:
            actual_csv = max(candidates, key=lambda f: os.path.getsize(os.path.join(raw_dir, f)))
        else:
            actual_csv = 'sample.csv'
    else:
        actual_csv = csv_files[0]

    file_path = os.path.join(raw_dir, actual_csv)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    print(f"Filename: {actual_csv}")
    print(f"File Size: {file_size_mb:.2f} MB")

    total_rows = 0
    inbound_count = 0
    outbound_count = 0
    outbound_authors = Counter()
    first_five_rows = []
    column_names = []

    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        column_names = reader.fieldnames
        
        for row in reader:
            if total_rows < 5:
                first_five_rows.append(row)
            
            total_rows += 1
            
            # inbound is a string "True" or "False" in CSV
            is_inbound = row['inbound'].lower() == 'true'
            
            if is_inbound:
                inbound_count += 1
            else:
                outbound_count += 1
                outbound_authors[row['author_id']] += 1

    print(f"Column Names: {column_names}")
    print("\nFirst 5 Rows:")
    for i, row in enumerate(first_five_rows):
        print(f"Row {i+1}: {row}")

    print(f"\nTotal Row Count: {total_rows}")
    print(f"Number of Inbound Messages: {inbound_count}")
    print(f"Number of Outbound Messages: {outbound_count}")
    
    print("\nMost Common Brand/Author Handles (Outbound):")
    for author, count in outbound_authors.most_common(10):
        print(f"- {author}: {count}")

if __name__ == "__main__":
    inspect_data()
