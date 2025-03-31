#!/usr/bin/env python3
"""
Script to add a sample OLT circuit to the database.
This is useful for testing the SSH connection to the mock SSH server.
"""

from app import app, db
from models import Equipment, CircuitMapping

with app.app_context():
    # Check if we already have the SHA1-FL-OLT-1 equipment
    olt = Equipment.query.filter_by(name="SHA1-FL-OLT-1").first()
    
    if not olt:
        # Create the OLT equipment
        print("Creating SHA1-FL-OLT-1 equipment...")
        olt = Equipment(
            name="SHA1-FL-OLT-1",
            ip_address="127.0.0.1",  # Local address for testing
            ssh_port=2222,           # Port of the mock SSH server
            username="admin",
            password="admin123"
        )
        db.session.add(olt)
        db.session.commit()
        print(f"Created OLT equipment with ID {olt.id}")
    
    # Check if the test circuit already exists
    circuit_id = "FLT-PON-001"
    existing = CircuitMapping.query.filter_by(circuit_id=circuit_id).first()
    
    if existing:
        print(f"Circuit {circuit_id} already exists with ID {existing.id}")
    else:
        # Create a test circuit mapping
        print(f"Creating test circuit {circuit_id}...")
        new_circuit = CircuitMapping(
            circuit_id=circuit_id,
            equipment_id=olt.id,
            command="show pon interface gpon 1/1\nshow pon ont status gpon 1/1",
            description="Test OLT circuit for mock SSH server",
            contact_name="Network Admin",
            contact_email="admin@example.com",
            contact_phone="555-987-6543",
            contact_notes="This is a test circuit for the OLT. It connects to the mock SSH server running locally."
        )
        
        db.session.add(new_circuit)
        db.session.commit()
        print(f"Created test circuit with ID {new_circuit.id}")
    
    print("Done. You can now test the circuit by entering FLT-PON-001 in the Circuit ID field.")