-- Reference: ChatGPT (OpenAI) - Study Group Room Bookings Migration
-- Date: 2026-02-25
-- Prompt: "I need a safe SQL migration to store module-level study room bookings
-- within study groups, with who booked, date/time, duration, and notes. Please use
-- idempotent CREATE TABLE/INDEX patterns."
-- ChatGPT provided the idempotent migration pattern adapted below.

CREATE TABLE IF NOT EXISTS study_group_room_bookings (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES study_groups(id) ON DELETE CASCADE,
    booked_by_student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    room_name TEXT NOT NULL,
    booked_for_at TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 60,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_study_group_room_bookings_group
    ON study_group_room_bookings(group_id, booked_for_at DESC);
