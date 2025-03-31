import pandas as pd
import os
import json

# Path to the Excel file
excel_file = 'attached_assets/Appendix D - Circuit IDs.xlsx'

# Check if the file exists
if not os.path.exists(excel_file):
    print(f"Error: File not found at {excel_file}")
    exit(1)

try:
    # Get all sheet names
    xlsx = pd.ExcelFile(excel_file)
    sheet_names = xlsx.sheet_names
    print(f"Found {len(sheet_names)} sheets in the workbook:")
    for i, name in enumerate(sheet_names):
        print(f"{i+1}. {name}")
    
    # Create a dictionary to store all sheet data
    all_data = {}
    
    # Read each sheet and extract data
    for sheet_name in sheet_names:
        print(f"\nReading sheet: {sheet_name}")
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # Skip empty sheets or sheets with no data
        if df.shape[0] <= 3:  # If the sheet has only a few rows, it might be header info
            print(f"Sheet '{sheet_name}' appears to be empty or only contains headers. Skipping.")
            continue
            
        print(f"Shape: {df.shape} (rows, columns)")
        
        # Find the header row - usually it's the first row with meaningful column names
        header_row = 0
        for i in range(min(10, df.shape[0])):  # Check the first 10 rows
            # If this row has values like "Market", "Provider", "Circuit ID", etc.
            if any(str(val).lower() in ["market", "provider", "circuit id", "description", "status"] 
                  for val in df.iloc[i].values if pd.notna(val)):
                header_row = i
                print(f"Found header row at index {header_row}")
                break
        
        # Set the header row as column names
        if header_row > 0:
            column_names = df.iloc[header_row].values
            df = df.iloc[header_row+1:].reset_index(drop=True)
            df.columns = column_names
            
        # Clean column names - replace NaN with descriptive names
        renamed_columns = {}
        for i, col in enumerate(df.columns):
            if pd.isna(col) or str(col).startswith('Unnamed:'):
                renamed_columns[col] = f"Column_{i+1}"
        
        if renamed_columns:
            df = df.rename(columns=renamed_columns)
        
        # Display column names after cleaning
        print("Cleaned Columns:")
        for col in df.columns:
            print(f"  - {col}")
        
        # Remove rows that are completely empty
        df = df.dropna(how='all')
        
        # Attempt to identify key columns
        key_columns = []
        for col in df.columns:
            col_str = str(col).lower()
            if any(key in col_str for key in ["circuit", "id", "market", "provider", "status"]):
                key_columns.append(col)
                
        print(f"Key columns identified: {key_columns}")
        
        # Preview first few rows
        print("\nPreview (first 3 rows, key columns only):")
        preview_df = df.head(3)
        if key_columns:
            preview_df = preview_df[key_columns]
        preview = preview_df.to_dict('records')
        print(json.dumps(preview, indent=2, default=str))
        
        # Store the data in the dictionary
        all_data[sheet_name] = df.to_dict('records')
    
    # Save the extracted data to a JSON file for easier handling in Flask
    output_file = 'circuit_ids_data.json'
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2, default=str)
    
    print(f"\nExtracted data saved to {output_file}")
    
except Exception as e:
    print(f"Error reading file: {str(e)}")