-- Reference: ChatGPT (OpenAI) - Student Number Field
-- Date: 2026-01-23
-- Prompt: "I need to store a student_number on the students table so it can be used
-- in email signatures. Can you provide the SQL?"
-- ChatGPT provided the schema update for student numbers.
ALTER TABLE students
ADD COLUMN IF NOT EXISTS student_number VARCHAR(50);

CREATE INDEX IF NOT EXISTS idx_students_student_number ON students(student_number);
