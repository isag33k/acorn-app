-- Migration script for adding SHA1-FL-OLT-1 equipment and circuit mapping
-- Created: March 30, 2025

-- Check if the equipment already exists
DO $$
DECLARE
    equipment_count INTEGER;
    equipment_id INTEGER;
BEGIN
    -- Check if equipment already exists
    SELECT COUNT(*) INTO equipment_count FROM equipment 
    WHERE ip_address = '10.160.15.4' AND name = 'SHA1-FL-OLT-1';
    
    IF equipment_count = 0 THEN
        -- Insert the equipment if it doesn't exist
        INSERT INTO equipment (name, ip_address, ssh_port, username, password)
        VALUES ('SHA1-FL-OLT-1', '10.160.15.4', 22, 'admin', 'adminpass')
        RETURNING id INTO equipment_id;
        
        -- Insert the circuit mapping
        INSERT INTO circuit_mapping (circuit_id, equipment_id, command, description)
        VALUES ('SHA1-FL-OLT-1', equipment_id, 'sh run', 'Florida OLT Device 1 - Show Running Configuration');
        
        RAISE NOTICE 'Added SHA1-FL-OLT-1 equipment and circuit mapping successfully.';
    ELSE
        RAISE NOTICE 'SHA1-FL-OLT-1 equipment already exists, skipping.';
    END IF;
END $$;