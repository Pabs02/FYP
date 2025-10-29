-- ============================================================================
-- Authentication Migration SQL
-- Run this directly in Supabase SQL Editor to add authentication fields
-- ============================================================================

-- Add authentication fields to students table
ALTER TABLE students 
ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;

ALTER TABLE students 
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

ALTER TABLE students 
ADD COLUMN IF NOT EXISTS canvas_api_token VARCHAR(500);

ALTER TABLE students 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

ALTER TABLE students 
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;

-- Create index on email for faster login lookups
CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);

-- View results
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'students'
ORDER BY ordinal_position;

-- ============================================================================
-- Migration Complete!
-- Students can now register with email/password
-- ============================================================================

