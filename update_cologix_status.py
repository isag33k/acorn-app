#!/usr/bin/env python3
"""
Script to update the status of Cologix - Jacksonville circuits in the circuit_ids_data.json file.
The status should be set to INACTIVE if Column S (End Date) has data, and ACTIVE if it's blank.
"""
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_cologix_statuses():
    """
    Update the status of Cologix - Jacksonville circuits in the circuit_ids_data.json file
    """
    # Path to the JSON file
    json_file = 'circuit_ids_data.json'
    
    # Check if the file exists
    if not os.path.exists(json_file):
        logger.error(f"JSON file not found: {json_file}")
        return
    
    try:
        # Load the JSON data
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Check if Cologix - Jacksonville is in the data
        if 'Cologix - Jacksonville' not in data:
            logger.warning("No 'Cologix - Jacksonville' sheet found in the data")
            return
        
        # Get the Cologix - Jacksonville circuits
        cologix_circuits = data['Cologix - Jacksonville']
        
        # Track the changes
        updated_count = 0
        
        # Update each circuit
        for circuit in cologix_circuits:
            # Check if there's data in Column S (End Date)
            end_date = circuit.get('End Date')
            
            # Set the status based on whether End Date has data
            if end_date is not None and end_date != "":
                if circuit.get('Status') != 'INACTIVE':
                    circuit['Status'] = 'INACTIVE'
                    updated_count += 1
            else:
                if circuit.get('Status') != 'ACTIVE':
                    circuit['Status'] = 'ACTIVE'
                    updated_count += 1
        
        # Save the updated data
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Updated {updated_count} Cologix - Jacksonville circuits")
        
    except Exception as e:
        logger.error(f"Error updating Cologix - Jacksonville statuses: {e}")
        raise

if __name__ == "__main__":
    update_cologix_statuses()