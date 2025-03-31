#!/usr/bin/env python3
"""
Script to add test circuit mappings to the equipment in the database.
This script adds sample circuit mappings for testing purposes.
"""

import logging
from app import app, db
from models import Equipment, CircuitMapping

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_test_circuit_mappings():
    """Add test circuit mappings to the database"""
    try:
        with app.app_context():
            # Get all equipment
            equipment_list = Equipment.query.all()
            
            if not equipment_list:
                logger.error("No equipment found in the database. Add equipment first.")
                return
                
            logger.info(f"Found {len(equipment_list)} equipment records")
            
            # Check for existing circuit mappings
            existing_count = CircuitMapping.query.count()
            if existing_count > 0:
                logger.warning(f"Database already has {existing_count} circuit mappings")
                response = input("Do you want to add more test mappings anyway? (y/n): ")
                if response.lower() != 'y':
                    logger.info("Operation cancelled by user")
                    return
            
            # Add circuit mappings for each equipment
            total_added = 0
            
            for equipment in equipment_list:
                # Create three test circuit mappings for each equipment
                circuit_prefix = f"TEST-{equipment.name[:3].upper()}"
                
                for i in range(1, 4):
                    circuit_id = f"{circuit_prefix}-{i:03d}"
                    
                    # Skip if this circuit ID already exists
                    if CircuitMapping.query.filter_by(circuit_id=circuit_id).first():
                        logger.warning(f"Circuit ID {circuit_id} already exists, skipping")
                        continue
                    
                    # Create command based on equipment
                    if "OLT" in equipment.name:
                        command = f"show pon interface gpon 1/{i}\nshow pon ont status gpon 1/{i}"
                    elif "Router" in equipment.name or "router" in equipment.name:
                        command = f"show interface description | include {circuit_id}\nshow ip interface brief"
                    elif "Switch" in equipment.name or "switch" in equipment.name:
                        command = f"show interface status | include {i:02d}\nshow vlan id {1000 + i}"
                    else:
                        command = f"show version\nshow system status\nshow circuit {circuit_id}"
                    
                    # Create the circuit mapping
                    new_mapping = CircuitMapping(
                        circuit_id=circuit_id,
                        equipment_id=equipment.id,
                        command=command,
                        description=f"Test circuit mapping for {equipment.name}",
                        contact_name="Test Contact",
                        contact_email="test@example.com",
                        contact_phone="555-123-4567",
                        contact_notes="This is a test circuit mapping added by the script."
                    )
                    
                    db.session.add(new_mapping)
                    total_added += 1
            
            # Commit changes
            db.session.commit()
            logger.info(f"Added {total_added} test circuit mappings")
            
    except Exception as e:
        logger.error(f"Error adding test circuit mappings: {str(e)}")
        db.session.rollback()
        raise

if __name__ == "__main__":
    logger.info("Starting test circuit mapping creation...")
    add_test_circuit_mappings()
    logger.info("Done.")