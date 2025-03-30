"""
Simple migration script to add key_filename columns to equipment and user_credential tables.
This script uses raw SQL to avoid requiring additional dependencies.
"""

import os
import sys
import psycopg2
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration():
    """Run migration to add key_filename columns to tables"""
    try:
        # Get database URL from environment
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL environment variable not found")
            sys.exit(1)
        
        # Connect to database using psycopg2 (should already be installed since it's used by the app)
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        try:
            # Start transaction
            logger.info("Starting database migration")
            
            # Check if equipment.key_filename column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='equipment' AND column_name='key_filename';
            """)
            
            if cursor.fetchone() is None:
                logger.info("Adding key_filename column to equipment table")
                cursor.execute("""
                    ALTER TABLE equipment 
                    ADD COLUMN key_filename VARCHAR(255) NULL;
                """)
                logger.info("Successfully added key_filename column to equipment table")
            else:
                logger.info("key_filename column already exists in equipment table")
            
            # Check if user_credential.key_filename column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='user_credential' AND column_name='key_filename';
            """)
            
            if cursor.fetchone() is None:
                logger.info("Adding key_filename column to user_credential table")
                cursor.execute("""
                    ALTER TABLE user_credential 
                    ADD COLUMN key_filename VARCHAR(255) NULL;
                """)
                logger.info("Successfully added key_filename column to user_credential table")
            else:
                logger.info("key_filename column already exists in user_credential table")
            
            # Commit transaction
            conn.commit()
            logger.info("Migration completed successfully")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error during migration: {str(e)}")
            sys.exit(1)
            
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting migration script")
    run_migration()