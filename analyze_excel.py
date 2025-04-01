#!/usr/bin/env python3
"""
Script to analyze the Excel file structure and identify the columns for each sheet.
"""
import pandas as pd
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_excel_file(excel_path):
    """
    Analyze the Excel file and print the column structure for each sheet.
    """
    try:
        # Read the Excel file into a pandas ExcelFile object
        excel_file = pd.ExcelFile(excel_path)
        
        # Process each sheet
        for sheet_name in excel_file.sheet_names:
            # Skip sheets that might be for documentation or other purposes
            if sheet_name in ['Summary', 'Notes', 'Instructions', 'README']:
                logger.info(f"Skipping sheet: {sheet_name}")
                continue
                
            logger.info(f"\n===== Processing sheet: {sheet_name} =====")
            
            # Read the sheet into a DataFrame
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Skip empty sheets
            if df.empty:
                logger.info(f"Sheet {sheet_name} is empty, skipping")
                continue
            
            # Print column names and first few values
            logger.info(f"Columns in {sheet_name}:")
            for i, col in enumerate(df.columns):
                logger.info(f"Column {i} ({col}):")
                # Print first 3 non-null values for each column
                non_null_values = df[col].dropna().head(3).tolist()
                if non_null_values:
                    logger.info(f"  Sample values: {non_null_values}")
                else:
                    logger.info("  No non-null values found")
            
            # More detailed analysis for specific sheets
            if sheet_name == 'CoreSite - Atlanta':
                logger.info("\nDetailed analysis for CoreSite - Atlanta:")
                # Specifically look at column F which should be 'Unnamed: 5'
                if 'Unnamed: 5' in df.columns:
                    col_f_values = df['Unnamed: 5'].dropna().tolist()
                    logger.info(f"Column F ('Unnamed: 5') values: {col_f_values[:10]}")
                    
                # Also look at column D which should be 'Unnamed: 3'
                if 'Unnamed: 3' in df.columns:
                    col_d_values = df['Unnamed: 3'].dropna().tolist()
                    logger.info(f"Column D ('Unnamed: 3') values: {col_d_values[:10]}")
                    
            elif sheet_name == 'Cologix - Jacksonville':
                logger.info("\nDetailed analysis for Cologix - Jacksonville:")
                # Look at column B which should be 'Unnamed: 1'
                if 'Unnamed: 1' in df.columns:
                    col_b_values = df['Unnamed: 1'].dropna().tolist()
                    logger.info(f"Column B ('Unnamed: 1') values: {col_b_values[:10]}")
                
                # Also look at column S which should be 'Unnamed: 18'
                if 'Unnamed: 18' in df.columns:
                    col_s_values = df['Unnamed: 18'].dropna().tolist()
                    logger.info(f"Column S ('Unnamed: 18') values: {col_s_values[:10]}")
    
    except Exception as e:
        logger.error(f"Error analyzing Excel file: {e}")
        raise

