#!/usr/bin/env python3
"""
Script to add sample circuit mappings to the database.
This script adds circuit mappings for the network equipment.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_circuit_mappings():
    """Add sample circuit mappings to the database"""
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            sys.exit(1)
            
        # Create engine
        engine = create_engine(database_url)
        
        # Sample circuit mappings
        circuit_mappings = [
            # Atlanta circuits
            {
                "circuit_id": "ATL-ARELION-001",
                "equipment_name": "ATL1-CORE-RTR1",
                "command": "show interfaces descriptions | include ATL-ARELION-001",
                "description": "Arelion Transit Circuit - Atlanta",
                "contact_name": "Arelion NOC",
                "contact_email": "noc@arelion.com",
                "contact_phone": "1-800-555-0100"
            },
            {
                "circuit_id": "ATL-COGENT-001",
                "equipment_name": "ATL1-CORE-RTR2",
                "command": "show interfaces descriptions | include ATL-COGENT-001",
                "description": "Cogent Transit Circuit - Atlanta",
                "contact_name": "Cogent NOC",
                "contact_email": "noc@cogent.com",
                "contact_phone": "1-800-555-0200"
            },
            {
                "circuit_id": "ATL-CORESITE-001",
                "equipment_name": "ATL2-EDGE-RTR1",
                "command": "show interfaces descriptions | include ATL-CORESITE-001",
                "description": "CoreSite Cross-Connect - Atlanta",
                "contact_name": "CoreSite Support",
                "contact_email": "support@coresite.com",
                "contact_phone": "1-800-555-0300"
            },
            
            # Dallas circuits
            {
                "circuit_id": "DAL-ARELION-001",
                "equipment_name": "DAL1-CORE-RTR1",
                "command": "show interfaces descriptions | include DAL-ARELION-001",
                "description": "Arelion Transit Circuit - Dallas",
                "contact_name": "Arelion NOC",
                "contact_email": "noc@arelion.com",
                "contact_phone": "1-800-555-0100"
            },
            {
                "circuit_id": "DAL-COGENT-001",
                "equipment_name": "DAL1-CORE-RTR2",
                "command": "show interfaces descriptions | include DAL-COGENT-001",
                "description": "Cogent Transit Circuit - Dallas",
                "contact_name": "Cogent NOC",
                "contact_email": "noc@cogent.com",
                "contact_phone": "1-800-555-0200"
            },
            
            # Chicago circuits
            {
                "circuit_id": "CHI-ARELION-001",
                "equipment_name": "CHI1-CORE-RTR1",
                "command": "show interfaces descriptions | include CHI-ARELION-001",
                "description": "Arelion Transit Circuit - Chicago",
                "contact_name": "Arelion NOC",
                "contact_email": "noc@arelion.com",
                "contact_phone": "1-800-555-0100"
            },
            {
                "circuit_id": "CHI-COGENT-001",
                "equipment_name": "CHI1-CORE-RTR2",
                "command": "show interfaces descriptions | include CHI-COGENT-001",
                "description": "Cogent Transit Circuit - Chicago",
                "contact_name": "Cogent NOC",
                "contact_email": "noc@cogent.com",
                "contact_phone": "1-800-555-0200"
            },
            
            # OLT commands
            {
                "circuit_id": "ATL-OLT1-CONFIG",
                "equipment_name": "ATL1-OLT-1",
                "command": "show running-config",
                "description": "Atlanta OLT 1 - Show Running Configuration",
                "contact_name": "Network Operations",
                "contact_email": "network@example.com",
                "contact_phone": "1-800-555-1000"
            },
            {
                "circuit_id": "DAL-OLT1-CONFIG",
                "equipment_name": "DAL1-OLT-1",
                "command": "show running-config",
                "description": "Dallas OLT 1 - Show Running Configuration",
                "contact_name": "Network Operations",
                "contact_email": "network@example.com",
                "contact_phone": "1-800-555-1000"
            },
            
            # Firewall commands
            {
                "circuit_id": "ATL-FW1-CONFIG",
                "equipment_name": "ATL1-FW-1",
                "command": "show configuration",
                "description": "Atlanta Firewall 1 - Show Configuration",
                "contact_name": "Security Team",
                "contact_email": "security@example.com",
                "contact_phone": "1-800-555-2000"
            },
            {
                "circuit_id": "DAL-FW1-CONFIG",
                "equipment_name": "DAL1-FW-1",
                "command": "show configuration",
                "description": "Dallas Firewall 1 - Show Configuration",
                "contact_name": "Security Team",
                "contact_email": "security@example.com",
                "contact_phone": "1-800-555-2000"
            }
        ]
        
        # Connect to database
        with engine.connect() as connection:
            # Add each circuit mapping if it doesn't already exist
            for mapping in circuit_mappings:
                # Start transaction for each mapping
                with connection.begin():
                    # Get equipment ID
                    result = connection.execute(text(
                        f"SELECT id FROM equipment WHERE name = '{mapping['equipment_name']}'"
                    ))
                    equipment_row = result.fetchone()
                    
                    if not equipment_row:
                        logger.warning(f"Equipment {mapping['equipment_name']} not found, skipping circuit {mapping['circuit_id']}")
                        continue
                        
                    equipment_id = equipment_row[0]
                    
                    # Check if circuit mapping already exists
                    result = connection.execute(text(
                        f"SELECT COUNT(*) FROM circuit_mapping WHERE circuit_id = '{mapping['circuit_id']}' AND equipment_id = {equipment_id}"
                    ))
                    mapping_count = result.scalar()
                    
                    if mapping_count == 0:
                        # Insert circuit mapping
                        result = connection.execute(text(
                            "INSERT INTO circuit_mapping (circuit_id, equipment_id, command, description, "
                            "contact_name, contact_email, contact_phone) "
                            f"VALUES ('{mapping['circuit_id']}', {equipment_id}, '{mapping['command']}', "
                            f"'{mapping['description']}', '{mapping['contact_name']}', '{mapping['contact_email']}', "
                            f"'{mapping['contact_phone']}') "
                            "RETURNING id"
                        ))
                        mapping_id = result.scalar()
                        logger.info(f"Added circuit mapping {mapping['circuit_id']} with ID {mapping_id}")
                    else:
                        logger.info(f"Circuit mapping {mapping['circuit_id']} already exists, skipping.")
                
            logger.info("Successfully added all circuit mappings.")
                
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting migration to add sample circuit mappings...")
    add_circuit_mappings()
    logger.info("Migration completed.")