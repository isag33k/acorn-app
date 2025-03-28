#!/usr/bin/env python3
"""
Script to add a mock SSH server to the database for testing.
This is a one-time script.
"""

from app import app, db
from models import Equipment

def add_mock_ssh_server():
    """Add mock SSH server to the database"""
    with app.app_context():
        # Check if the mock server already exists
        existing = Equipment.query.filter_by(name="ACORN Test Router").first()
        if existing:
            print("Mock SSH server already exists in database.")
            return
        
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
        
        print(f"Added mock SSH server to database with ID: {mock_server.id}")
        
if __name__ == "__main__":
    add_mock_ssh_server()