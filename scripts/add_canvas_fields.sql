-- ============================================================================
-- Add Canvas Integration Fields to Tasks Table
-- Run this in Supabase SQL Editor before syncing Canvas assignments
-- ============================================================================

-- Add Canvas assignment ID field
ALTER TABLE tasks 
ADD COLUMN IF NOT EXISTS canvas_assignment_id BIGINT;

-- Add Canvas course ID field
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

-- ============================================================================
-- Migration Complete!
-- You can now sync Canvas assignments
-- ============================================================================

SELECT 'Canvas fields added successfully!' as message;

