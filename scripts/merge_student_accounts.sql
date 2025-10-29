-- ============================================================================
-- Merge Duplicate Student Accounts Script
-- Run this in Supabase SQL Editor to fix the duplicate student issue
-- ============================================================================

-- STEP 1: View current student records
SELECT 
    id, 
    name, 
    email,
    (SELECT COUNT(*) FROM tasks WHERE student_id = s.id) as task_count,
    created_at
FROM students s
ORDER BY id;

-- You should see TWO records for yourself:
-- Record A: Old student (has tasks, NO email)
-- Record B: New student (has email, NO tasks)

-- ============================================================================
-- OPTION 1: Keep OLD record (with tasks), add authentication to it
-- ============================================================================

-- Find the new record's authentication info
-- SELECT id, email, password_hash FROM students WHERE email IS NOT NULL;

-- Copy authentication from NEW record to OLD record
-- REPLACE THESE VALUES:
--   - 'your.email@umail.ucc.ie' with your actual email
--   - OLD_STUDENT_ID with the ID that has tasks
--   - NEW_STUDENT_ID with the ID that has email

/*
UPDATE students 
SET 
    email = 'your.email@umail.ucc.ie',
    password_hash = (SELECT password_hash FROM students WHERE id = NEW_STUDENT_ID),
    canvas_api_token = '13518~WXBMkD6LHmBmJeePx3t2ZAeFNNwyUkTZ4yUy4c4eP3Q4EkBZyuLZUGKr47ycrCrA',
    created_at = NOW()
WHERE id = OLD_STUDENT_ID;

-- Delete the duplicate NEW record (has no tasks)
DELETE FROM students WHERE id = NEW_STUDENT_ID;
*/

-- ============================================================================
-- OPTION 2: Keep NEW record (with auth), move tasks to it
-- ============================================================================

/*
-- Move all tasks from OLD record to NEW record
UPDATE tasks 
SET student_id = NEW_STUDENT_ID
WHERE student_id = OLD_STUDENT_ID;

-- Add Canvas token to NEW record
UPDATE students 
SET canvas_api_token = '13518~WXBMkD6LHmBmJeePx3t2ZAeFNNwyUkTZ4yUy4c4eP3Q4EkBZyuLZUGKr47ycrCrA'
WHERE id = NEW_STUDENT_ID;

-- Delete OLD record (now has no tasks)
DELETE FROM students WHERE id = OLD_STUDENT_ID;
*/

-- ============================================================================
-- VERIFICATION: Check you have ONE record with email AND tasks
-- ============================================================================

SELECT 
    s.id, 
    s.name, 
    s.email,
    s.canvas_api_token IS NOT NULL as has_canvas_token,
    COUNT(t.id) as task_count
FROM students s
LEFT JOIN tasks t ON t.student_id = s.id
GROUP BY s.id, s.name, s.email, s.canvas_api_token
ORDER BY s.id;

-- You should see ONE record with:
--   - Your name
--   - Your email
--   - has_canvas_token = true
--   - task_count > 0

-- ============================================================================
-- After running this, LOGOUT and LOGIN again in your app
-- ============================================================================

