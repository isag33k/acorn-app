# Synchronizing Production and Development Data

This document explains how to keep your development and production environments in sync, specifically for equipment and circuit mapping data.

## Option 1: Using Python Scripts (Recommended)

### Step 1: Export Data from Production
1. Copy the `export_production_data.py` script to your production server
2. Run it on the production server:
   ```bash
   python export_production_data.py
   ```
3. This will create two files:
   - `production_equipment.json`
   - `production_circuit_mappings.json`

### Step 2: Transfer Files to Development
1. Securely copy the JSON files from production to your development environment:
   ```bash
   scp user@production-server:~/production_equipment.json .
   scp user@production-server:~/production_circuit_mappings.json .
   ```

### Step 3: Import Data to Development
1. Place the JSON files in the root directory of your development environment
2. Run the import script:
   ```bash
   python import_production_data.py
   ```

## Option 2: Using Database Dumps

### Step 1: Export Tables from Production
1. On your production server, run:
   ```bash
   pg_dump -h $PGHOST -U $PGUSER -d $PGDATABASE -t equipment -f equipment_export.sql
   pg_dump -h $PGHOST -U $PGUSER -d $PGDATABASE -t circuit_mapping -f circuit_mapping_export.sql
   ```

### Step 2: Transfer Files to Development
1. Securely copy the SQL files from production to your development environment:
   ```bash
   scp user@production-server:~/equipment_export.sql .
   scp user@production-server:~/circuit_mapping_export.sql .
   ```

### Step 3: Import Tables to Development
1. First, clear the existing data (optional):
   ```sql
   DELETE FROM circuit_mapping WHERE equipment_id > 7;
   DELETE FROM equipment WHERE id > 7;
   ```

2. Import the new data:
   ```bash
   psql -h $PGHOST -U $PGUSER -d $PGDATABASE -f equipment_export.sql
   psql -h $PGHOST -U $PGUSER -d $PGDATABASE -f circuit_mapping_export.sql
   ```

## Security Considerations

* The JSON files will contain real passwords - handle them securely
* Delete the files after completing the import
* Consider masking or redacting sensitive data if needed

## Troubleshooting

* If you encounter foreign key constraint errors, make sure the equipment records are imported before circuit mappings
* If you see ID conflicts, you may need to adjust the sequences in the database
* If some circuit mappings are skipped during import, check the logs for details - it's usually because the referenced equipment ID doesn't exist