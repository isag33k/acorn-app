#!/usr/bin/env python3
"""
Script to analyze the Uniti sheet structure in the Excel file.
"""
import logging
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_uniti_sheet(excel_path):
    """
    Analyze the Uniti sheet in the Excel file to understand its structure.
    """
    try:
        # Read the Excel file into a pandas ExcelFile object
        excel_file = pd.ExcelFile(excel_path)
        
        sheet_name = 'Uniti'
        logger.info(f"\n===== Processing sheet: {sheet_name} =====")
        
        # Read the sheet into a DataFrame
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # Skip empty sheets
        if df.empty:
            logger.info(f"Sheet {sheet_name} is empty, skipping")
            return
        
        # Print column names and first few values
        logger.info(f"Columns in {sheet_name}:")
        for i, col in enumerate(df.columns):
            col_letter = chr(65 + i) if i < 26 else chr(65 + (i // 26) - 1) + chr(65 + (i % 26))
            logger.info(f"Column {col_letter} ({i}) ({col}):")
            # Print first 3 non-null values for each column
            non_null_values = df[col].dropna().head(3).tolist()
            if non_null_values:
                logger.info(f"  Sample values: {non_null_values}")
            else:
                logger.info("  No non-null values found")
                
        # Get column statistics for mapping
        logger.info(f"\nColumn summary for mapping ({sheet_name}):")
        # Map letter notation to index and human-readable name
        required_columns = {
            'A': (0, 'Market'),  
            'B': (1, 'Provider'),  
            'C': (2, 'Description'),  
            'D': (3, 'Circuit ID'),  
            'E': (4, 'Status'),  
            'K': (10, '24x7 Support Number'),
            'L': (11, 'Maintenance E-mail'),
            'AC': (28, 'A LOC Description'),
            'AD': (29, 'A LOC Address 1'),
            'AF': (31, 'A LOC City'),
            'AG': (32, 'A LOC State'),
            'AK': (36, 'Z LOC Description'),
            'AL': (37, 'Z LOC Address 1'),
            'AM': (38, 'Z LOC Address 2'),
            'AN': (39, 'Z LOC City'),
            'AO': (40, 'Z LOC State')
        }
        
        for letter, (idx, human_name) in required_columns.items():
            col_name = df.columns[idx] if idx < len(df.columns) else f"Out of range ({idx})"
            logger.info(f"Column {letter} (index {idx}): {col_name} => Map to: '{human_name}'")
            if idx < len(df.columns):
                non_null_values = df[df.columns[idx]].dropna().head(3).tolist()
                logger.info(f"  Sample values: {non_null_values}")
    
    except Exception as e:
        logger.error(f"Error analyzing Excel file: {e}")
        raise

if __name__ == "__main__":
    # Process Excel file
    excel_path = 'attached_assets/Appendix D - Circuit IDs.xlsx'
    analyze_uniti_sheet(excel_path)