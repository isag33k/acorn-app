#!/usr/bin/env python3
"""
Script to import equipment and circuit mapping data from JSON files into the database.
Run this script in your DEVELOPMENT environment after copying the JSON files from production.
"""

import os
import sys
import json
from app import app, db
from models import Equipment, CircuitMapping

# Main execution - place app context at the outermost level
with app.app_context():
    print("Starting import of production data...")

    def import_equipment(json_file='production_equipment.json'):
        """Import equipment data from a JSON file"""
        try:
            # Check if file exists
            if not os.path.exists(json_file):
                print(f"File not found: {json_file}")
                print("Run simple_export.py on your production server first")
                return
                
            # Load JSON data
            with open(json_file, 'r') as f:
                equipment_data = json.load(f)
                
            print(f"Loaded {len(equipment_data)} equipment records from {json_file}")
            
            # First find and save all existing circuit mappings
            existing_mappings = CircuitMapping.query.filter(CircuitMapping.equipment_id.notin_([5, 6, 7])).all()
            print(f"Found {len(existing_mappings)} circuit mappings with equipment IDs not in protected list")
            
            # Delete those circuit mappings first to avoid foreign key constraints
            for mapping in existing_mappings:
                db.session.delete(mapping)
            db.session.commit()
            print("Deleted circuit mappings with non-protected equipment IDs")
            
            # Now we can safely delete equipment
            # Keep IDs 5, 6, 7 which are likely the original test equipment
            protected_ids = [5, 6, 7]
            equipment_to_delete = Equipment.query.filter(Equipment.id.notin_(protected_ids)).all()
            
            for equipment in equipment_to_delete:
                db.session.delete(equipment)
            db.session.commit()
            print(f"Deleted {len(equipment_to_delete)} equipment records")
            
            # Get existing equipment IDs after deletion
            existing_ids = {e.id for e in Equipment.query.all()}
            
            # Import equipment
            imported_count = 0
            for e in equipment_data:
                # Skip if this ID already exists
                if e['id'] in existing_ids:
                    print(f"Equipment ID {e['id']} already exists, skipping")
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
            print(f"Imported {imported_count} new equipment records")
            
        except Exception as e:
            print(f"Error importing equipment data: {str(e)}")
            db.session.rollback()
            return False
        
        return True

    def import_circuit_mappings(json_file='production_circuit_mappings.json'):
        """Import circuit mapping data from a JSON file"""
        try:
            # Check if file exists
            if not os.path.exists(json_file):
                print(f"File not found: {json_file}")
                print("Run simple_export.py on your production server first")
                return
                
            # Load JSON data
            with open(json_file, 'r') as f:
                mapping_data = json.load(f)
                
            print(f"Loaded {len(mapping_data)} circuit mappings from {json_file}")
            
            # Get existing mapping IDs and equipment IDs
            existing_mapping_ids = {m.id for m in CircuitMapping.query.all()}
            existing_equipment_ids = {e.id for e in Equipment.query.all()}
            
            # Import circuit mappings
            imported_count = 0
            skipped_count = 0
            for m in mapping_data:
                # Skip if this ID already exists
                if m['id'] in existing_mapping_ids:
                    print(f"Circuit mapping ID {m['id']} already exists, skipping")
                    skipped_count += 1
                    continue
                    
                # Skip if referenced equipment doesn't exist
                if m['equipment_id'] not in existing_equipment_ids:
                    print(f"Equipment ID {m['equipment_id']} not found, skipping circuit mapping {m['id']}")
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
            print(f"Imported {imported_count} new circuit mappings")
            if skipped_count > 0:
                print(f"Skipped {skipped_count} circuit mappings")
            
        except Exception as e:
            print(f"Error importing circuit mapping data: {str(e)}")
            db.session.rollback()
            return False
        
        return True

    # Run the import functions
    if import_equipment():
        import_circuit_mappings()
    
    print("Import completed.")