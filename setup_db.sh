#!/bin/bash
# Script to set up PostgreSQL database for ACORN

echo "Setting up database for ACORN application"

# Prompt for database details
read -p "Enter database name: " DB_NAME
read -p "Enter database user: " DB_USER
read -p "Enter database host [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}
read -p "Enter database port [5432]: " DB_PORT
DB_PORT=${DB_PORT:-5432}

# Prompt for postgres user password
read -sp "Enter PostgreSQL superuser (postgres) password: " PGPASS
echo

# Create schema and set permissions using postgres user
export PGPASSWORD=$PGPASS

echo "Creating schema and setting permissions..."
psql -U postgres -h $DB_HOST -p $DB_PORT -d $DB_NAME << EOF
CREATE SCHEMA IF NOT EXISTS acorn_schema;
GRANT ALL ON SCHEMA acorn_schema TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA acorn_schema GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA acorn_schema GRANT ALL ON SEQUENCES TO $DB_USER;
EOF

if [ $? -ne 0 ]; then
  echo "Error: Failed to create schema and set permissions."
  exit 1
fi

echo "Schema and permissions created successfully."

# Now create a modified version of app.py that uses the schema
echo "Creating modified app.py..."
cat > /home/sjones/acorn-app/app_fixed.py << 'EOF'
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "a secret key"

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "connect_args": {"options": "-c search_path=acorn_schema,public"}
}
# initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Set search path explicitly for this session
    db.session.execute(text("SET search_path TO acorn_schema, public;"))
    db.session.commit()
    
    # Import models and create tables
    import models
    db.create_all()
    print("Database tables created successfully in acorn_schema.")
EOF

echo ""
echo "Now run the following command to test the fixed setup:"
echo "python app_fixed.py"
echo "If successful, replace app.py with app_fixed.py."

# Make script executable
chmod +x /home/sjones/acorn-app/app_fixed.py
