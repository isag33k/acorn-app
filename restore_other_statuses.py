#!/usr/bin/env python3
"""
Script to restore the original status values for all providers except Cologix - Jacksonville.
This will undo any inadvertent status changes made to other providers by regenerating the data
from the Excel file with the correct mapping.
"""
import json
import os
import logging
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def json_serial(obj):
    """
    Custom JSON serializer for objects not serializable by default json code
    """
    if isinstance(obj, pd.Timestamp) or hasattr(obj, 'isoformat'):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def read_excel_for_restoration(excel_path):
    """
    Read the Excel file with circuit IDs and convert each sheet to JSON,
    applying special status handling ONLY for Cologix - Jacksonville
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
        
        # Special mapping for CoreSite - Atlanta where Circuit ID is in column F (Notes)
        coresite_mapping = column_mapping.copy()
        coresite_mapping.update({
            'Unnamed: 3': 'Service Number',  # What was labeled as Circuit ID is actually Service Number
            'Unnamed: 5': 'Circuit ID'       # The real Circuit ID is in the Notes column (F)
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
            for record in records:
                # Replace NaN values with None for clean JSON
                for key, value in list(record.items()):
                    if pd.isna(value):
                        record[key] = None
                    elif key in ['Circuit ID', 'Service Number'] and value is not None:
                        # Ensure circuit ID and service number are strings
                        record[key] = str(value)
                        
                # For CoreSite records, ensure the Circuit ID is set correctly
                if sheet_name == 'CoreSite - Atlanta':
                    # For CoreSite, we know Column F (Unnamed: 5) contains the Circuit ID values
                    # and Column D (Unnamed: 3) contains the Service Numbers
                    # We need to find the original index of this record to access the raw data
                    row_idx = records.index(record)
                    
                    # Set Circuit ID from Column F if it exists
                    if row_idx < len(df) and 'Unnamed: 5' in df.columns:
                        circuit_id_value = df.iloc[row_idx]['Unnamed: 5']
                        if not pd.isna(circuit_id_value) and str(circuit_id_value) != 'Circuit ID':
                            record['Circuit ID'] = str(circuit_id_value)
                    
                    # Store Service Number from Column D if it exists
                    if row_idx < len(df) and 'Unnamed: 3' in df.columns:
                        service_number_value = df.iloc[row_idx]['Unnamed: 3']
                        if not pd.isna(service_number_value) and str(service_number_value).startswith('SVC-'):
                            record['Service Number'] = str(service_number_value)
                
                # Special handling for Cologix - Jacksonville ONLY
                if sheet_name == 'Cologix - Jacksonville':
                    # Use Provider (Column B) as the Circuit ID
                    if record.get('Provider') is not None:
                        record['Circuit ID'] = record.get('Provider')
                    
                    # Set status based on End Date column (column S)
                    if record.get('End Date') is not None and record.get('End Date') != "":
                        record['Status'] = 'INACTIVE'
                    else:
                        record['Status'] = 'ACTIVE'
            
            # Add the records to the all_data dictionary under the sheet name
            all_data[sheet_name] = records
            
            logger.info(f"Added {len(records)} records from sheet {sheet_name}")
        
        return all_data
    
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        raise

def restore_other_statuses():
    """
    Regenerate the JSON data with proper status handling for all providers
    """
    # Input and output paths
    excel_path = 'attached_assets/Appendix D - Circuit IDs.xlsx'
    json_file = 'circuit_ids_data.json'
    
    # Check if the Excel file exists
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found: {excel_path}")
        return
    
    try:
        # Read the Excel file with correct Cologix - Jacksonville handling
        logger.info(f"Reading Excel file: {excel_path}")
        data = read_excel_for_restoration(excel_path)
        
        # Save the data to the JSON file
        logger.info(f"Saving data to JSON file: {json_file}")
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2, default=json_serial)
        
        logger.info("Circuit ID data restoration complete")
        
    except Exception as e:
        logger.error(f"Error restoring data: {e}")
        raise

if __name__ == "__main__":
    restore_other_statuses()