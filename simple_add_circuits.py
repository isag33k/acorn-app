#!/usr/bin/env python3
"""
Simple script to add test circuit mappings to the equipment in the database.
"""

from app import app, db
from models import Equipment, CircuitMapping

with app.app_context():
    # Get all equipment
    equipment_list = Equipment.query.all()
    
    if not equipment_list:
        print("No equipment found in the database. Add equipment first.")
    else:
        print(f"Found {len(equipment_list)} equipment records")
        
        # Add circuit mappings for each equipment
        total_added = 0
        
        for equipment in equipment_list:
            # Create test circuit mapping for this equipment
            circuit_id = f"TEST-{equipment.name[:3].upper()}-001"
            
            # Skip if this circuit ID already exists
            if CircuitMapping.query.filter_by(circuit_id=circuit_id).first():
                print(f"Circuit ID {circuit_id} already exists, skipping")
                continue
            
            # Create command based on equipment
            if "OLT" in equipment.name:
                command = "show pon interface gpon 1/1\nshow pon ont status gpon 1/1"
            elif "Router" in equipment.name or "router" in equipment.name:
                command = f"show interface description | include {circuit_id}\nshow ip interface brief"
            elif "Switch" in equipment.name or "switch" in equipment.name:
                command = "show interface status | include 01\nshow vlan id 1001"
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
                contact_notes="This is a test circuit mapping."
            )
            
            db.session.add(new_mapping)
            total_added += 1
        
        # Commit changes
        db.session.commit()
        print(f"Added {total_added} test circuit mappings")