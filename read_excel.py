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
            
            # Remove rows where all cells are empty except for formatting
            # (Some Excel files have empty rows with formatting that pandas reads as NaN)
            
            # Convert DataFrame to list of dictionaries
            records = df.to_dict(orient='records')
            
            # Add the records to the all_data dictionary under the sheet name
            all_data[sheet_name] = records
            
            logger.info(f"Added {len(records)} records from sheet {sheet_name}")
        
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