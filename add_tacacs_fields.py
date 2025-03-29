#!/usr/bin/env python3
"""
Script to add TACACS credential fields to the user table.
This is a one-time migration script.
"""

import os
import sys
from sqlalchemy import create_engine, text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the database URL from the environment
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

def add_tacacs_columns():
    """Add TACACS credential columns to the user table"""
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    
    try:
        # Check if the columns already exist to avoid errors
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user' AND column_name = 'tacacs_username'
        """))
        if result.rowcount > 0:
            logger.info("Column 'tacacs_username' already exists in the 'user' table")
            return
        
        # Add the tacacs_username column
        conn.execute(text("""
            ALTER TABLE "user" ADD COLUMN tacacs_username VARCHAR(50)
        """))
        logger.info("Added 'tacacs_username' column to 'user' table")
        
        # Add the tacacs_password column
        conn.execute(text("""
            ALTER TABLE "user" ADD COLUMN tacacs_password VARCHAR(100)
        """))
        logger.info("Added 'tacacs_password' column to 'user' table")
        
        # Commit the transaction
        conn.commit()
        logger.info("TACACS credential columns successfully added to the 'user' table")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding TACACS columns: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting migration to add TACACS credential columns")
    add_tacacs_columns()
    logger.info("Migration completed successfully")