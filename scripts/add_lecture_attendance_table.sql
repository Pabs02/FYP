-- Reference: ChatGPT (OpenAI) - Lecture Attendance Tracking Schema
-- Date: 2026-02-11
-- Prompt: "I need a PostgreSQL table to track lecture attendance per student per
-- calendar event, with an attended flag and timestamp. It should prevent duplicate
-- attendance rows for the same student/event and include useful indexes."
-- ChatGPT provided the schema pattern below.

CREATE TABLE IF NOT EXISTS lecture_attendance (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    attended BOOLEAN NOT NULL DEFAULT TRUE,
    attended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, event_id)
);

CREATE INDEX IF NOT EXISTS idx_lecture_attendance_student_event
    ON lecture_attendance(student_id, event_id);

CREATE INDEX IF NOT EXISTS idx_lecture_attendance_event
    ON lecture_attendance(event_id);
