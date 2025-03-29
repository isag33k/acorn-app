#!/usr/bin/env python3
"""
One-time script to initialize the database with proper schema settings.
"""
import os
import sys
import psycopg2
from psycopg2 import sql
from app import app, db, init_db
from sqlalchemy import text

# Get database connection details from the app config
db_url = app.config["SQLALCHEMY_DATABASE_URI"]
db_parts = db_url.split("/")
db_name = db_parts[-1].split("?")[0]  # Extract database name
db_conn_parts = db_parts[2].split("@")
db_user_pass = db_conn_parts[0].split(":")
db_user = db_user_pass[0]

print(f"Setting up database for user: {db_user}")
print(f"Database name: {db_name}")

try:
    # Connect directly with psycopg2 as postgres user
    # You'll need to provide the postgres password
    postgres_password = input("Enter PostgreSQL superuser (postgres) password: ")
    
    # Connect as superuser
    conn = psycopg2.connect(
        dbname=db_name,
        user="postgres",
        password=postgres_password,
        host="localhost"
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Create acorn_schema if it doesn't exist
    cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS acorn_schema;"))
    
    # Grant privileges on the schema to the application user
    cursor.execute(sql.SQL("GRANT ALL ON SCHEMA acorn_schema TO {};").format(
        sql.Identifier(db_user)))
    cursor.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA acorn_schema "
                           "GRANT ALL ON TABLES TO {};").format(
        sql.Identifier(db_user)))
    cursor.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA acorn_schema "
                           "GRANT ALL ON SEQUENCES TO {};").format(
        sql.Identifier(db_user)))
    
    print("Schema and permissions created successfully.")
    cursor.close()
    conn.close()
    
    # Now set the search_path in SQLAlchemy session
    with app.app_context():
        # Set search_path for this session
        db.session.execute(text("SET search_path TO acorn_schema, public;"))
        db.session.commit()
        
        # Initialize the database
        init_db()
        print("Database tables created successfully in acorn_schema.")
    
except Exception as e:
    print(f"Error setting up database: {e}")
    sys.exit(1)
