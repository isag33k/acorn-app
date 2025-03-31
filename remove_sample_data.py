#!/usr/bin/env python3
"""
Script to remove fictional sample data from the database.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def remove_sample_data():
    """Remove the sample equipment and circuit mappings we added"""
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
            # Start transaction
            with connection.begin():
                # First, delete the circuit mappings (due to foreign key constraints)
                # Get only the mappings for fictional circuits we added recently
                result = connection.execute(text(
                    "DELETE FROM circuit_mapping WHERE circuit_id LIKE 'ATL-%' OR circuit_id LIKE 'DAL-%' OR circuit_id LIKE 'CHI-%'"
                ))
                logger.info(f"Deleted {result.rowcount} sample circuit mappings")
                
                # Delete the equipment excluding the original 3 devices
                result = connection.execute(text(
                    "DELETE FROM equipment WHERE id > 7"
                ))
                logger.info(f"Deleted {result.rowcount} sample equipment records")
                
            logger.info("Successfully removed sample data.")
                
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting removal of sample data...")
    remove_sample_data()
    logger.info("Clean-up completed.")