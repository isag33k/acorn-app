# Circuit Database Migration Guide

This guide explains how to copy the Circuit ID Database from a development server to a production server.

## Overview

The migration process involves:
1. Exporting circuit mappings from the development server
2. Copying the export file to the production server
3. Importing the circuit mappings on the production server

## Step-by-Step Instructions

### On Your Development Server

1. Pull the latest code changes from GitHub:

```bash
git pull origin main
```

2. Run the export script to create a JSON file with all circuit mapping data:

```bash
# If your environment is already set up correctly
python circuit_export.py

# Or use the helper shell script we created
./export_prod_circuits.sh
```

3. This will create a file called `dev_circuit_mappings.json` in the current directory.

4. Copy this file to your production server using SCP, SFTP, or any other secure file transfer method.

Example:
```bash
scp dev_circuit_mappings.json user@production-server:/path/to/acorn-app/
```

### On Your Production Server

1. Pull the latest code changes from GitHub:

```bash
git pull origin main
```

2. Place the `dev_circuit_mappings.json` file in the root directory of your ACORN application.

3. **IMPORTANT**: Make a backup of your production database before proceeding:

```bash
# Use our helper script to create a backup
./export_prod_circuits.sh
```

4. Run the import script:

```bash
# If your environment is already set up correctly
python circuit_import.py

# Or use the helper shell script we created
./import_dev_circuits.sh
```

5. Follow the prompts in the import script:
   - You'll be asked if you want to replace all existing circuit mappings or just add new ones
   - The script will confirm your choice before proceeding

6. Once the import is complete, restart your application to ensure all changes take effect:

```bash
sudo systemctl restart acorn
```

## Troubleshooting

### Environment Setup Issues

If you encounter issues with missing Python modules or database connection errors:

1. Make sure your virtual environment is activated:
   ```bash
   source /home/sjones/acorn-app/venv/bin/activate
   ```

2. Make sure the DATABASE_URL environment variable is set:
   ```bash
   export DATABASE_URL="your_postgresql_connection_string"
   ```

3. Use the helper scripts we created that handle environment setup automatically:
   ```bash
   ./export_prod_circuits.sh
   ./import_dev_circuits.sh
   ```

### Missing Equipment References

If the import script shows warnings about missing equipment references, it means that some circuits in your dev environment reference equipment that doesn't exist on your production server.

To fix this:
1. Either import the equipment data first using `import_production_data.py`
2. Or modify the `dev_circuit_mappings.json` file to only include circuits that reference existing equipment

### File Permission Issues

If you encounter file permission issues, ensure that:
1. The JSON file is readable by the user running the import script
2. The database file (or database server) is writable by the application
3. The helper scripts are executable: `chmod +x export_prod_circuits.sh import_dev_circuits.sh`

### Database Rollback

If the import fails and you need to restore your database:
1. Stop the application: `sudo systemctl stop acorn`
2. Restore your database backup
3. Restart the application: `sudo systemctl start acorn`