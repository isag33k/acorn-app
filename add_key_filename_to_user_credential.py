"""
Script to add key_filename field to the user_credential table.
This is a one-time migration script.
"""

import sys
import os
import logging
from sqlalchemy import create_engine, text
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_key_filename_column():
    """Add key_filename column to the user_credential table"""
    try:
        # Get database URL from environment
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL environment variable not found")
            sys.exit(1)
        
        # Create connection to database
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Start a transaction
            with connection.begin():
                # Check if column already exists
                check_sql = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='user_credential' AND column_name='key_filename';
                """)
                
                result = connection.execute(check_sql)
                column_exists = result.fetchone() is not None
                
                if column_exists:
                    logger.info("key_filename column already exists in user_credential table")
                    return
                
                # Add the column
                logger.info("Adding key_filename column to user_credential table")
                add_column_sql = text("""
                    ALTER TABLE user_credential 
                    ADD COLUMN key_filename VARCHAR(255) NULL;
                """)
                
                connection.execute(add_column_sql)
                logger.info("Successfully added key_filename column to user_credential table")
                
    except Exception as e:
        logger.error(f"Error adding key_filename column: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting migration to add key_filename column to user_credential table")
    add_key_filename_column()
    logger.info("Migration completed successfully")