#!/usr/bin/env python3
"""
Script to add common network equipment to the database.
This script adds ~30 equipment entries that would typically exist in production.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_network_equipment():
    """Add common network equipment to the database"""
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            sys.exit(1)
            
        # Create engine
        engine = create_engine(database_url)
        
        # Common network equipment to add
        equipment_list = [
            # Routers
            {"name": "ATL1-CORE-RTR1", "ip_address": "10.1.1.1", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "ATL1-CORE-RTR2", "ip_address": "10.1.1.2", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "ATL2-EDGE-RTR1", "ip_address": "10.1.2.1", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "DAL1-CORE-RTR1", "ip_address": "10.2.1.1", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "DAL1-CORE-RTR2", "ip_address": "10.2.1.2", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "DAL2-EDGE-RTR1", "ip_address": "10.2.2.1", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "CHI1-CORE-RTR1", "ip_address": "10.3.1.1", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "CHI1-CORE-RTR2", "ip_address": "10.3.1.2", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "CHI2-EDGE-RTR1", "ip_address": "10.3.2.1", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            
            # Switches
            {"name": "ATL1-CORE-SW1", "ip_address": "10.1.1.101", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "ATL1-CORE-SW2", "ip_address": "10.1.1.102", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "ATL1-DIST-SW1", "ip_address": "10.1.1.111", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "ATL1-DIST-SW2", "ip_address": "10.1.1.112", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "DAL1-CORE-SW1", "ip_address": "10.2.1.101", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "DAL1-CORE-SW2", "ip_address": "10.2.1.102", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "DAL1-DIST-SW1", "ip_address": "10.2.1.111", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "DAL1-DIST-SW2", "ip_address": "10.2.1.112", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            
            # OLTs
            {"name": "ATL1-OLT-1", "ip_address": "10.1.3.1", "ssh_port": 22, "username": "admin", "password": "olt_password"},
            {"name": "ATL1-OLT-2", "ip_address": "10.1.3.2", "ssh_port": 22, "username": "admin", "password": "olt_password"},
            {"name": "DAL1-OLT-1", "ip_address": "10.2.3.1", "ssh_port": 22, "username": "admin", "password": "olt_password"},
            {"name": "DAL1-OLT-2", "ip_address": "10.2.3.2", "ssh_port": 22, "username": "admin", "password": "olt_password"},
            
            # Firewalls
            {"name": "ATL1-FW-1", "ip_address": "10.1.4.1", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "ATL1-FW-2", "ip_address": "10.1.4.2", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "DAL1-FW-1", "ip_address": "10.2.4.1", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            {"name": "DAL1-FW-2", "ip_address": "10.2.4.2", "ssh_port": 22, "username": "TACACS", "password": "TACACS_PLACEHOLDER"},
            
            # Other devices
            {"name": "ATL1-LB-1", "ip_address": "10.1.5.1", "ssh_port": 22, "username": "admin", "password": "load_balancer_pw"},
            {"name": "DAL1-LB-1", "ip_address": "10.2.5.1", "ssh_port": 22, "username": "admin", "password": "load_balancer_pw"},
            {"name": "CHI1-LB-1", "ip_address": "10.3.5.1", "ssh_port": 22, "username": "admin", "password": "load_balancer_pw"}
        ]
        
        # Connect to database
        with engine.connect() as connection:
            # Start transaction
            with connection.begin():
                # Add each equipment if it doesn't already exist
                for equipment in equipment_list:
                    # Check if equipment already exists
                    result = connection.execute(text(
                        f"SELECT COUNT(*) FROM equipment WHERE ip_address = '{equipment['ip_address']}' AND name = '{equipment['name']}'"
                    ))
                    equipment_count = result.scalar()
                    
                    if equipment_count == 0:
                        # Insert equipment
                        result = connection.execute(text(
                            "INSERT INTO equipment (name, ip_address, ssh_port, username, password) "
                            f"VALUES ('{equipment['name']}', '{equipment['ip_address']}', {equipment['ssh_port']}, "
                            f"'{equipment['username']}', '{equipment['password']}') "
                            "RETURNING id"
                        ))
                        equipment_id = result.scalar()
                        logger.info(f"Added equipment {equipment['name']} with ID {equipment_id}")
                    else:
                        logger.info(f"Equipment {equipment['name']} already exists, skipping.")
                
                logger.info("Successfully added all network equipment.")
                
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting migration to add common network equipment...")
    add_network_equipment()
    logger.info("Migration completed.")