-- Reference: ChatGPT (OpenAI) - Authentication Fields Migration
-- Date: 2025-10-10
-- Prompt: "I need to add authentication fields to my students table in PostgreSQL. 
-- I need email (unique), password_hash, canvas_api_token, created_at, and last_login 
-- columns. Can you give me the migration SQL with proper indexes?"
-- ChatGPT provided the ALTER TABLE statements for all authentication fields and 
-- email index for login performance.

-- Authentication Migration SQL

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



