-- Create events table to store timed calendar items (e.g., lectures)
CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    module_id BIGINT REFERENCES modules(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    start_at TIMESTAMPTZ NOT NULL,
    end_at   TIMESTAMPTZ NOT NULL,
    location TEXT,
    canvas_event_id BIGINT,
    canvas_course_id BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure uniqueness per student per Canvas event
CREATE UNIQUE INDEX IF NOT EXISTS idx_events_unique_canvas_event
ON events(student_id, canvas_event_id) WHERE canvas_event_id IS NOT NULL;

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_events_student_start ON events(student_id, start_at);
CREATE INDEX IF NOT EXISTS idx_events_module ON events(module_id);
