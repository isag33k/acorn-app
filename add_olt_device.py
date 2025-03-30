#!/usr/bin/env python3
"""
Script to add the SHA1-FL-OLT-1 OLT device to the database.
This is a one-time script.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_olt_device():
    """Add SHA1-FL-OLT-1 OLT device to the database"""
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            sys.exit(1)
            
        # Create engine
        engine = create_engine(database_url)
        
        # Connect to database
        with engine.connect() as connection:
            # Check if equipment already exists
            result = connection.execute(text(
                "SELECT COUNT(*) FROM equipment WHERE ip_address = '10.160.15.4' AND name = 'SHA1-FL-OLT-1'"
            ))
            equipment_count = result.scalar()
            
            if equipment_count == 0:
                # Start transaction
                trans = connection.begin()
                try:
                    # Insert equipment
                    result = connection.execute(text(
                        "INSERT INTO equipment (name, ip_address, ssh_port, username, password) "
                        "VALUES ('SHA1-FL-OLT-1', '10.160.15.4', 22, 'admin', 'adminpass') "
                        "RETURNING id"
                    ))
                    equipment_id = result.scalar()
                    
                    # Insert circuit mapping
                    connection.execute(text(
                        "INSERT INTO circuit_mapping (circuit_id, equipment_id, command, description) "
                        f"VALUES ('SHA1-FL-OLT-1', {equipment_id}, 'sh run', 'Florida OLT Device 1 - Show Running Configuration')"
                    ))
                    
                    # Commit transaction
                    trans.commit()
                    logger.info("Added SHA1-FL-OLT-1 equipment and circuit mapping successfully.")
                except Exception as e:
                    # Rollback on error
                    trans.rollback()
                    logger.error(f"Transaction failed: {str(e)}")
                    raise
            else:
                logger.info("SHA1-FL-OLT-1 equipment already exists, skipping.")
                
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting migration to add SHA1-FL-OLT-1 OLT device...")
    add_olt_device()
    logger.info("Migration completed.")