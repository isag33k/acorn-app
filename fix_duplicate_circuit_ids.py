#!/usr/bin/env python3
"""
Script to fix duplicate Circuit IDs in the CoreSite - Atlanta data
"""
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_duplicate_circuit_ids(json_path, output_path=None):
    """
    Remove duplicate Circuit IDs from provider data in the JSON file
    and remove header rows incorrectly imported from Excel.
    """
    try:
        # Load the JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        # Process both CoreSite and Cologix data
        providers_to_fix = {
            'CoreSite - Atlanta': 'CoreSite Circuit IDs',
            'Cologix - Jacksonville': 'Cologix Circuit IDs'
        }
        
        for provider, description in providers_to_fix.items():
            # Check if provider is in the data
            if provider not in data:
                logger.error(f"{provider} not found in the data")
                continue
                
            # Get the original provider data
            original_data = data[provider]
            logger.info(f"Original {provider} records: {len(original_data)}")
            
            # First remove any header rows (rows with Circuit ID = "Circuit ID")
            filtered_data = [record for record in original_data if record.get('Circuit ID') != 'Circuit ID']
            logger.info(f"{provider} - After removing header rows: {len(filtered_data)}")
            
            # For Cologix - Jacksonville, we also need to fix the Circuit ID field
            if provider == 'Cologix - Jacksonville':
                # Update Circuit IDs to ensure they're unique
                # The current issue is that Cologix records are using the provider name as Circuit ID
                for i, record in enumerate(filtered_data):
                    # If Circuit ID is the same as Provider, generate a new one based on row data
                    if record.get('Circuit ID') == provider:
                        # Try to use a meaningful identifier from the data
                        # For Cologix, let's use Market + Row Number if available
                        market = record.get('Market') or 'Unknown'
                        new_cid = f"CLX-{market}-{i+1}"
                        record['Circuit ID'] = new_cid
                        logger.info(f"Assigned new Circuit ID for Cologix record {i}: {new_cid}")
            
            # Create a dictionary to keep track of seen circuit IDs and their records
            seen_cids = {}
            unique_data = []
            
            for record in filtered_data:
                cid = record.get('Circuit ID')
                if not cid:
                    # Skip records without a Circuit ID
                    continue
                    
                # If we haven't seen this Circuit ID before, keep the record
                if cid not in seen_cids:
                    seen_cids[cid] = record
                    unique_data.append(record)
            
            logger.info(f"{provider} - After removing duplicates: {len(unique_data)}")
            
            # Update the data with the unique records
            data[provider] = unique_data
        
        # Save the updated data
        output_path = output_path or json_path
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Updated data saved to {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing duplicate Circuit IDs: {e}")
        return False

def check_duplicate_stats(json_path):
    """
    Check the duplicate statistics for all providers in the JSON file
    """
    try:
        # Load the JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Only check stats for key providers of interest
        key_providers = ['CoreSite - Atlanta', 'Cologix - Jacksonville']
        
        for provider, circuits in data.items():
            # Skip non-key providers
            if provider not in key_providers:
                continue
                
            # Find duplicates
            unique_cids = set()
            duplicate_cids = set()
            header_rows = []
            
            for i, record in enumerate(circuits):
                cid = record.get('Circuit ID')
                
                # Check for header rows
                if cid == 'Circuit ID':
                    header_rows.append(i)
                    continue
                    
                if cid and cid in unique_cids:
                    duplicate_cids.add(cid)
                elif cid:
                    unique_cids.add(cid)
            
            logger.info(f"{provider}:")
            logger.info(f"  Total records: {len(circuits)}")
            logger.info(f"  Unique Circuit IDs: {len(unique_cids)}")
            logger.info(f"  Duplicate Circuit IDs: {len(duplicate_cids)}")
            logger.info(f"  Header rows: {len(header_rows)}")
            if header_rows:
                logger.info(f"  Header row indices: {header_rows}")
            if duplicate_cids:
                logger.info(f"  Example duplicates: {list(duplicate_cids)[:3]}")
    
    except Exception as e:
        logger.error(f"Error checking duplicates: {e}")

if __name__ == "__main__":
    json_path = 'circuit_ids_data.json'
    
    # First check the statistics before fixing
    logger.info("Before fixing:")
    check_duplicate_stats(json_path)
    
    # Fix the duplicates
    if fix_duplicate_circuit_ids(json_path):
        # Check the statistics after fixing
        logger.info("\nAfter fixing:")
        check_duplicate_stats(json_path)
    else:
        logger.error("Failed to fix duplicate Circuit IDs")