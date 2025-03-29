#!/usr/bin/env python3
"""
Script to add profile fields to the user table.
This is a one-time migration script.
"""

import logging
import os
import psycopg2
from psycopg2 import sql

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_user_profile_columns():
    """Add profile columns to the user table"""
    # Get database connection parameters from environment variables
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return

    try:
        # Connect to the database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Get current columns in the user table
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'user'")
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add the new columns if they don't exist
        new_columns = {
            'first_name': 'VARCHAR(50)',
            'last_name': 'VARCHAR(50)',
            'phone': 'VARCHAR(20)',
            'avatar': 'VARCHAR(255)',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    # Use parameterized SQL to avoid SQL injection
                    query = sql.SQL("ALTER TABLE {} ADD COLUMN {} {}").format(
                        sql.Identifier('user'),
                        sql.Identifier(col_name),
                        sql.SQL(col_type)
                    )
                    cursor.execute(query)
                    logger.info(f"Added column '{col_name}' to user table.")
                except Exception as e:
                    logger.error(f"Error adding column '{col_name}': {str(e)}")
                    conn.rollback()  # Rollback on error
                    continue
        
        # Commit the transaction
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("User profile columns migration completed successfully.")
        
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")

if __name__ == "__main__":
    add_user_profile_columns()
    print("Migration script completed. Check the logs for details.")