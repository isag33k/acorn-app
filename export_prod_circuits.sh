#!/bin/bash
# Script to run circuit export with the correct environment variables

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

# Run the export script
python circuit_export.py --output=production_backup_circuits.json

# Check if the export was successful
if [ $? -eq 0 ]; then
    echo "✅ Circuit export completed successfully!"
    echo "Backup file created: production_backup_circuits.json"
else
    echo "❌ Circuit export failed. Please check the error messages above."
fi