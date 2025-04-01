#!/usr/bin/env python3
"""
Specialized script to import only circuit mapping data from a JSON file into the database.
Run this script on your PRODUCTION environment after copying the JSON file from development.
This script imports ONLY the circuit data, not the equipment data.
"""

import os
import sys
import json
import logging
from app import app, db
from models import CircuitMapping, Equipment

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_circuit_mappings(json_file='dev_circuit_mappings.json', replace_existing=True):
    """
    Import circuit mapping data from a JSON file
    
    Args:
        json_file: Path to the JSON file with circuit mappings
        replace_existing: If True, delete existing circuit mappings first
    """
    try:
        with app.app_context():
            # Check if file exists
            if not os.path.exists(json_file):
                logger.error(f"File not found: {json_file}")
                logger.error("Run circuit_export.py on your development server first")
                return 0
                
            # Load JSON data
            with open(json_file, 'r') as f:
                mapping_data = json.load(f)
                
            logger.info(f"Loaded {len(mapping_data)} circuit mappings from {json_file}")
            
            # Get existing equipment IDs to validate references
            existing_equipment_ids = {e.id for e in Equipment.query.all()}
            
            # Verify that all equipment references exist
            equipment_errors = 0
            for m in mapping_data:
                if m['equipment_id'] not in existing_equipment_ids:
                    logger.warning(f"Equipment ID {m['equipment_id']} referenced by circuit ID {m['circuit_id']} does not exist")
                    equipment_errors += 1
            
            if equipment_errors > 0:
                logger.error(f"Found {equipment_errors} equipment references that don't exist in the database")
                logger.error("You need to import equipment data first using import_production_data.py")
                user_input = input("Continue anyway? (y/n): ")
                if user_input.lower() != 'y':
                    logger.info("Import aborted")
                    return 0
            
            # If replacing existing, delete all current circuit mappings
            if replace_existing:
                # Get count of existing mappings
                existing_count = CircuitMapping.query.count()
                logger.info(f"Deleting {existing_count} existing circuit mappings")
                
                # Delete all current mappings
                CircuitMapping.query.delete()
                db.session.commit()
                logger.info("All existing circuit mappings deleted")
            
            # Import circuit mappings
            imported_count = 0
            skipped_count = 0
            error_count = 0
            
            for m in mapping_data:
                # Get the ID from the data
                mapping_id = m.get('id')
                
                # Skip if referenced equipment doesn't exist (but continue with others)
                if m['equipment_id'] not in existing_equipment_ids:
                    logger.warning(f"Skipping circuit {m['circuit_id']} (ID: {mapping_id}): Equipment ID {m['equipment_id']} not found")
                    skipped_count += 1
                    continue
                
                try:
                    # Create new circuit mapping
                    new_mapping = CircuitMapping(
                        id=mapping_id,
                        circuit_id=m['circuit_id'],
                        equipment_id=m['equipment_id'],
                        command=m['command'],
                        description=m.get('description'),
                        contact_name=m.get('contact_name'),
                        contact_email=m.get('contact_email'),
                        contact_phone=m.get('contact_phone'),
                        contact_notes=m.get('contact_notes')
                    )
                    
                    db.session.add(new_mapping)
                    imported_count += 1
                    
                    # Commit every 100 records to avoid large transactions
                    if imported_count % 100 == 0:
                        db.session.commit()
                        logger.info(f"Imported {imported_count} circuit mappings so far...")
                
                except Exception as e:
                    logger.error(f"Error importing circuit {m['circuit_id']} (ID: {mapping_id}): {str(e)}")
                    error_count += 1
                    continue
            
            # Final commit
            db.session.commit()
            logger.info(f"Successfully imported {imported_count} circuit mappings")
            if skipped_count > 0:
                logger.info(f"Skipped {skipped_count} circuit mappings due to missing equipment references")
            if error_count > 0:
                logger.warning(f"Encountered {error_count} errors during import")
            
            return imported_count
            
    except Exception as e:
        logger.error(f"Error during circuit mapping import: {str(e)}")
        db.session.rollback()
        return 0

if __name__ == "__main__":
    logger.info("Starting import of circuit mapping data...")
    
    # Check if the file path is provided as a command-line argument
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        logger.info(f"Using JSON file: {json_file}")
    else:
        json_file = 'dev_circuit_mappings.json'
        logger.info(f"Using default JSON file: {json_file}")
    
    # Ask user for confirmation about replacement behavior
    print("\nImport Options:")
    print("1. Replace ALL existing circuit mappings with the imported data")
    print("2. Keep existing circuit mappings and add new ones")
    
    choice = input("\nSelect option (1 or 2): ").strip()
    replace_existing = (choice == '1')
    
    if replace_existing:
        logger.info("Will REPLACE all existing circuit mappings with imported data")
    else:
        logger.info("Will KEEP existing circuit mappings and add new ones from import")
    
    # Final confirmation
    confirm = input("\nReady to proceed with import? (y/n): ").strip().lower()
    if confirm != 'y':
        logger.info("Import cancelled")
        sys.exit(0)
    
    # Perform the import
    count = import_circuit_mappings(json_file, replace_existing)
    
    if count > 0:
        logger.info(f"Import completed successfully. {count} circuit mappings imported.")
    else:
        logger.error("Import failed or no records were imported.")