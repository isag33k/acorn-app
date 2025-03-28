import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect, Text

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Enable host as 0.0.0.0 to be accessible from outside
app.config["SERVER_NAME"] = None

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

def alter_column_type(table_name, column_name, new_type):
    """Helper function to alter column type in the database"""
    from sqlalchemy.sql import text
    
    try:
        # Create the ALTER TABLE statement
        alter_statement = text(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {new_type}")
        
        # Execute the statement
        db.session.execute(alter_statement)
        db.session.commit()
        logger.info(f"Successfully changed {table_name}.{column_name} to {new_type}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing column type: {str(e)}")
        return False

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models
    import models  # noqa: F401
    
    # Create all tables
    db.create_all()
    
    # Check if the circuit_mapping.command column needs to be converted to TEXT
    inspector = inspect(db.engine)
    if 'circuit_mapping' in inspector.get_table_names():
        columns = inspector.get_columns('circuit_mapping')
        for column in columns:
            if column['name'] == 'command':
                # Check if the column is already Text
                if not isinstance(column['type'], Text) and not str(column['type']).lower() == 'text':
                    logger.info("Altering circuit_mapping.command column to TEXT type")
                    alter_column_type('circuit_mapping', 'command', 'TEXT')
                break
    
    logger.debug("Database tables created")
