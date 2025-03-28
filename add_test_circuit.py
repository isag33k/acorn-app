#!/usr/bin/env python3
"""
Script to add a test circuit mapping to the database for testing.
This is a one-time script.
"""

from app import app, db
from models import Equipment, CircuitMapping

def add_test_circuit():
    """Add test circuit mapping to the database"""
    with app.app_context():
        # Find the mock server equipment
        equipment = Equipment.query.filter_by(name="ACORN Test Router").first()
        if not equipment:
            print("Error: Mock SSH server not found in database. Please run add_mock_ssh_server.py first.")
            return
        
        # Check if a test circuit already exists
        existing = CircuitMapping.query.filter_by(circuit_id="TEST-001").first()
        if existing:
            print("Test circuit mapping already exists in database.")
            return
        
        # Create a test circuit mapping for the mock server
        test_circuit = CircuitMapping(
            circuit_id="TEST-001",
            equipment_id=equipment.id,
            command="show circuit id TEST-001",
            description="Test Circuit for ACORN Demo",
            contact_name="John Demo",
            contact_email="john.demo@example.com",
            contact_phone="555-123-4567"
        )
        
        db.session.add(test_circuit)
        
        # Add another test circuit
        test_circuit2 = CircuitMapping(
            circuit_id="TEST-002",
            equipment_id=equipment.id,
            command="show service TEST-002",
            description="Another Test Circuit for ACORN Demo",
            contact_name="Jane Test",
            contact_email="jane.test@example.com",
            contact_phone="555-987-6543"
        )
        
        db.session.add(test_circuit2)
        
        # Add a multi-command test
        test_circuit3 = CircuitMapping(
            circuit_id="TEST-MULTI",
            equipment_id=equipment.id,
            command="show version; show interface ge-0/0/0",
            description="Multi-command Test Circuit",
            contact_name="Alex Multi",
            contact_email="alex.multi@example.com",
            contact_phone="555-555-5555"
        )
        
        db.session.add(test_circuit3)
        
        db.session.commit()
        
        print(f"Added test circuits to database with IDs: {test_circuit.id}, {test_circuit2.id}, {test_circuit3.id}")
        
if __name__ == "__main__":
    add_test_circuit()