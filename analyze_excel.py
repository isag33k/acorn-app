#!/usr/bin/env python3
"""
Script to analyze the Excel file structure and identify the columns for each sheet.
"""
import pandas as pd
import logging

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
    Focus specifically on CoreSite - Atlanta data to identify the Circuit ID column.
    """
    try:
        excel_path = 'attached_assets/Appendix D - Circuit IDs.xlsx'
        logger.info(f"Reading CoreSite - Atlanta sheet from {excel_path}")
        
        # Read the specific sheet
        df = pd.read_excel(excel_path, sheet_name='CoreSite - Atlanta')
        
        # Print info about column D (Unnamed: 3, expected to be Service Number)
        logger.info("\nColumn D (Unnamed:.3, expected to be Service Number):")
        if 'Unnamed: 3' in df.columns:
            values = df['Unnamed: 3'].dropna().head(10).tolist()
            logger.info(f"Values: {values}")
        else:
            logger.info("Column not found")
            
        # Print info about column F (Unnamed: 5, expected to be Circuit ID)
        logger.info("\nColumn F (Unnamed: 5, expected to be true Circuit ID):")
        if 'Unnamed: 5' in df.columns:
            values = df['Unnamed: 5'].dropna().head(10).tolist()
            logger.info(f"Values: {values}")
        else:
            logger.info("Column not found")
            
        # Look at first few rows to understand the structure
        logger.info("\nFirst few rows of CoreSite - Atlanta:")
        for idx, row in df.head(5).iterrows():
            logger.info(f"Row {idx}:")
            for col, val in row.items():
                if not pd.isna(val):
                    logger.info(f"  {col}: {val}")
    
    except Exception as e:
        logger.error(f"Error analyzing CoreSite - Atlanta: {e}")
        raise

if __name__ == "__main__":
    # analyze_excel_file('attached_assets/Appendix D - Circuit IDs.xlsx')
    analyze_coresite_atlanta()