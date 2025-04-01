#!/usr/bin/env python3
"""
Very simple script to export equipment and circuit mapping data to JSON files.
"""

import json
import datetime
from app import app, db
from models import Equipment, CircuitMapping

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# Main export script
with app.app_context():
    print("Starting export of production data...")
    
    # Export equipment
    equipment_list = Equipment.query.all()
    equipment_data = []
    for e in equipment_list:
        equipment_data.append({
            'id': e.id,
            'name': e.name,
            'ip_address': e.ip_address,
            'ssh_port': e.ssh_port,
            'username': e.username,
            'password': e.password,
            'key_filename': e.key_filename
        })
    
    with open('production_equipment.json', 'w') as f:
        json.dump(equipment_data, f, indent=4, default=json_serial)
    
    print(f"Exported {len(equipment_data)} equipment records to production_equipment.json")
    
    # Export circuit mappings
    mapping_list = CircuitMapping.query.all()
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
    
    with open('production_circuit_mappings.json', 'w') as f:
        json.dump(mapping_data, f, indent=4, default=json_serial)
    
    print(f"Exported {len(mapping_data)} circuit mappings to production_circuit_mappings.json")
    
    print("Export completed successfully.")
    print("!!! IMPORTANT !!! The equipment JSON file contains real passwords. Secure this file appropriately.")