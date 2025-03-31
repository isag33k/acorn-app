#!/usr/bin/env python3
"""
Script to export equipment and circuit mapping data from the database to JSON files.
Run this script in your PRODUCTION environment to export data.
"""

import os
import sys
import json
import logging
import datetime
from app import app, db
from models import Equipment, CircuitMapping

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def export_equipment():
    """Export all equipment data to a JSON file"""
    try:
        with app.app_context():
            # Get all equipment
            equipment_list = Equipment.query.all()
            
            # Convert to dictionary format
            equipment_data = []
            for e in equipment_list:
                equipment_data.append({
                    'id': e.id,
                    'name': e.name,
                    'ip_address': e.ip_address,
                    'ssh_port': e.ssh_port,
                    'username': e.username,
                    'password': e.password,  # Note: This will export the real password
                    'key_filename': e.key_filename
                })
                
            # Save to JSON file
            with open('production_equipment.json', 'w') as f:
                json.dump(equipment_data, f, indent=4, default=json_serial)
                
            logger.info(f"Exported {len(equipment_data)} equipment records to production_equipment.json")
            
    except Exception as e:
        logger.error(f"Error exporting equipment data: {str(e)}")
        sys.exit(1)

def export_circuit_mappings():
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
            with open('production_circuit_mappings.json', 'w') as f:
                json.dump(mapping_data, f, indent=4, default=json_serial)
                
            logger.info(f"Exported {len(mapping_data)} circuit mappings to production_circuit_mappings.json")
            
    except Exception as e:
        logger.error(f"Error exporting circuit mapping data: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting export of production data...")
    export_equipment()
    export_circuit_mappings()
    logger.info("Export completed. Files created: production_equipment.json, production_circuit_mappings.json")
    logger.info("!!! IMPORTANT !!! The equipment JSON file contains real passwords. Secure this file appropriately.")