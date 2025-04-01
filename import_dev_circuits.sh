#!/bin/bash
# Script to run circuit import with the correct environment variables

# For Replit environment - no need to activate a virtual environment

# Check if DATABASE_URL environment variable is already set
if [ -n "$DATABASE_URL" ]; then
    echo "Using existing DATABASE_URL environment variable"
else
    # For Replit environment, use the PostgreSQL connection details
    if [ -n "$PGDATABASE" ] && [ -n "$PGHOST" ] && [ -n "$PGPORT" ] && [ -n "$PGUSER" ] && [ -n "$PGPASSWORD" ]; then
        export DATABASE_URL="postgresql://$PGUSER:$PGPASSWORD@$PGHOST:$PGPORT/$PGDATABASE"
        echo "Created DATABASE_URL from PostgreSQL environment variables"
    fi
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

# Check if replace_option argument is provided
REPLACE_OPTION=${1:-"2"}  # Default to option 2 (add new only) if not specified

# Create a temporary script to automate the input selection
cat << EOF > /tmp/select_option.py
import sys

# Just print the selected option and exit
print("$REPLACE_OPTION")
EOF

# Run the import script with automated input selection
python -c "
import sys
import subprocess

# Start circuit_import.py with stdin/stdout directed to our process
process = subprocess.Popen(['python', 'circuit_import.py'], 
                          stdin=subprocess.PIPE, 
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          universal_newlines=True)

# Read output until we find the prompt
while True:
    output = process.stdout.readline()
    if not output:
        break
    print(output.strip())
    if 'Select option' in output:
        break

# Send the option choice
process.stdin.write('$REPLACE_OPTION\\n')
process.stdin.flush()

# Continue reading the remaining output
while True:
    output = process.stdout.readline()
    if not output:
        break
    print(output.strip())

# Read any error output
for line in process.stderr:
    print(line.strip())

# Get the exit code
exit_code = process.wait()
sys.exit(exit_code)
"

# Check if the import was successful
if [ $? -eq 0 ]; then
    echo "✅ Circuit import completed successfully!"
    echo "Restart the application for changes to take effect."
    echo "For Replit, this happens automatically when you restart the workflow."
else
    echo "❌ Circuit import failed. Please check the error messages above."
fi