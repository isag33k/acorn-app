#!/usr/bin/env python3
"""
Specialized script to export only circuit mapping data from the database to a JSON file.
Run this script on your DEV environment to export the circuit data.
This script exports ONLY the circuit data, not the equipment data.
"""

import os
import sys
import json
import logging
import datetime
from app import app, db
from models import CircuitMapping

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def export_circuit_mappings(output_file='dev_circuit_mappings.json'):
    """Export all circuit mapping data to a JSON file"""
    try:
        with app.app_context():
            # Get all circuit mappings
            mapping_list = CircuitMapping.query.all()
            
            # Convert to dictionary format
            mapping_data = []
            for m in mapping_list:
                mapping_data.append({
                    'id': m.id,
                    'circuit_id': m.circuit_id,
                    'equipment_id': m.equipment_id,
                    'command': m.command,
                    'description': m.description,
                    'contact_name': m.contact_name,
                    'contact_email': m.contact_email,
                    'contact_phone': m.contact_phone,
                    'contact_notes': m.contact_notes
                })
                
            # Save to JSON file
            with open(output_file, 'w') as f:
                json.dump(mapping_data, f, indent=4, default=json_serial)
                
            logger.info(f"Exported {len(mapping_data)} circuit mappings to {output_file}")
            
    except Exception as e:
        logger.error(f"Error exporting circuit mapping data: {str(e)}")
        sys.exit(1)
    
    return len(mapping_data)

if __name__ == "__main__":
    logger.info("Starting export of circuit mapping data...")
    
    # Check if output file is specified as argument
    import sys
    output_file = 'dev_circuit_mappings.json'
    
    # Parse command line arguments
    for i in range(1, len(sys.argv)):
        if sys.argv[i].startswith('--output='):
            output_file = sys.argv[i].split('=')[1]
            logger.info(f"Using output file: {output_file}")
    
    count = export_circuit_mappings(output_file)
    logger.info(f"Export completed. {count} circuit mappings exported to {output_file}")