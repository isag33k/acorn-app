"""
Script to add is_editor field to the user table.
This is a one-time migration script.
"""
import logging
from app import db, app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_is_editor_column():
    """Add is_editor column to the user table"""
    try:
        with app.app_context():
            # Check if column exists
            result = db.session.execute(text(
                "SELECT column_name FROM information_schema.columns "
                'WHERE table_name=\'user\' AND column_name=\'is_editor\''
            ))
            if result.fetchone():
                logger.info("is_editor column already exists in user table")
                return
            
            # Add the column
            db.session.execute(text(
                'ALTER TABLE "user" ADD COLUMN is_editor BOOLEAN DEFAULT FALSE'
            ))
            db.session.commit()
            
            logger.info("is_editor column added to user table successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error adding is_editor column: {str(e)}")
        raise

if __name__ == "__main__":
    add_is_editor_column()