-- Reference: ChatGPT (Open AI) - Canvas Integration Database Schema
-- Date: 2025-10-20
-- Prompt: "I need to add Canvas LMS integration fields to my tasks table in PostgreSQL. 
-- I need columns for canvas_assignment_id and canvas_course_id, plus indexes for performance 
-- and a unique constraint to prevent duplicate assignments per student. Can you give me 
-- the SQL migration script?"
-- ChatGPT provided the ALTER TABLE statements, indexes, and unique constraint pattern.

-- Add Canvas Integration Fields to Tasks Table




ALTER TABLE tasks 
ADD COLUMN IF NOT EXISTS canvas_assignment_id BIGINT;


ALTER TABLE tasks 
ADD COLUMN IF NOT EXISTS canvas_course_id BIGINT;

-- Create index on canvas_assignment_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_tasks_canvas_assignment 
ON tasks(canvas_assignment_id);

-- Create index on canvas_course_id for course-based queries
CREATE INDEX IF NOT EXISTS idx_tasks_canvas_course 
ON tasks(canvas_course_id);

-- Add unique constraint to prevent duplicate Canvas assignments per student
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_canvas_assignment_per_student 
ON tasks(student_id, canvas_assignment_id) 
WHERE canvas_assignment_id IS NOT NULL;

-- View results
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'tasks' 
AND column_name LIKE '%canvas%'
ORDER BY ordinal_position;





SELECT 'Canvas fields added successfully!' as message;

