#!/usr/bin/env python3
"""
Script to import equipment and circuit mapping data from JSON files into the database.
Run this script in your DEVELOPMENT environment after copying the JSON files from production.
"""

import os
import sys
import json
import logging
from app import app, db
from models import Equipment, CircuitMapping
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_equipment(json_file='production_equipment.json'):
    """Import equipment data from a JSON file"""
    try:
        # Check if file exists
        if not os.path.exists(json_file):
            logger.error(f"File not found: {json_file}")
            logger.error("Run export_production_data.py on your production server first")
            return
            
        # Load JSON data
        with open(json_file, 'r') as f:
            equipment_data = json.load(f)
            
        logger.info(f"Loaded {len(equipment_data)} equipment records from {json_file}")
        
        with app.app_context():
            # Clear existing equipment (except the original 3)
            db.session.execute(db.delete(Equipment).where(Equipment.id > 7))
            db.session.commit()
            logger.info("Cleared existing equipment data (kept original 3 records)")
            
            # Get existing equipment IDs
            existing_ids = {e.id for e in Equipment.query.all()}
            
            # Import equipment
            imported_count = 0
            for e in equipment_data:
                # Skip if this ID already exists
                if e['id'] in existing_ids:
                    logger.warning(f"Equipment ID {e['id']} already exists, skipping")
                    continue
                    
                # Create new equipment
                new_equipment = Equipment(
                    id=e['id'],
                    name=e['name'],
                    ip_address=e['ip_address'],
                    ssh_port=e['ssh_port'],
                    username=e['username'],
                    password=e['password'],
                    key_filename=e['key_filename'] if 'key_filename' in e else None
                )
                
                db.session.add(new_equipment)
                imported_count += 1
                
            # Commit changes
            db.session.commit()
            logger.info(f"Imported {imported_count} new equipment records")
            
    except SQLAlchemyError as e:
        logger.error(f"Database error importing equipment: {str(e)}")
        db.session.rollback()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error importing equipment data: {str(e)}")
        sys.exit(1)

def import_circuit_mappings(json_file='production_circuit_mappings.json'):
    """Import circuit mapping data from a JSON file"""
    try:
        # Check if file exists
        if not os.path.exists(json_file):
            logger.error(f"File not found: {json_file}")
            logger.error("Run export_production_data.py on your production server first")
            return
            
        # Load JSON data
        with open(json_file, 'r') as f:
            mapping_data = json.load(f)
            
        logger.info(f"Loaded {len(mapping_data)} circuit mappings from {json_file}")
        
        with app.app_context():
            # Clear existing circuit mappings that aren't associated with the original 3 equipment
            original_equipment_ids = [5, 6, 7]
            db.session.execute(db.delete(CircuitMapping).where(
                CircuitMapping.equipment_id.notin_(original_equipment_ids)
            ))
            db.session.commit()
            logger.info("Cleared existing circuit mappings (kept mappings for original equipment)")
            
            # Get existing mapping IDs and equipment IDs
            existing_mapping_ids = {m.id for m in CircuitMapping.query.all()}
            existing_equipment_ids = {e.id for e in Equipment.query.all()}
            
            # Import circuit mappings
            imported_count = 0
            skipped_count = 0
            for m in mapping_data:
                # Skip if this ID already exists
                if m['id'] in existing_mapping_ids:
                    logger.warning(f"Circuit mapping ID {m['id']} already exists, skipping")
                    skipped_count += 1
                    continue
                    
                # Skip if referenced equipment doesn't exist
                if m['equipment_id'] not in existing_equipment_ids:
                    logger.warning(f"Equipment ID {m['equipment_id']} not found, skipping circuit mapping {m['id']}")
                    skipped_count += 1
                    continue
                    
                # Create new circuit mapping
                new_mapping = CircuitMapping(
                    id=m['id'],
                    circuit_id=m['circuit_id'],
                    equipment_id=m['equipment_id'],
                    command=m['command'],
                    description=m['description'] if 'description' in m else None,
                    contact_name=m['contact_name'] if 'contact_name' in m else None,
                    contact_email=m['contact_email'] if 'contact_email' in m else None,
                    contact_phone=m['contact_phone'] if 'contact_phone' in m else None,
                    contact_notes=m['contact_notes'] if 'contact_notes' in m else None
                )
                
                db.session.add(new_mapping)
                imported_count += 1
                
            # Commit changes
            db.session.commit()
            logger.info(f"Imported {imported_count} new circuit mappings")
            if skipped_count > 0:
                logger.warning(f"Skipped {skipped_count} circuit mappings")
            
    except SQLAlchemyError as e:
        logger.error(f"Database error importing circuit mappings: {str(e)}")
        db.session.rollback()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error importing circuit mapping data: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting import of production data...")
    import_equipment()
    import_circuit_mappings()
    logger.info("Import completed.")