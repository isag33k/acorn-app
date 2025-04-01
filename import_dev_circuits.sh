#!/bin/bash
# Script to run circuit import with the correct environment variables

# Activate the virtual environment
source /home/sjones/acorn-app/venv/bin/activate

# Set required environment variables
export DATABASE_URL="$(grep -oP 'SQLALCHEMY_DATABASE_URI\s*=\s*\K[^#\s]+' /home/sjones/acorn-app/.env 2>/dev/null || grep -oP 'DATABASE_URL\s*=\s*\K[^#\s]+' /home/sjones/acorn-app/.env 2>/dev/null)"

# If the .env file doesn't have the DATABASE_URL, let's try to get it from the systemd service file
if [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="$(grep -oP 'Environment="DATABASE_URL=\K[^"]+' /etc/systemd/system/acorn.service 2>/dev/null)"
fi

# If we still don't have it, ask the user
if [ -z "$DATABASE_URL" ]; then
    echo "DATABASE_URL environment variable not found."
    echo "Please enter your database connection string: "
    read -p "> " DATABASE_URL
    export DATABASE_URL
fi

echo "Using DATABASE_URL: $DATABASE_URL"

# Check if the dev circuit mappings file exists
if [ ! -f "dev_circuit_mappings.json" ]; then
    echo "❌ File 'dev_circuit_mappings.json' not found!"
    echo "Please copy this file from your development server first."
    exit 1
fi

# Run the import script
python circuit_import.py

# Check if the import was successful
if [ $? -eq 0 ]; then
    echo "✅ Circuit import completed successfully!"
    echo "Restart the application for changes to take effect:"
    echo "sudo systemctl restart acorn"
else
    echo "❌ Circuit import failed. Please check the error messages above."
fi