def analyze_coresite_atlanta():
    """
    Focus specifically on CoreSite - Atlanta data to identify all required columns.
    """
    try:
        excel_path = 'attached_assets/Appendix D - Circuit IDs.xlsx'
        logger.info(f"Reading CoreSite - Atlanta sheet from {excel_path}")
        
        # Read the specific sheet
        df = pd.read_excel(excel_path, sheet_name='CoreSite - Atlanta')
        
        # List of columns to analyze based on requirements
        columns_to_check = {
            'A': ('Unnamed: 0', 'Cross Connect Description'),
            'B': ('Unnamed: 1', 'CoreSite XCON ID'),
            'C': ('Unnamed: 2', 'CoreSite Case Number'),
            'D': ('Unnamed: 3', 'CoreSite Service Number'),
            'E': ('Unnamed: 4', 'Provider'),
            'F': ('Unnamed: 5', 'Circuit ID'),
            'G': ('Unnamed: 6', 'Space ID - A Location'),
            'H': ('Unnamed: 7', 'Cabinet Number - A Location'),
            'I': ('Unnamed: 8', 'Demarc Location - A Location'),
            'J': ('Unnamed: 9', 'Patch Panel Port - A Location'),
            'L': ('Unnamed: 11', 'Space ID - Z Location'),
            'M': ('Unnamed: 12', 'Cabinet Number - Z Location'),
            'N': ('Unnamed: 13', 'Demarc Location - Z Location'),
            'P': ('Unnamed: 15', 'Patch Panel Port - Z Location')
        }
        
        # Print all column headers
        logger.info("\nAll column headers in CoreSite - Atlanta sheet:")
        for i, col in enumerate(df.columns):
            col_letter = chr(65 + i) if i < 26 else chr(64 + i // 26) + chr(65 + i % 26)
            logger.info(f"Column {col_letter} ({i}): {col}")
            
        # Print info about each required column
        logger.info("\nRequired columns analysis:")
        for col_letter, (col_name, expected_content) in columns_to_check.items():
            logger.info(f"\nColumn {col_letter} ({col_name}, expected to be {expected_content}):")
            if col_name in df.columns:
                values = df[col_name].dropna().head(5).tolist()
                logger.info(f"Values: {values}")
            else:
                logger.info("Column not found")
                
        # Look at some key rows to understand the structure
        logger.info("\nSome key rows with circuit data:")
        # Find rows with actual circuit data (typically after the header rows)
        for idx, row in df.iloc[15:20].iterrows():
            logger.info(f"\nRow {idx}:")
            for col, val in row.items():
                if not pd.isna(val):
                    logger.info(f"  {col}: {val}")
    
    except Exception as e:
        logger.error(f"Error analyzing CoreSite - Atlanta: {e}")
        raise

def analyze_arelion():
    """
    Focus specifically on Arelion data to identify column structure,
    including IP address columns: Local IPv4 (N), Remote IPv4 (O), Local IPv6 (P), Remote IPv6 (Q).
    """
    try:
        excel_path = 'attached_assets/Appendix D - Circuit IDs.xlsx'
        logger.info(f"Reading Arelion sheet from {excel_path}")
        
        # Read the specific sheet
        df = pd.read_excel(excel_path, sheet_name='Arelion')
        
        # Print key column names for reference
        logger.info("\nKey columns in Arelion sheet:")
        logger.info(f"Column A (Unnamed: 0) - Expected to be Market")
        logger.info(f"Column B (Unnamed: 1) - Expected to be Provider")
        logger.info(f"Column C (Unnamed: 2) - Expected to be Description")
        logger.info(f"Column D (Unnamed: 3) - Expected to be Circuit ID")
        logger.info(f"Column E (Unnamed: 4) - Expected to be Status")
        
        # Look at the values in all key columns
        logger.info("\nColumn A values (Market):")
        logger.info(f"Values: {df.iloc[:, 0].dropna().head(10).tolist()}")
        
        logger.info("\nColumn B values (Provider):")
        logger.info(f"Values: {df.iloc[:, 1].dropna().head(10).tolist()}")
        
        logger.info("\nColumn C values (Description):")
        logger.info(f"Values: {df.iloc[:, 2].dropna().head(10).tolist()}")
        
        logger.info("\nColumn D values (Circuit ID):")
        logger.info(f"Values: {df.iloc[:, 3].dropna().head(10).tolist()}")
        
        logger.info("\nColumn E values (Status):")
        logger.info(f"Values: {df.iloc[:, 4].dropna().head(10).tolist()}")
        
        # IP address columns (N, O, P, Q)
        logger.info("\nIP address columns:")
        
        # Map columns to their expected meanings
        ip_columns = {
            13: 'Local IPv4',   # Column N
            14: 'Remote IPv4',  # Column O
            15: 'Local IPv6',   # Column P
            16: 'Remote IPv6'   # Column Q
        }
        
        # Print column headers for all columns to see what's available
        logger.info("\nAll column headers:")
        for i, col in enumerate(df.columns):
            col_letter = chr(65 + i) if i < 26 else chr(64 + i//26) + chr(65 + i%26)
            logger.info(f"Column {col_letter} ({i}): {col}")
        
        # Examine the IP address columns
        for col_idx, ip_type in ip_columns.items():
            if col_idx < len(df.columns):
                col_name = df.columns[col_idx]
                col_letter = chr(65 + col_idx) if col_idx < 26 else chr(64 + col_idx//26) + chr(65 + col_idx%26)
                logger.info(f"\nColumn {col_letter} ({col_name}) - {ip_type}:")
                values = df.iloc[:, col_idx].dropna().head(5).tolist()
                logger.info(f"Sample values: {values}")
            else:
                logger.info(f"\nColumn index {col_idx} ({ip_type}) is out of range")
        
        # Print sample rows with both basic info and IP addresses
        logger.info("\nSample rows with IP addresses:")
        for idx in range(3, min(8, len(df))):  # Skip header rows
            if pd.isna(df.iloc[idx, 3]):  # Skip rows without Circuit ID
                continue
                
            row_info = [f"Circuit ID: {df.iloc[idx, 3]}"]
            
            # Add IP address information if available
            for col_idx, ip_type in ip_columns.items():
                if col_idx < len(df.columns) and not pd.isna(df.iloc[idx, col_idx]):
                    row_info.append(f"{ip_type}: {df.iloc[idx, col_idx]}")
            
            logger.info(" | ".join(row_info))
    
    except Exception as e:
        logger.error(f"Error analyzing Arelion sheet: {e}")

def analyze_accelecom():
    """
    Focus specifically on Accelecom data to identify the column structure
    and check for duplicate column headers that might be causing issues.
    """
    try:
        excel_path = 'attached_assets/Appendix D - Circuit IDs.xlsx'
        logger.info(f"Reading Accelecom sheet from {excel_path}")
        
        # Read the specific sheet
        df = pd.read_excel(excel_path, sheet_name='Accelecom')
        
        # Analyze column structure to check for duplicates
        logger.info("\nChecking for duplicate column headers in Accelecom sheet:")
        column_counts = {}
        for i, col in enumerate(df.columns):
            col_letter = chr(65 + i) if i < 26 else chr(64 + i//26) + chr(65 + i%26)
            logger.info(f"Column {col_letter} ({i}): {col}")
            
            if col in column_counts:
                column_counts[col] += 1
            else:
                column_counts[col] = 1
        
        # Print any duplicate columns
        duplicate_cols = {col: count for col, count in column_counts.items() if count > 1}
        if duplicate_cols:
            logger.info("\nDuplicate column headers found:")
            for col, count in duplicate_cols.items():
                logger.info(f"Column {col} appears {count} times")
        else:
            logger.info("\nNo duplicate column headers found")
        
        # Print the first row to see the actual header values
        logger.info("\nFirst row (likely header row):")
        first_row = df.iloc[0]
        for i, val in enumerate(first_row):
            col_letter = chr(65 + i) if i < 26 else chr(64 + i//26) + chr(65 + i%26)
            col_name = df.columns[i]
            logger.info(f"Column {col_letter} ({col_name}): {val}")
        
        # Print specific column mappings requested by the user
        logger.info("\nChecking requested column mappings:")
        column_mappings = {
            'A': 'Market',
            'B': 'Provider',
            'C': 'Description',
            'D': 'Circuit ID',
            'E': 'Status',
            'H': 'Access Provider',
            'J': 'Account Number',
            'K': 'Online Portal',
            'L': '24x7 Support Number',
            'M': 'Support E-mail',
            'AD': 'A LOC Description',
            'AE': 'A LOC Address 1',
            'AG': 'A LOC City',
            'AH': 'A LOC State',
            'AI': 'A LOC Zip',
            'AL': 'Z LOC Description',
            'AM': 'Z LOC Address 1',
            'AN': 'Z LOC Address 2',
            'AO': 'Z LOC City',
            'AP': 'Z LOC State',
            'BC': 'Notes'
        }
        
        # Convert column letters to indices
        col_to_index = {}
        for col_letter, field_name in column_mappings.items():
            if len(col_letter) == 1:
                idx = ord(col_letter) - ord('A')
            else:
                idx = (ord(col_letter[0]) - ord('A') + 1) * 26 + (ord(col_letter[1]) - ord('A'))
            
            if idx < len(df.columns):
                col_name = df.columns[idx]
                sample_values = df.iloc[1:4, idx].dropna().tolist()
                logger.info(f"{col_letter} ({col_name}) => {field_name}: {sample_values}")
                col_to_index[field_name] = idx
            else:
                logger.info(f"{col_letter} => {field_name}: Column index out of range")
                
        # Print sample records from the sheet
        logger.info("\nSample records from Accelecom sheet:")
        for idx in range(1, min(5, len(df))):  # Skip header row(s)
            record = {}
            for field_name, col_idx in col_to_index.items():
                if col_idx < len(df.columns) and not pd.isna(df.iloc[idx, col_idx]):
                    record[field_name] = df.iloc[idx, col_idx]
            
            if record.get('Circuit ID'):
                logger.info(f"\nRecord {idx}:")
                for field, value in record.items():
                    logger.info(f"  {field}: {value}")
    
    except Exception as e:
        logger.error(f"Error analyzing Accelecom sheet: {e}")
        raise

if __name__ == "__main__":
    # analyze_excel_file('attached_assets/Appendix D - Circuit IDs.xlsx')
    # analyze_coresite_atlanta()
    # analyze_arelion()
    analyze_accelecom()