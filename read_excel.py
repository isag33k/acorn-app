#!/usr/bin/env python3
"""
Script to read Excel file containing circuit data and generate a JSON file
"""
import json
import os
import logging
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_excel_file(excel_path):
    """
    Read the Excel file with circuit IDs and convert each sheet to JSON
    """
    try:
        # Create a data structure to hold all sheets
        all_data = {}
        
        # Read the Excel file into a pandas ExcelFile object
        excel_file = pd.ExcelFile(excel_path)
        
        # Define column mappings for standardization
        column_mapping = {
            'Unnamed: 0': 'Market',
            'Unnamed: 1': 'Provider',
            'Unnamed: 2': 'Description',
            'Unnamed: 3': 'Circuit ID',
            'Unnamed: 4': 'Status',
            'Unnamed: 5': 'Notes',
            'Unnamed: 6': 'Parent CID',
            'Unnamed: 7': 'Access CID',
            'Unnamed: 8': 'Access Provider',
            'Unnamed: 9': 'Bandwidth',
            'Unnamed: 10': 'Account Number',
            'Unnamed: 11': '24x7 Support Number',
            'Unnamed: 12': 'Support E-mail',
            'Unnamed: 13': 'MTU',
            'Unnamed: 14': 'Port',
            'Unnamed: 15': 'VLAN',
            'Unnamed: 16': 'IP Addresses',
            'Unnamed: 17': 'Start Date',
            'Unnamed: 18': 'Term',
            'Unnamed: 19': 'End Date',
            'Unnamed: 20': 'Renewal Notice Date',
            'Unnamed: 21': 'Account Manager',
            'Unnamed: 22': 'Account Manager Phone',
            'Unnamed: 23': 'Account Manager Mobile'
        }
        
        # Special mapping for Arelion with IP address fields
        arelion_mapping = column_mapping.copy()
        arelion_mapping.update({
            'Unnamed: 13': 'Local IPv4',  # Column N
            'Unnamed: 14': 'Remote IPv4', # Column O
            'Unnamed: 15': 'Local IPv6',  # Column P
            'Unnamed: 16': 'Remote IPv6'  # Column Q
        })
        
        # Special mapping for Cogent workbook
        cogent_mapping = column_mapping.copy()
        cogent_mapping.update({
            'Unnamed: 0': 'Market',          # Column A
            'Unnamed: 1': 'Provider',        # Column B
            'Unnamed: 2': 'Description',     # Column C
            'Unnamed: 3': 'Circuit ID',      # Column D
            'Unnamed: 4': 'Status',          # Column E
            'Unnamed: 5': 'Notes',           # Column F
            'Unnamed: 10': 'Account Number', # Column K
            'Unnamed: 11': '24x7 Support Number', # Column L
            'Unnamed: 12': 'Support E-mail', # Column M
            'Unnamed: 13': 'Local IPv4',     # Column N
            'Unnamed: 14': 'Remote IPv4',    # Column O
            'Unnamed: 15': 'Local IPv6',     # Column P
            'Unnamed: 16': 'Remote IPv6'     # Column Q
        })
        
        # Special mapping for CoreSite - Atlanta with comprehensive information
        coresite_mapping = column_mapping.copy()
        coresite_mapping.update({
            'Unnamed: 0': 'Cross Connect Description',  # Column A
            'Unnamed: 1': 'CoreSite XCON ID',           # Column B
            'Unnamed: 2': 'CoreSite Case Number',       # Column C
            'Unnamed: 3': 'Service Number',             # Column D
            'Unnamed: 4': 'Provider',                   # Column E
            'Unnamed: 5': 'Circuit ID',                 # Column F
            'Unnamed: 7': 'Cabinet Number A',           # Column H
            'Unnamed: 8': 'Demarc A',                   # Column I
            'Unnamed: 9': 'Patch Panel Port A',         # Column J
            'Unnamed: 11': 'Space ID Z',                # Column L
            'Unnamed: 12': 'Cabinet Number Z',          # Column M
            'Unnamed: 13': 'Demarc Z',                  # Column N
            'Unnamed: 15': 'Patch Panel Port Z'         # Column P
        })
        
        # Special mapping for Uniti workbook with location fields
        uniti_mapping = column_mapping.copy()
        uniti_mapping.update({
            'Unnamed: 0': 'Market',              # Column A
            'Unnamed: 1': 'Provider',            # Column B
            'Unnamed: 2': 'Description',         # Column C
            'Unnamed: 3': 'Circuit ID',          # Column D
            'Unnamed: 4': 'Status',              # Column E
            'Unnamed: 10': '24x7 Support Number', # Column K
            'Unnamed: 11': 'Maintenance E-mail', # Column L
            'Unnamed: 28': 'A LOC Description',  # Column AC
            'Unnamed: 29': 'A LOC Address 1',    # Column AD
            'Unnamed: 31': 'A LOC City',         # Column AF
            'Unnamed: 32': 'A LOC State',        # Column AG
            'Unnamed: 36': 'Z LOC Description',  # Column AK
            'Unnamed: 37': 'Z LOC Address 1',    # Column AL
            'Unnamed: 38': 'Z LOC Address 2',    # Column AM
            'Unnamed: 39': 'Z LOC City',         # Column AN
            'Unnamed: 40': 'Z LOC State'         # Column AO
        })
        
        # Define valid providers list
        valid_providers = ['Arelion', 'Accelecom', 'Cogent', 'Cologix - Jacksonville', 
                           'CoreSite - Atlanta', 'Lumen', 'Seimitsu', 'Uniti', 
                           'CenturyLink', 'Windstream']
        
        # Process each sheet
        for sheet_name in excel_file.sheet_names:
            # Skip sheets that might be for documentation or other purposes
            if sheet_name in ['Summary', 'Notes', 'Instructions', 'README']:
                logger.info(f"Skipping sheet: {sheet_name}")
                continue
                
            logger.info(f"Processing sheet: {sheet_name}")
            
            # Read the sheet into a DataFrame
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Skip empty sheets
            if df.empty:
                logger.info(f"Sheet {sheet_name} is empty, skipping")
                continue
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Select the appropriate column mapping based on the sheet name
            if sheet_name == 'CoreSite - Atlanta':
                logger.info(f"Using special mapping for CoreSite - Atlanta")
                # Use the special mapping for CoreSite - Atlanta
                df = df.rename(columns=coresite_mapping)
            elif sheet_name == 'Arelion':
                logger.info(f"Using special mapping for Arelion with IP address fields")
                # Use the special mapping for Arelion with IP address fields
                df = df.rename(columns=arelion_mapping)
            elif sheet_name == 'Cogent':
                logger.info(f"Using special mapping for Cogent with IP address fields")
                # Use the special mapping for Cogent with IP address fields
                df = df.rename(columns=cogent_mapping)
            elif sheet_name == 'Uniti':
                logger.info(f"Using special mapping for Uniti with location fields")
                # Use the special mapping for Uniti with location fields
                df = df.rename(columns=uniti_mapping)
            else:
                # Use the standard mapping for other sheets
                df = df.rename(columns=column_mapping)
            
            # Set the provider name for all records in this sheet if not already present
            if 'Provider' in df.columns:
                # Update provider if it's not in the valid list
                for index, provider in enumerate(df['Provider']):
                    if provider is None or pd.isna(provider) or provider not in valid_providers:
                        df.loc[index, 'Provider'] = sheet_name
            else:
                df['Provider'] = sheet_name
            
            # Convert DataFrame to list of dictionaries
            records = df.to_dict(orient='records')
            
            # Clean up records (remove NaN values and standardize circuit IDs)
            clean_records = []
            for record in records:
                # Replace NaN values with None for clean JSON
                for key, value in list(record.items()):
                    if pd.isna(value):
                        record[key] = None
                    elif key in ['Circuit ID', 'Service Number'] and value is not None:
                        # Ensure circuit ID and service number are strings
                        record[key] = str(value)
                
                # Special handling for different sheet types
                if sheet_name == 'CoreSite - Atlanta':
                    # Determine if this is a valid record or should be skipped
                    should_skip = False
                    
                    # Comprehensive list of header rows, metadata, and non-circuit rows to skip
                    header_patterns = [
                        'Data Center', 'Center Description', 'Cage ID', 'Cabinet Number', 
                        'Patch Panel', 'Circuit ID', 'CoreSite Circuit ID', 'Cross Connect Description',
                        'Space ID', 'Demarc Location', 'Welcome Letter', 'Main Support',
                        'N/A. All operations', 'Account Rep', 'Notes'
                    ]
                    
                    # Skip header and metadata rows
                    for pattern in header_patterns:
                        for field in ['Cross Connect Description', 'Service Number', 'Provider', 'Circuit ID']:
                            value = record.get(field)
                            if value and isinstance(value, str) and pattern in value:
                                should_skip = True
                                break
                        if should_skip:
                            break
                    
                    # Skip rows where the Circuit ID or Provider are missing or header-like values
                    if not should_skip and (not record.get('Circuit ID') or record.get('Circuit ID') in ['Circuit ID', None]):
                        should_skip = True
                    
                    if not should_skip and (not record.get('Provider') or record.get('Provider') in ['Provider', None]):
                        should_skip = True
                    
                    # Only process valid records
                    if not should_skip:
                        # If the Circuit ID is empty but Notes has a value (old mapping), use Notes as Circuit ID
                        if (not record.get('Circuit ID') or pd.isna(record.get('Circuit ID'))) and record.get('Notes'):
                            record['Circuit ID'] = record['Notes']
                            
                        # Ensure we have XCON ID and Service Number as strings
                        for key in ['CoreSite XCON ID', 'Service Number']:
                            if record.get(key) is not None and not pd.isna(record.get(key)):
                                record[key] = str(record.get(key))
                        
                        # Add this record to the clean_records list
                        clean_records.append(record)
                
                # Special handling for Cologix - Jacksonville
                elif sheet_name == 'Cologix - Jacksonville':
                    # Use Provider (Column B) as the Circuit ID
                    if record.get('Provider') is not None:
                        record['Circuit ID'] = record.get('Provider')
                    
                    # Set status based on End Date column (column S)
                    if record.get('End Date') is not None and record.get('End Date') != "":
                        record['Status'] = 'INACTIVE'
                    else:
                        record['Status'] = 'ACTIVE'
                    
                    # Add this record to the clean_records list
                    clean_records.append(record)
                
                # Add all other records by default
                else:
                    clean_records.append(record)
            
            # Add the clean records to the all_data dictionary under the sheet name
            all_data[sheet_name] = clean_records
            logger.info(f"Added {len(clean_records)} records from sheet {sheet_name} (filtered from {len(records)} original records)")
        
        return all_data
    
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        raise
        
def json_serial(obj):
    """
    Custom JSON serializer for objects not serializable by default json code
    """
    if isinstance(obj, pd.Timestamp) or hasattr(obj, 'isoformat'):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def save_json(data, output_path):
    """
    Save data to a JSON file
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=json_serial)
        logger.info(f"Data saved to {output_path}")
    except Exception as e:
        logger.error(f"Error saving JSON file: {e}")
        raise

def main():
    """
    Main function to process Excel file and save as JSON
    """
    # Input and output paths
    excel_path = 'attached_assets/Appendix D - Circuit IDs.xlsx'
    output_path = 'circuit_ids_data.json'
    
    # Check if the Excel file exists
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found: {excel_path}")
        return
    
    # Read the Excel file
    logger.info(f"Reading Excel file: {excel_path}")
    data = read_excel_file(excel_path)
    
    # Save the data to a JSON file
    logger.info(f"Saving data to JSON file: {output_path}")
    save_json(data, output_path)
    
    logger.info("Circuit ID data processing complete")

if __name__ == "__main__":
    main()