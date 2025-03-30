-- Migration script to add key_filename columns

-- Add column to equipment table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name='equipment' AND column_name='key_filename'
    ) THEN
        ALTER TABLE equipment ADD COLUMN key_filename VARCHAR(255) NULL;
        RAISE NOTICE 'Added key_filename column to equipment table';
    ELSE
        RAISE NOTICE 'key_filename column already exists in equipment table';
    END IF;
END $$;

-- Add column to user_credential table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name='user_credential' AND column_name='key_filename'
    ) THEN
        ALTER TABLE user_credential ADD COLUMN key_filename VARCHAR(255) NULL;
        RAISE NOTICE 'Added key_filename column to user_credential table';
    ELSE
        RAISE NOTICE 'key_filename column already exists in user_credential table';
    END IF;
END $$;