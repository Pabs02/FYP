-- Reference: ChatGPT (OpenAI) - Lecturer Replies Table Schema
-- Date: 2026-02-03
-- Prompt: "I need a PostgreSQL table to store incoming email replies from lecturers.
-- It should track the student, optionally link to a lecturer record, store email
-- fields (from_email, from_name, subject, body, received_at), have a read/unread
-- flag, and prevent duplicates using message-id. Can you provide the schema?"
-- ChatGPT provided the table schema with foreign keys and indexes.

CREATE TABLE IF NOT EXISTS lecturer_replies (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    lecturer_id INTEGER REFERENCES lecturers(id) ON DELETE SET NULL,
    from_email VARCHAR(255) NOT NULL,
    from_name VARCHAR(255),
    subject VARCHAR(500),
    body TEXT,
    received_at TIMESTAMP WITH TIME ZONE,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_read BOOLEAN DEFAULT FALSE,
    message_id VARCHAR(255) UNIQUE,  -- Email Message-ID to prevent duplicates
    in_reply_to INTEGER REFERENCES lecturer_messages(id) ON DELETE SET NULL  -- Link to original message if detected
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_lecturer_replies_student_id ON lecturer_replies(student_id);
CREATE INDEX IF NOT EXISTS idx_lecturer_replies_is_read ON lecturer_replies(student_id, is_read);
CREATE INDEX IF NOT EXISTS idx_lecturer_replies_message_id ON lecturer_replies(message_id);


