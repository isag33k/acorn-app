#!/usr/bin/env python3
"""
Setup script to prepare the test environment for ACORN application.
This script will:
1. Create the mock SSH server in the database (if not exists)
2. Create test circuit mappings for the demo
3. Ensure the SSH test server is running
"""

import os
import sys
import subprocess
import time
from app import app, db
from models import Equipment, CircuitMapping, User
from werkzeug.security import generate_password_hash

def create_mock_ssh_server():
    """Add or verify mock SSH server in the database"""
    with app.app_context():
        # Check if the mock server already exists
        mock_server = Equipment.query.filter_by(name="ACORN Test Router").first()
        
        if mock_server:
            print("✓ Mock SSH server already exists in database with ID:", mock_server.id)
            # Update its credentials to be sure they match what we expect
            mock_server.username = "test"
            mock_server.password = "Ac0rN$"
            mock_server.ssh_port = 2222
            mock_server.ip_address = "127.0.0.1"
            db.session.commit()
            print("✓ Mock SSH server credentials updated")
            return mock_server
        
        # Create a new equipment entry for our mock SSH server
        mock_server = Equipment(
            name="ACORN Test Router",
            ip_address="127.0.0.1",  # Use localhost
            ssh_port=2222,           # The port our mock server runs on
            username="test",         # Default username
            password="Ac0rN$",       # Default password
        )
        
        db.session.add(mock_server)
        db.session.commit()
        
        print(f"✓ Added mock SSH server to database with ID: {mock_server.id}")
        return mock_server

def create_test_circuits(mock_server):
    """Create test circuit mappings for demo purposes"""
    with app.app_context():
        # Check for existing test circuits
        test_count = CircuitMapping.query.filter(
            CircuitMapping.circuit_id.in_(["TEST-001", "TEST-002", "TEST-MULTI"])
        ).count()
        
        if test_count == 3:
            print("✓ All test circuits already exist in database")
            return
            
        # Delete any existing test circuits to avoid duplicates
        CircuitMapping.query.filter(
            CircuitMapping.circuit_id.in_(["TEST-001", "TEST-002", "TEST-MULTI"])
        ).delete()
        
        # Create test circuits from scratch
        test_circuits = [
            CircuitMapping(
                circuit_id="TEST-001",
                equipment_id=mock_server.id,
                command="show circuit id TEST-001",
                description="Test Circuit for ACORN Demo",
                contact_name="John Demo",
                contact_email="john.demo@example.com",
                contact_phone="555-123-4567"
            ),
            CircuitMapping(
                circuit_id="TEST-002",
                equipment_id=mock_server.id,
                command="show service TEST-002",
                description="Another Test Circuit for ACORN Demo",
                contact_name="Jane Test",
                contact_email="jane.test@example.com",
                contact_phone="555-987-6543"
            ),
            CircuitMapping(
                circuit_id="TEST-MULTI",
                equipment_id=mock_server.id,
                command="show version; show interface ge-0/0/0",
                description="Multi-command Test Circuit",
                contact_name="Alex Multi",
                contact_email="alex.multi@example.com",
                contact_phone="555-555-5555"
            )
        ]
        
        for circuit in test_circuits:
            db.session.add(circuit)
            
        db.session.commit()
        print(f"✓ Added {len(test_circuits)} test circuits to database")

def ensure_admin_user():
    """Make sure the admin user exists in the database"""
    with app.app_context():
        admin = User.query.filter_by(username="admin").first()
        
        if admin:
            print("✓ Admin user already exists")
            return
            
        # Create admin user
        admin = User(
            username="admin",
            email="admin@acorn.test",
            password_hash=generate_password_hash("Welcome1@123"),
            is_admin=True,
            first_name="Admin",
            last_name="User"
        )
        
        db.session.add(admin)
        db.session.commit()
        print("✓ Created admin user (username: admin, password: Welcome1@123)")

def check_ssh_server_running():
    """Check if the mock SSH server is running"""
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 2222))
        if result == 0:
            print("✓ SSH server is running on port 2222")
            return True
        else:
            print("✗ SSH server is not running on port 2222")
            return False
    except Exception as e:
        print(f"✗ Error checking SSH server: {str(e)}")
        return False
    finally:
        sock.close()

def verify_ssh_connection():
    """Verify that we can connect to the SSH server"""
    import paramiko
    
    print("\nTesting SSH connection to mock server:")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("Connecting to 127.0.0.1:2222 as test/Ac0rN$...")
        client.connect(
            hostname="127.0.0.1",
            port=2222,
            username="test",
            password="Ac0rN$",
            timeout=5,
            allow_agent=False,
            look_for_keys=False
        )
        print("✓ SSH connection successful!")
        
        # Test a simple command
        print("Testing command execution...")
        stdin, stdout, stderr = client.exec_command('show version')
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if error:
            print(f"✗ Command execution failed: {error}")
        else:
            print("✓ Command execution successful!")
            print("Output sample:", output.split("\n")[0])
        
        client.close()
        return True
    except Exception as e:
        print(f"✗ SSH connection failed: {str(e)}")
        return False

def main():
    """Run the complete setup process"""
    print("======= ACORN Test Environment Setup =======")
    
    # Step 1: Create the mock SSH server in the database
    mock_server = create_mock_ssh_server()
    
    # Step 2: Create test circuit mappings
    create_test_circuits(mock_server)
    
    # Step 3: Ensure admin user exists
    ensure_admin_user()
    
    # Step 4: Check if the mock SSH server is running
    ssh_running = check_ssh_server_running()
    
    # Step 5: If the server is running, verify we can connect
    if ssh_running:
        verify_ssh_connection()
    else:
        print("\nPlease start the mock SSH server using:")
        print("python mock_ssh_server.py")
    
    print("\n========== Setup Complete ==========")
    print("You can now log in with:")
    print("Username: admin")
    print("Password: Welcome1@123")
    print("\nTest circuit IDs: TEST-001, TEST-002, TEST-MULTI")
    print("====================================")

if __name__ == "__main__":
    main()