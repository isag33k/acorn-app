"""
Script to add contact fields to the circuit_mapping table.
This is a one-time migration script.
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    logger.error("DATABASE_URL environment variable not set.")
    sys.exit(1)

# Create engine and connect
engine = create_engine(db_url)

def add_contact_columns():
    """Add contact columns to the circuit_mapping table"""
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            check_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'circuit_mapping' 
                AND column_name = 'contact_name'
            """)
            result = conn.execute(check_sql)
            if result.rowcount > 0:
                logger.info("Contact columns already exist.")
                return True
            
            # Add contact columns if they don't exist
            logger.info("Adding contact columns to circuit_mapping table...")
            
            # Add contact_name column
            conn.execute(text("""
                ALTER TABLE circuit_mapping 
                ADD COLUMN contact_name VARCHAR(100)
            """))
            
            # Add contact_email column
            conn.execute(text("""
                ALTER TABLE circuit_mapping 
                ADD COLUMN contact_email VARCHAR(120)
            """))
            
            # Add contact_phone column
            conn.execute(text("""
                ALTER TABLE circuit_mapping 
                ADD COLUMN contact_phone VARCHAR(20)
            """))
            
            # Add contact_notes column
            conn.execute(text("""
                ALTER TABLE circuit_mapping 
                ADD COLUMN contact_notes TEXT
            """))
            
            # Commit the changes
            conn.commit()
            
            logger.info("Contact columns added successfully!")
            return True
    except Exception as e:
        logger.error(f"Error adding contact columns: {str(e)}")
        return False

if __name__ == "__main__":
    add_contact_columns()