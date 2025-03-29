#!/usr/bin/env python
"""
Script to add the Contact table to the database.
This is a one-time migration script.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_contact_table():
    """Add Contact table to the database"""
    try:
        # Get database connection string from environment variable
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            return False
            
        # Connect to the database
        engine = create_engine(database_url)
        metadata = MetaData()
        
        # Check if the table already exists
        inspector = engine.dialect.has_table(engine.connect(), 'contact')
        if inspector:
            logger.info("Contact table already exists, skipping creation")
            return True
            
        # Define the contact table
        contact = Table('contact', metadata,
            Column('id', Integer, primary_key=True),
            Column('first_name', String(50), nullable=False, index=True),
            Column('last_name', String(50), nullable=False, index=True),
            Column('company', String(100), nullable=False, index=True),
            Column('email', String(120), nullable=True),
            Column('phone', String(20), nullable=True, index=True),
            Column('mobile', String(20), nullable=True),
            Column('title', String(100), nullable=True),
            Column('address', String(200), nullable=True),
            Column('city', String(50), nullable=True, index=True),
            Column('state', String(50), nullable=True, index=True),
            Column('zip_code', String(20), nullable=True),
            Column('notes', Text, nullable=True),
            Column('created_at', DateTime, default=datetime.datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
        )
        
        # Create the table
        metadata.create_all(engine)
        logger.info("Successfully created contact table")
        return True
        
    except Exception as e:
        logger.error(f"Error creating contact table: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_contact_table()
    sys.exit(0 if success else 1)