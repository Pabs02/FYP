================================================================================
FYP PROJECT CODE REFERENCES
Smart Student Planner - Student Task Management System
================================================================================

This file contains all references for external code, libraries, and resources
used in this project. References are organized by file and then by code section.



================================================================================
FILE: main.py
================================================================================

Lines 1-3: Flask Framework Imports
Reference: 
  - Flask Documentation. Flask Quickstart.
    URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/
  Used for building the web application framework.

Lines 5-7: Flask-Login Extension Imports
Reference:
  - Flask-Login Documentation. Managing User Sessions.
    URL: https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager
  Extension for handling user authentication and session management.

Lines 9-11: Werkzeug Security Imports
Reference:
  - Werkzeug Documentation. Password Hashing.
    URL: https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security
  Used for password hashing and verification (generate_password_hash, 
  check_password_hash).

Lines 21-24: Flask Application Initialization
Reference:
  - Flask Documentation. Application Setup.
    URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#a-minimal-application
  Standard Flask app creation pattern.

Lines 26-32: Flask-Login Initialization
Reference:
  - Flask-Login Documentation. Initializing Extension.
    URL: https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.init_app
  Setup follows Flask-Login quickstart guide for user session management.

Lines 35-38: User Class with UserMixin
Reference:
  - Flask-Login Documentation. User Class Implementation.
    URL: https://flask-login.readthedocs.io/en/latest/#flask_login.UserMixin
  Used UserMixin pattern from Flask-Login docs. Adapted to work with our 
  database structure.

Lines 73-79: User Loader Callback
Reference:
  - Flask-Login Documentation. User Loader Callback.
    URL: https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader
  Required callback function for Flask-Login to load users from session.

Lines 82-98: Custom Template Filters
Reference:
  - Flask Documentation. Custom Template Filters.
    URL: https://flask.palletsprojects.com/en/3.0.x/templating/#registering-filters
  Custom filters for Irish date format (DD/MM/YYYY and DD/MM/YYYY HH:MM).

Lines 202-207: Password Verification
Reference:
  - Werkzeug Documentation. Password Verification.
    URL: https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.check_password_hash
  Verifies password against stored hash during login.

Lines 216-219: User Login
Reference:
  - Flask-Login Documentation. Logging Users In.
    URL: https://flask-login.readthedocs.io/en/latest/#flask_login.login_user
  Creates user session after successful authentication.

Lines 261-264: Password Hashing
Reference:
  - Werkzeug Documentation. Password Hashing.
    URL: https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.generate_password_hash
  Hashes password before storing in database during registration.

Lines 308-311: Login Required Decorator
Reference:
  - Flask-Login Documentation. Protecting Views.
    URL: https://flask-login.readthedocs.io/en/latest/#flask_login.login_required
  Decorator to protect routes that require authentication.

Lines 471-473: FullCalendar Event Format
Reference:
  - FullCalendar.js Documentation. Event Object.
    URL: https://fullcalendar.io/docs/event-object
  FullCalendar requires ISO-8601 date strings for timed events.

Lines 573-586: PostgreSQL DATE_TRUNC Function
Reference:
  - PostgreSQL Documentation. Date/Time Functions.
    URL: https://www.postgresql.org/docs/current/functions-datetime.html#FUNCTIONS-DATETIME-TRUNC
  DATE_TRUNC groups dates by week for weekly analytics.

Lines 684-715: Threading with Timeout
Reference:
  - ChatGPT (OpenAI). Background Threading with Timeout.
    Date: 2025-11-04
    ChatGPT suggested a pattern using threading and queue to run the Canvas sync in 
    a background worker with a 15 second timeout. The worker thread calls the sync 
    function and reports either success or an error back through a queue. If the sync 
    exceeds the timeout, the system aborts the operation, records an error, and 
    displays a warning to the user instead of blocking the request.
  - Python Documentation. threading Module.
    URL: https://docs.python.org/3/library/threading.html
  - Python Documentation. queue Module.
    URL: https://docs.python.org/3/library/queue.html
  Using threading to run calendar sync in background so page doesn't hang.
  Queue used to pass results back from worker thread. Timeout prevents 
  indefinite hanging.

Lines 91-101: ISO Date Parsing in Template Filters
Reference:
  - ChatGPT (OpenAI). ISO Date Parsing with Timezone Handling.
    Date: 2025-10-12
    Prompt: "I'm getting ISO date strings from a database that sometimes have 'Z' for 
    UTC timezone. Python's fromisoformat() doesn't accept 'Z', it needs '+00:00'. Can 
    you show me how to safely parse these ISO strings and handle the timezone conversion?"
    ChatGPT provided the pattern for replacing 'Z' with '+00:00' before parsing ISO 
    date strings. Used in both irish_date and irish_datetime template filters.

Lines 402-425: Calendar Event Time Boundary Handling
Reference:
  - ChatGPT (OpenAI). Calendar Event Time Boundary Handling.
    Date: 2025-11-04
    Prompt: "Canvas sometimes gives a due_at timestamp or just a due_date. Can you 
    show me how to safely convert either one into a start and end time in ISO format 
    for my calendar view?"
    ChatGPT provided a helper block to convert Canvas assignment due information 
    into calendar event start and end timestamps. When due_at (a full datetime) is 
    available, it is used as the event start, with an end time five minutes later and 
    clamped to the end of the same day. If only a due_date is available, the code 
    treats it as an all-day event. This ensures every assignment can be plotted on the 
    calendar, even when Canvas only supplies date-level precision.

Lines 579-589: Data Extraction with Generator Expressions
Reference:
  - ChatGPT (OpenAI). Data Extraction with Generator Expressions.
    Date: 2025-10-18
    Prompt: "I have a list of dictionaries with 'status' and 'count' keys. I need to 
    extract counts for specific statuses (completed, in_progress, pending) and default 
    to 0 if not found. Can you show me how to use next() with generator expressions and 
    default values?"
    ChatGPT provided the pattern using next() with generator expressions to extract 
    values from a list of dictionaries, with default values if the status is not found.

Lines 608-624: Analytics SQL with Conditional Aggregation
Reference:
  - ChatGPT (OpenAI). Analytics SQL with Conditional Aggregation.
    Date: 2025-10-18
    Prompt: "I need SQL queries for analytics in PostgreSQL. I need to count completed 
    tasks that were on-time (completed_at <= due_date) vs late. Can you provide the SQL 
    with proper CASE WHEN statements for conditional counting?"
    ChatGPT provided the SQL query using CASE WHEN for conditional aggregation to 
    distinguish between on-time and late completions.

Lines 632-653: Module Performance Analytics with NULLIF
Reference:
  - ChatGPT (OpenAI). Module Performance Analytics with NULLIF.
    Date: 2025-10-18
    Prompt: "I need to calculate completion rates per module using LEFT JOIN in 
    PostgreSQL, handling division by zero with NULLIF. The query should group by module 
    and only show modules that have tasks. Can you provide the SQL with proper NULLIF 
    for safe division?"
    ChatGPT provided the SQL query with LEFT JOIN, NULLIF to prevent division by zero, 
    and HAVING clause to filter modules with tasks.

Lines 735-769: Text Summarization Algorithm
Reference:
  - ChatGPT (OpenAI). Text Summarization Algorithm.
    Date: 2025-11-14
    Prompt: "I need a function that summarizes text to a maximum length by extracting complete 
    sentences. It should split text into sentences, add sentences until the max length is 
    reached, and handle edge cases like single very long sentences. Can you help me write this?"
    ChatGPT provided the algorithm for summarizing text by sentence extraction. It uses regex 
    to split sentences, accumulates sentences until the max length, handles single long 
    sentences, and ensures the summary doesn't cut words mid-sentence.

Lines 781-808: Prompt Text Sanitization
Reference:
  - ChatGPT (OpenAI). Prompt Text Sanitization.
    Date: 2025-11-14
    Prompt: "I need to sanitize assignment briefs before sending them to AI. I need to remove 
    sensitive words (plagiarism, harassment, etc.) and replace them with safer alternatives. 
    Also strip content after certain markers like 'Rubric:' or 'Required Format:'. Can you 
    help me write this sanitization function?"
    ChatGPT provided the text sanitization logic that replaces sensitive keywords, strips 
    content after specific markers, and calls the summarization function to keep text concise. 
    This prevents AI safety blocks and keeps prompts focused.

Lines 820-880: Multi-Format File Text Extraction
Reference:
  - ChatGPT (OpenAI). Multi-Format File Text Extraction.
    Date: 2025-11-14
    Prompt: "I need a function that extracts text from multiple file formats: plain text (.txt, 
    .md), DOCX files, and PDF files. It should handle encoding issues, extract text from DOCX 
    paragraphs and tables, and extract text from PDF pages. Can you help me write this with 
    proper error handling?"
    ChatGPT provided the multi-format text extraction logic with encoding fallbacks for text 
    files, paragraph and table extraction for DOCX files, and page-by-page extraction for PDFs. 
    Includes comprehensive error handling and validation.

Lines 904-956: Calendar Context Building for AI Prompts
Reference:
  - ChatGPT (OpenAI). Calendar Context Building for AI Prompts.
    Date: 2025-11-14
    Prompt: "I need to build a summary of a student's upcoming assignments and calendar 
    events to include in the AI prompt. This helps the AI suggest realistic timing for new 
    task breakdowns that don't conflict with existing commitments. Can you help me format 
    this context information?"
    ChatGPT provided the structure for building a context summary that includes upcoming 
    assignments with due dates, weights, and status, plus calendar events with locations. 
    This context is included in AI prompts to enable smarter scheduling suggestions.

Lines 977-992: Datetime Rounding to Nearest Half Hour
Reference:
  - ChatGPT (OpenAI). Datetime Rounding to Nearest Half Hour.
    Date: 2025-11-14
    Prompt: "I need a function that rounds a datetime to the nearest hour or 30-minute mark, 
    always rounding up. So 2:15 PM becomes 2:30 PM, 2:45 PM becomes 3:00 PM. Can you help me 
    write this rounding logic?"
    ChatGPT provided the datetime rounding algorithm that rounds to the nearest hour or 
    30-minute mark, always rounding up. This ensures calendar events start at clean time 
    boundaries (hour or half-hour marks).

Lines 1020-1033: Interval Arithmetic for Time Slots
Reference:
  - ChatGPT (OpenAI). Interval Arithmetic for Time Slots.
    Date: 2025-11-14
    Prompt: "I need a function that subtracts a busy time interval from a list of free 
    time segments. If a busy interval overlaps with a free segment, I need to split the 
    free segment into parts that don't overlap. Can you help me write this interval 
    subtraction logic?"
    ChatGPT provided the algorithm for subtracting busy intervals from free time segments 
    by checking overlap conditions and splitting segments accordingly. This is used to 
    find available time slots after accounting for existing calendar events.

Lines 1044-1090: Free Time Slot Generation Algorithm
Reference:
  - ChatGPT (OpenAI). Free Time Slot Generation Algorithm.
    Date: 2025-11-14
    Prompt: "I need to find free time slots in a student's calendar. I have a working 
    day window (9 AM to 9 PM), existing calendar events (busy intervals), and I need to 
    find all available 30+ minute slots over the next few weeks. Can you help me write 
    an algorithm that subtracts busy intervals from working hours and returns free slots?"
    ChatGPT provided the algorithm for generating free time slots by defining a working 
    window (9 AM - 9 PM), iterating through each day, and subtracting busy intervals from 
    each day's working hours using interval arithmetic. This ensures AI-generated tasks 
    can be scheduled in available time.

Lines 1130-1190: Task Lookup and Creation Pattern
Reference:
  - ChatGPT (OpenAI). Task Lookup and Creation Pattern.
    Date: 2025-11-14
    Prompt: "I need a function that looks up an existing task by title and module, and if 
    not found, creates a new task. It should handle both tasks with and without modules, 
    parse due dates from strings, and set default due times. Can you help me write this?"
    ChatGPT provided the lookup-or-create pattern for tasks. It searches by title and module 
    (or NULL module), handles date parsing with multiple formats, sets default due times, and 
    returns the task ID for linking subtasks.

Lines 1251-1300: Natural Language Date/Time Parsing
Reference:
  - ChatGPT (OpenAI). Natural Language Date/Time Parsing.
    Date: 2025-11-14
    Prompt: "The AI sometimes returns time hints like 'Tuesday evening', 'next week 
    afternoon', or ISO dates. I need a function that can parse these natural language 
    hints and convert them to datetime objects. It should handle multiple date formats 
    and extract time-of-day hints (morning, afternoon, evening, night) to set appropriate 
    hours."
    ChatGPT provided the parsing logic for multiple date formats and natural language 
    time-of-day hints. The function tries various date formats, extracts time-of-day 
    keywords to set hours, and falls back to ISO parsing. This allows the scheduling 
    system to respect AI-suggested preferred times.

Lines 1293-1470: Even Task Distribution Scheduling Algorithm
Reference:
  - ChatGPT (OpenAI). Even Task Distribution Scheduling Algorithm.
    Date: 2025-11-14
    Prompt: "I need to schedule AI-generated subtasks into calendar slots. The AI suggests 
    preferred times, but I need to distribute tasks evenly across available time until the 
    deadline. If a task can't fit in the preferred time slot, find the nearest available 
    slot. Tasks should be spread out evenly, not clustered on one day. Can you help me 
    write this scheduling algorithm?"
    ChatGPT provided the algorithm for distributing subtasks evenly across available time 
    slots. It prioritizes AI-suggested times when possible, but evenly spreads tasks across 
    the available window until the deadline. The algorithm uses slot consumption to prevent 
    double-booking and finds nearest available slots when preferred times are unavailable.

Lines 1440-1465: Calendar Event Overlap Detection
Reference:
  - ChatGPT (OpenAI). Calendar Event Overlap Detection.
    Date: 2025-11-14
    Prompt: "I need to check if a new calendar event would overlap with existing events, 
    including a buffer time (30 minutes) between events. The overlap check should account 
    for both the new event's time and the buffer. Can you help me write this overlap 
    detection logic?"
    ChatGPT provided the overlap detection algorithm that checks if a new event (with buffer) 
    overlaps with existing events. It compares start and end times with buffers to prevent 
    double-booking and ensures events have proper spacing.

Lines 526-588: Task Update Form Validation and Date Parsing
Reference:
  - ChatGPT (OpenAI). Task Update Form Validation and Date Parsing.
    Date: 2025-11-18
    Prompt: "I need to handle form submission for updating task details. The form can have 
    title, description, weight, due_date (date only), and due_at (datetime). I need to 
    validate the title is required, parse dates with multiple formats, handle timezone 
    conversions, and update the database. Can you help me write this validation and parsing 
    logic?"
    ChatGPT provided the form validation and date parsing logic that handles multiple date 
    formats, timezone conversions, validates required fields, and safely updates the database 
    with proper error handling.

Lines 478-569: Dashboard Grade Formatting (Canvas Scores)
Reference:
  - ChatGPT (OpenAI). Canvas Grade Display Formatting.
    Date: 2026-01-22
    Prompt: "I want to show Canvas grades on the dashboard as score/possible and percentage,
    with safe handling for missing values. Can you suggest a robust formatting pattern?"
  ChatGPT provided the grade formatting logic so the UI shows score/possible with a
  percentage and safe fallbacks when values are missing.

Lines 455-524: Daily Summary Auto-Send (Once Per Day)
Reference:
  - ChatGPT (OpenAI). Daily Summary Email Trigger Pattern.
    Date: 2026-01-22
    Prompt: "I need to send a daily summary email once per day when the user loads the dashboard.
    Can you help me design a last-sent check and update status flags?"
  ChatGPT provided the daily summary trigger pattern and the last‑sent/status updates.

Lines 1132-1205: SMTP Email Sender + Summary Buckets
Reference:
  - ChatGPT (OpenAI). SMTP Sender + Summary Grouping.
    Date: 2026-01-22
    Prompt: "Can you help me build a simple SMTP email sender and a daily summary email
    that groups tasks into overdue, due in 24h, and due in 72h?"
  ChatGPT provided the SMTP pattern and the summary grouping format.

SMTP Fail-Fast Timeout Guard
Reference:
  - ChatGPT (OpenAI). SMTP Fail-Fast Timeout Guard.
    Date: 2026-02-12
    Prompt: "My Flask request can timeout when SMTP host is slow/unreachable. I need a
    fail-fast timeout strategy so email attempts return quickly instead of blocking
    the web worker. Can you provide a practical pattern?"
    ChatGPT recommended using a short, bounded timeout (2–8s, default 4s) for all SMTP
    socket operations. Used in _send_reminder_email() to prevent SMTP from blocking
    Gunicorn workers on hosted environments like Render.

Lines 883-1007: AI Assignment Review Flow
Reference:
  - ChatGPT (OpenAI). Assignment Review Orchestration.
    Date: 2026-01-22
    Prompt: "I want a flow that accepts a file or text input, extracts content, sends it to
    an AI reviewer, and stores feedback + score. Can you outline a clean end-to-end flow?"
  ChatGPT provided the review flow and error handling pattern around file inputs.

Lines 3041-3123: Study Planner Prompt Context
Reference:
  - ChatGPT (OpenAI). Study Planner Prompt Context.
    Date: 2026-01-22
    Prompt: "I need to summarize tasks and progress into a compact prompt for study
    recommendations. Can you help structure the summary text?"
  ChatGPT provided the tasks/progress summary structure for the study planner prompt.

Lines 3126-3355: Course Bot Upload + Q&A Flow
Reference:
  - ChatGPT (OpenAI). Course Bot Flow with Sources.
    Date: 2026-01-22
    Prompt: "I want a course bot that stores uploaded materials and answers questions using
    only those sources. Can you outline the flow and storage steps?"
  ChatGPT provided the upload + Q&A orchestration with citations stored in history.

Lines 695-850: Active Semester View with Date Filtering and Event Grouping
Reference:
  - ChatGPT (OpenAI). Semester View with Event Grouping.
    Date: 2026-02-03
    Prompt: "I need a semester overview page that shows tasks, events, reviews, and 
    microtasks within a configurable date range. Events should be grouped by title and 
    time to show recurring lectures as a single entry with a count. The date range should 
    be saveable in session. Can you help me build this view?"
    ChatGPT provided the date filtering logic with session persistence, the SQL queries 
    for fetching tasks/events/reviews within the date window, and the event grouping 
    algorithm that consolidates recurring lectures by title + time into single entries 
    with occurrence counts.

Lines 1447-1610: IMAP Email Fetching for Lecturer Replies
Reference:
  - ChatGPT (OpenAI). IMAP Email Fetching with SSL.
    Date: 2026-02-03
    Prompt: "I need a function that connects to an IMAP email server, searches for emails 
    from specific sender addresses (lecturers), parses the email content (subject, body, 
    date), and stores them in a database. It should handle SSL connections, email header 
    decoding, and avoid duplicate messages using message-id."
    ChatGPT provided the IMAP connection pattern using imaplib, email parsing with the 
    email module, header decoding with decode_header, and duplicate prevention using 
    message-id as a unique constraint.
  - Python Documentation. imaplib Module.
    URL: https://docs.python.org/3/library/imaplib.html
  - Python Documentation. email Module.
    URL: https://docs.python.org/3/library/email.html

Lines 2981-3055: Calendar Recurring Events Pattern Detection
Reference:
  - ChatGPT (OpenAI). Recurring Event Pattern Detection Algorithm.
    Date: 2026-02-03
    Prompt: "I have calendar events that repeat weekly (like lectures) but aren't always 
    marked as recurring in the database. I need to automatically detect recurring patterns 
    by grouping events with the same title, same day of week, and same time. Events that 
    appear 2+ times with this pattern should be grouped and displayed as a single recurring 
    entry with a count."
    ChatGPT provided the pattern detection algorithm using a dictionary to group events 
    by a composite key (title + day_of_week + time), then separating groups with 2+ 
    occurrences as recurring vs single events.

Lines 4186-4223: Reviews History Paginated View
Reference:
  - ChatGPT (OpenAI). Paginated History View Pattern.
    Date: 2026-02-03
    Prompt: "I need a paginated view for assignment review history. It should show reviews 
    with their scores, feedback, linked task details, and support pagination with page 
    numbers and offset calculations."
    ChatGPT provided the pagination pattern with COUNT query for totals, LIMIT/OFFSET 
    for paging, and the SQL query joining assignment_reviews with tasks and modules for 
    display context.

Lines 4226-4269: Subtasks History Paginated View
Reference:
  - ChatGPT (OpenAI). Paginated History View Pattern.
    Date: 2026-02-03
    Prompt: "I need a paginated view for AI-generated subtasks/microtasks. It should show 
    subtasks with their parent task, completion status, estimated hours, and support 
    pagination."
    ChatGPT provided the pagination pattern with COUNT query, LIMIT/OFFSET for paging, 
    and the SQL query joining subtasks with tasks and modules for display context.

Lines 4272-4312: Lecturer Messages History Paginated View
Reference:
  - ChatGPT (OpenAI). Paginated Sent Messages View Pattern.
    Date: 2026-02-03
    Prompt: "I need a paginated view for messages sent to lecturers via the Quick Connect 
    feature. It should show the message subject, lecturer name, sent timestamp, and email 
    delivery status."
    ChatGPT provided the pagination pattern with COUNT query, LIMIT/OFFSET for paging, 
    and the SQL query joining lecturer_messages with lecturers for display context.

Lines 4315-4368: Lecturer Replies Inbox View
Reference:
  - ChatGPT (OpenAI). Email Inbox View with Read/Unread Status.
    Date: 2026-02-03
    Prompt: "I need an inbox view for lecturer email replies. It should show unread count, 
    display replies with sender info, subject, body preview, received date, and support 
    marking as read and pagination."
    ChatGPT provided the inbox view pattern with unread count query, pagination, and the 
    SQL query for fetching replies with lecturer info.

Lines 4456-4555: Contact Lecturer Quick Connect Route
Reference:
  - ChatGPT (OpenAI). Quick Connect Lecturer Email Flow.
    Date: 2026-01-23
    Prompt: "I need a simple flow that lets students pick a lecturer, enter a subject
    and message, and send it via SMTP with validation. Can you outline the pattern?"
    ChatGPT provided the validation and send flow. The route handles two actions:
    "generate" to use AI to draft a professional email, and "send" to send the message
    via SMTP. It validates lecturer exists, adds the student signature, records the 
    message in the database with delivery status, and handles errors gracefully.

Lines 4777-4799: Add Lecturer Contact Route
Reference:
  - ChatGPT (OpenAI). Simple Form Handler Pattern.
    Date: 2026-01-23
    Prompt: "I need a route to add lecturer contacts from a form. It should validate 
    name and email are provided, normalize the module code to uppercase, and insert 
    into the lecturers table."
    ChatGPT provided the form validation and database insert pattern for adding 
    lecturer contacts.

Lines 49-118: Activity Logging Middleware
Reference:
  - ChatGPT (OpenAI). Activity Logging Middleware.
    Date: 2026-02-04
    Prompt: "I need to log all authenticated user actions with timestamps. It should
    capture method, path, endpoint, status code, duration, IP, and user agent, and
    store them in a database table. Can you provide a clean before_request/after_request
    pattern in Flask?"
    ChatGPT provided the before_request/after_request pattern to capture timing and
    persist request metadata for authenticated users.

Lines 808-870: Semester Activity Log Queries
Reference:
  - ChatGPT (OpenAI). Activity Log Query Pattern.
    Date: 2026-02-04
    Prompt: "I need to show activity logs in a semester view. Provide SQL to count
    activity in a date range and fetch the latest entries for display."
    ChatGPT provided the COUNT and SELECT queries with date-range filtering and
    limit ordering for activity logs.

Lines 120-179: Activity Log Title Mapping
Reference:
  - ChatGPT (OpenAI). Activity Log Title Mapping.
    Date: 2026-02-04
    Prompt: "I want activity logs to show friendly titles instead of raw paths.
    Can you map endpoints/paths to readable labels and add action verbs by method?"
    ChatGPT provided the mapping approach with method-based verbs.

Per-Module Dashboard Routes (US 17)
Reference:
  - ChatGPT (OpenAI). Per-Module Dashboard Routes.
    Date: 2026-02-10
    Prompt: "I need a modules overview page showing all modules with task count,
    completion %, and average grade, plus a detail page for a single module showing
    all tasks, grade breakdown, and progress chart. Can you provide the Flask routes
    and SQL queries?"
    ChatGPT provided the route structure and SQL queries used in modules_overview()
    and module_detail() in main.py.

Analytics Visualisation Queries (Daily Density + Cumulative Progress)
Reference:
  - ChatGPT (OpenAI). Analytics Visualisation Queries.
    Date: 2026-02-10
    Prompt: "I need extra analytics queries for new Chart.js visuals:
    daily task due counts (workload heatmap), cumulative completed tasks
    over time (progress line), and per-module completion % for a radar chart."
    ChatGPT provided the PostgreSQL queries for daily task density, cumulative
    completions using window functions (SUM OVER), and the Chart.js radar,
    bar, and line chart configurations for the analytics dashboard.

Analytics Data Densification + Chart Date Safety Improvements
Reference:
  - ChatGPT (OpenAI). Dense Time-Series Chart Preparation.
    Date: 2026-02-10
    Prompt: "My workload chart only shows dates that have tasks. I want to
    render a stable 30-day timeline including zero-value days so the chart
    is easier to read. Can you show a Python pattern to densify SQL rows?"
    ChatGPT provided the dictionary-lookup + fixed-range expansion approach
    used to fill missing dates with zero counts before sending chart data.
  - ChatGPT (OpenAI). Safe Local Date Parsing for Chart Labels.
    Date: 2026-02-10
    Prompt: "My Chart.js labels can shift by one day because JS Date parses
    YYYY-MM-DD as UTC in some environments. Can you provide a helper that
    parses ISO date-only strings in local time and formats them for charts?"
    ChatGPT provided the local date parsing helper pattern used in
    analytics.html to avoid timezone-shifted labels.

Voice-to-Task Capture (US 19)
Reference:
  - ChatGPT (OpenAI). Voice Transcript Parsing for Task Forms.
    Date: 2026-02-10
    Prompt: "I need a Flask endpoint to parse spoken task text into structured
    fields (title, module code, due date, due time, weight, status) for
    auto-filling a form. Can you provide a robust parsing pattern with
    fallback defaults?"
    ChatGPT provided the Flask helper + endpoint structure used in main.py,
    including regex/date parsing and module matching fallbacks.
  - ChatGPT (OpenAI). Voice-to-Task Frontend Flow.
    Date: 2026-02-10
    Prompt: "I need browser-side voice capture (Web Speech API) that sends
    transcript to a Flask endpoint and auto-fills task form fields. Can you
    provide a simple, resilient JS flow with start/stop, parse request, and
    user feedback?"
    ChatGPT provided the Web Speech API + fetch/autofill interaction pattern
    used in add_data.html.
  - ChatGPT (OpenAI). Voice Command Intent Router + Action Handlers.
    Date: 2026-02-11
    Prompt: "I already have voice-to-task autofill. I now need one endpoint
    that detects voice intents for (1) dashboard query ('what is due this week/
    any overdue'), (2) recurring calendar event creation, and (3) microtask
    generation from a spoken command. Can you provide a safe Flask pattern with
    helper functions, regex parsing, DB inserts, and structured JSON responses?"
    ChatGPT provided the intent-router + helper pattern used in main.py
    (`/voice-command`) for dashboard querying, recurring event creation, and
    microtask generation.
  - ChatGPT (OpenAI). Voice Command API Response Contract.
    Date: 2026-02-11
    Prompt: "For multiple voice actions, I need a single Flask endpoint that
    returns consistent JSON (`ok`, `intent`, `message`, `data`) and gracefully
    handles unknown intents and validation errors. Can you provide a clean route
    pattern?"
    ChatGPT provided the response-contract + intent dispatch pattern now used in
    `/voice-command`.
  - ChatGPT (OpenAI). Reusable Voice Command Widget (Frontend).
    Date: 2026-02-11
    Prompt: "I need a lightweight browser voice widget that records speech and
    sends transcript to a Flask /voice-command endpoint, then renders result
    feedback. Can you provide a reusable JS pattern?"
    ChatGPT provided the start/stop + fetch/render pattern used in
    `index.html`, `calendar.html`, and `subtasks_history.html`.
  - ChatGPT (OpenAI). Voice Task Lifecycle Command Handlers.
    Date: 2026-02-18
    Prompt: "Extend voice commands to handle task lifecycle actions in Flask:
    mark task status (done/in-progress/pending), reschedule due date/time, and
    update weighting/priority. I need task title extraction + fuzzy matching and
    safe DB update patterns. Can you provide helper functions and intent hooks?"
    ChatGPT provided the normalization + task-matching helper pattern used in
    `main.py` for new voice lifecycle intents.
  - ChatGPT (OpenAI). Voice Navigation Intent Routing.
    Date: 2026-02-18
    Prompt: "I want voice commands to navigate pages (open modules, calendar,
    analytics) and also open specific module detail pages when a module code is
    spoken (e.g., 'open module IS4408'). Can you provide a Flask helper that
    returns redirect targets for the frontend?"
    ChatGPT provided the destination mapping + module-code routing pattern used
    in `main.py` and frontend voice widgets.

Group Workspace (US 21)
Reference:
  - ChatGPT (OpenAI). Group Workspace Backend Flow.
    Date: 2026-02-11
    Prompt: "I need a group project workspace in Flask where students can create
    projects, add members, assign tasks manually or with AI, track progress, and
    email members their assigned items. Can you provide a robust route/action
    pattern with ownership checks, safe parsing, and summary metrics?"
    ChatGPT provided the backend helper + route architecture used in main.py for
    `/group-workspace`, including task delegation, progress tracking, and email
    actions.
  - ChatGPT (OpenAI). Group Workspace SQL Schema.
    Date: 2026-02-11
    Prompt: "I need PostgreSQL tables for a group project workspace: projects
    owned by a student, members per project, and delegated tasks with
    status/progress for tracking. Can you draft a practical schema with indexes
    and safe constraints?"
    ChatGPT provided the schema pattern used in
    `scripts/add_group_workspace_tables.sql`.
  - ChatGPT (OpenAI). Invite Token Member Portal Pattern.
    Date: 2026-02-11
    Prompt: "I need invited group members to open a secure token link, accept
    the invite, and update only tasks assigned to them without full account
    login. Can you provide a safe Flask route flow?"
    ChatGPT provided the invite-token validation and restricted task-update flow
    used in `/group-workspace/invite/<invite_token>`.
  - ChatGPT (OpenAI). Group Workspace Collaboration Extensions.
    Date: 2026-02-11
    Prompt: "Extend the group workspace with member invite resend emails,
    project milestones, and per-task file attachments (upload/delete) while
    keeping action handling in a single Flask route. Can you provide a clean
    branching pattern?"
    ChatGPT provided the extension branch pattern used in main.py for invite
    resend, milestone actions, and task attachment actions.
  - ChatGPT (OpenAI). Secure Project File Download Guard.
    Date: 2026-02-11
    Prompt: "I need a secure Flask download route for project-level files where
    only the project owner can access downloads. Can you provide a safe
    ownership check and send_file pattern?"
    ChatGPT provided the owner-check + safe send_file pattern used in
    `/group-workspace/project-files/<file_id>/download`.
  - ChatGPT (OpenAI). Project Team Messaging Thread Flow.
    Date: 2026-02-11
    Prompt: "I need a project-level team thread in Flask where the project owner
    can post updates/comments and render messages newest-last in the workspace.
    Can you provide a simple insert + fetch pattern with validation?"
    ChatGPT provided the insertion/ordering pattern used for
    `group_project_messages` in `/group-workspace`.
  - ChatGPT (OpenAI). Secure Owner-Only File Download Route.
    Date: 2026-02-11
    Prompt: "I need a Flask download endpoint for group-task attachments where
    only the project owner can download files. Can you provide a secure pattern
    with ownership checks and safe send_file handling?"
    ChatGPT provided the ownership-check + send_file route pattern used in
    `/group-workspace/files/<file_id>/download`.
  - ChatGPT (OpenAI). Group Workspace Incremental Migration.
    Date: 2026-02-11
    Prompt: "I already created initial group workspace tables. I now need a safe
    follow-up migration to add invite token support, milestones, and task
    attachments without breaking existing data. Can you provide ALTER/CREATE
    statements with IF NOT EXISTS patterns?"
    ChatGPT provided the incremental migration approach used in
    `scripts/add_group_workspace_extras.sql`.
  - ChatGPT (OpenAI). Group Workspace Member-Safe Access Mode.
    Date: 2026-02-18
    Prompt: "I need accepted group members to use /group-workspace safely:
    see assigned tasks, update only their own progress, and read team thread,
    while owner-only project controls remain restricted. Can you provide
    backend guard + template branching patterns?"
    ChatGPT provided the member-access guard + member-view branching pattern
    used in `main.py` and `group_workspace.html`.
  - ChatGPT (OpenAI). Group Workspace AI Brief File Ingestion.
    Date: 2026-02-18
    Prompt: "In the group workspace AI breakdown form, I want users to optionally
    upload a brief file (txt/md/docx/pdf) and combine it with typed brief text
    before generating tasks. Can you provide a safe Flask parsing pattern with
    size/type validation and sanitization?"
    ChatGPT provided the upload-parse-combine pattern adapted in
    `group_workspace` AI task generation.
  - ChatGPT (OpenAI). Bounded AI Worker Timeout in Flask.
    Date: 2026-02-18
    Prompt: "My hosted Flask request can time out when AI generation is
    slow/cold-starting. I need a thread+queue timeout guard so UI gets a
    controlled warning instead of a worker crash. Can you provide a pattern?"
    ChatGPT provided the background-worker timeout pattern used in
    `group_workspace` AI task generation.
  - ChatGPT (OpenAI). Prompt Bounding for Hosted AI Latency.
    Date: 2026-02-18
    Prompt: "My hosted AI request still times out with long user briefs. Can you
    suggest a bounded-summary approach and timeout tuning that improves
    completion reliability without removing functionality?"
    ChatGPT provided the brief summarization + configurable timeout approach used
    in group AI generation.
  - ChatGPT (OpenAI). Group Report Section Split Heuristic.
    Date: 2026-02-18
    Prompt: "My AI sometimes creates a generic task like 'Draft Individual
    Sections' for group reports. I need a deterministic fallback to expand that
    into section-specific tasks assigned across members. Can you suggest a clean
    post-processing pattern in Python?"
    ChatGPT provided the post-processing expansion pattern used in
    `group_workspace` AI generation flow.

Lecture Attendance + Health Score (Iteration 5)
Reference:
  - ChatGPT (OpenAI). Attendance Toggle Upsert Pattern.
    Date: 2026-02-11
    Prompt: "I need a Flask route that toggles lecture attendance for a given
    calendar event (event belongs to current user). It should insert if missing
    and flip attended true/false if existing."
    ChatGPT provided the ownership-check + insert/update toggle flow used in
    `/events/<event_id>/attendance-toggle`.
  - ChatGPT (OpenAI). Lecture Attendance Analytics Queries.
    Date: 2026-02-11
    Prompt: "I need SQL for lecture attendance analytics: overall attendance %,
    module-level attendance %, and a recent lecture session list with attended
    flags for clickable toggles. Can you provide PostgreSQL queries?"
    ChatGPT provided the query patterns used in `analytics()` and module routes.
  - ChatGPT (OpenAI). Module Fallback Matching from Event Title.
    Date: 2026-02-11
    Prompt: "Some Canvas lecture events may not have module_id populated, but
    the module code appears in the event title (e.g., IS4408 ...). I need SQL
    fallback logic so module attendance still aggregates correctly. Can you
    provide a safe PostgreSQL pattern?"
    ChatGPT provided the regex extraction fallback used in module attendance
    subqueries.
  - ChatGPT (OpenAI). Weighted Health Score Calculation.
    Date: 2026-02-11
    Prompt: "I need a student 'health score' that combines completion rate,
    on-time completion percentage, and lecture attendance. Some components may be
    missing. Can you provide a weighted scoring pattern that renormalizes
    weights?"
    ChatGPT provided the weighted-average normalization pattern used in
    `_calculate_health_score()`.
  - ChatGPT (OpenAI). Lecture Attendance Tracking Schema.
    Date: 2026-02-11
    Prompt: "I need a PostgreSQL table to track lecture attendance per student
    per calendar event, with an attended flag and timestamp. It should prevent
    duplicate attendance rows for the same student/event and include useful
    indexes."
    ChatGPT provided the schema pattern used in
    `scripts/add_lecture_attendance_table.sql`.
  - ChatGPT (OpenAI). Semester Group Progress + Attendance Aggregation.
    Date: 2026-02-11
    Prompt: "In a semester overview page, I need SQL summaries for (1) group
    project progress and (2) lecture attendance stats constrained to the
    selected date range. Can you provide practical aggregation queries and safe
    defaults?"
    ChatGPT provided the aggregation/query pattern used in `active_semester()`.
  - ChatGPT (OpenAI). Resend API Email Sender Fallback.
    Date: 2026-02-12
    Prompt: "I need a Flask email helper that sends via Resend API first when
    RESEND_API_KEY is configured, then falls back to SMTP. It should return an
    error string instead of raising and use request timeouts."
    ChatGPT provided the provider-priority + graceful-fallback pattern used in
    `_send_reminder_email()`.

ICS Calendar Export Route
Reference:
  - ChatGPT (OpenAI). ICS Calendar Export with icalendar Library.
    Date: 2026-02-10
    Prompt: "I need a Flask route that generates an ICS feed from my tasks
    (due dates) and calendar events tables so students can subscribe in
    Google Calendar or Outlook. Can you show me how to build VEVENT entries
    with the icalendar library and return the file as a download?"
    ChatGPT provided the route pattern, VEVENT construction with DTSTART,
    DTEND, SUMMARY, UID, DESCRIPTION fields, timezone handling, and the
    Content-Type/Content-Disposition headers for ICS file download.
  - icalendar Library Documentation.
    URL: https://icalendar.readthedocs.io/
  Used for generating standards-compliant ICS calendar files.

Lines 871-950: Activity History Page (Pagination)
Reference:
  - ChatGPT (OpenAI). Activity History Pagination.
    Date: 2026-02-04
    Prompt: "I need a paginated activity log page. It should count total rows,
    fetch a page of recent activity, and display friendly titles."
    ChatGPT provided the pagination flow and query pattern.

================================================================================
FILE: canvas_sync.py
================================================================================

Lines 6-9: canvasapi Library
Reference:
  - canvasapi Library (UCF Open). Python wrapper for Canvas LMS API.
    URL: https://github.com/ucfopen/canvasapi
  Python wrapper for Canvas LMS API. Used for fetching courses and assignments.

Lines 14-17: Requests Library
Reference:
  - Requests Library. HTTP for Humans.
    URL: https://requests.readthedocs.io/
  Used for direct Canvas REST API calls (calendar events endpoint) since 
  canvasapi library doesn't support calendar events.

Lines 46-51: Canvas Connection
Reference:
  - canvasapi Documentation. Getting Started.
    URL: https://canvasapi.readthedocs.io/en/stable/getting_started.html
  Connection pattern from canvasapi library examples for connecting to Canvas
  and getting current user/courses.

Lines 79-90: Canvas Assignment Buckets
Reference:
  - Canvas API Documentation. List Assignments.
    URL: https://canvas.instructure.com/doc/api/assignments.html#method.assignments.index
  Using bucket parameter to get upcoming assignments, then filtering past 30 
  days to limit data fetched.

Lines 98-107: ISO-8601 Date Parsing
Reference:
  - Python datetime Documentation. fromisoformat.
    URL: https://docs.python.org/3/library/datetime.html#datetime.datetime.fromisoformat
  Parsing ISO-8601 date strings from Canvas API. Handles timezone conversion.

Lines 59-84: Module Matching and Auto-Creation
Reference:
  - ChatGPT (OpenAI). Module Matching and Auto-Creation.
    Date: 2025-10-20
    Prompt: "When syncing Canvas courses, I need to match them to modules in my 
    database. If a module doesn't exist, I should create it. If the course_code is 
    missing, I should generate a fallback. Can you show me the pattern for checking 
    existence and creating if needed?"
    ChatGPT provided the upsert pattern for modules with fallback course code generation.

Lines 79-97: Date Filtering with List Comprehension
Reference:
  - ChatGPT (OpenAI). Date Filtering with List Comprehension.
    Date: 2025-10-22
    Prompt: "I'm fetching Canvas assignments using 'upcoming' and 'past' buckets. I 
    need to filter the past assignments to only include those from the last 30 days. 
    Can you show me how to parse ISO dates, compare them to a cutoff date, and filter 
    using a list comprehension?"
    ChatGPT provided the pattern for filtering past assignments by date using list 
    comprehension with ISO date parsing and comparison.

Lines 109-158: Database Upsert Pattern for Assignments
Reference:
  - ChatGPT (OpenAI). Database Upsert Pattern for Assignments.
    Date: 2025-11-04
    ChatGPT provided pattern for checking if assignment exists, then updating or 
    inserting. This prevents duplicates when syncing multiple times.

Lines 223-259: Canvas Calendar Events Pagination
Reference:
  - ChatGPT (OpenAI). Canvas API Pagination with Link Header.
    Date: 2025-11-04
    Prompt: "How can I fetch all Canvas API events or assignments when the API 
    response is paginated? Can you give me Python code that loops through each page 
    using the Link header until all results are retrieved?"
    ChatGPT provided a pagination pattern for the Canvas API that follows the Link 
    headers returned by each response. The loop repeatedly calls the API, appends JSON 
    items to the local list, and updates the request URL using the rel="next" link 
    until there are no more pages or a maximum page limit is reached. This ensures that 
    all relevant Canvas events are fetched without manually constructing next-page URLs.
    Changes Made: Adapted to handle case-insensitive headers, added timeout and max 
    page limit, integrated with Canvas calendar events endpoint.
  - Canvas API Documentation. Calendar Events.
    URL: https://canvas.instructure.com/doc/api/calendar_events.html#method.calendar_events.index
  - Canvas API Documentation. Pagination.
    URL: https://canvas.instructure.com/doc/api/file.pagination.html


Lines 278-294: Date/Time Normalization
Reference:
  - ChatGPT (OpenAI). Date/Time Parsing and Normalization.
    Date: 2025-11-04
    Prompt: "Sometimes Canvas events don't have an end time. Can you give me Python 
    code that checks the start and end times, and if the end is missing or earlier than 
    the start, sets it one hour later automatically?"
    ChatGPT provided a guard block around event timestamps to guarantee that each event 
    has a sensible end time. The code converts ISO timestamps to datetime objects and, 
    if an event is missing an end time or has an end time earlier than its start, it 
    automatically assigns a default duration of 60 minutes. This prevents invalid time 
    ranges from breaking the calendar rendering or analytics.
  - Python datetime Documentation. ISO Format Parsing.
    URL: https://docs.python.org/3/library/datetime.html#datetime.datetime.fromisoformat

Lines 316-339: Context Code Parsing and Module Matching
Reference:
  - ChatGPT (OpenAI). Context Code Parsing and Module Matching.
    Date: 2025-10-25
    Prompt: "Canvas API returns context codes like 'course_12345' or 'user_67890'. I 
    need to extract the course ID from these strings and match them to modules in my 
    database. Can you show me how to parse the context code and handle cases where it 
    might not be a course?"
    ChatGPT provided the pattern for parsing Canvas context codes and matching to 
    modules with fallback logic.

Lines 312-352: Database Upsert Pattern for Events
Reference:
  - ChatGPT (OpenAI). Database Upsert Pattern for Events.
    Date: 2025-11-04
    Prompt: "How do I update an event if it already exists in my Supabase table, 
    or insert a new one if it doesn't? Can you show me an SQL example using Python and 
    Supabase?"
    ChatGPT provided pattern for checking if event exists, then updating or inserting.
    Changes Made: Adapted for events table with canvas_event_id for deduplication.

================================================================================
FILE: db_supabase.py
================================================================================

Lines 1-77: Database Connection Module (Supabase PostgreSQL)
Reference:
  - ChatGPT (OpenAI). SQLAlchemy Supabase Connection Setup.
    Date: 2025-10-15
    Prompt: "I'm using Supabase PostgreSQL with SQLAlchemy. Can you show me how to set up 
    a connection engine with connection pooling and health checks? I need it to work with 
    a PostgreSQL connection string from an environment variable."
    ChatGPT provided the entire database connection module including engine 
    initialization, connection management, and query functions.
  
  - ChatGPT (OpenAI). Connection Context Manager Pattern.
    Date: 2025-10-15
    Prompt: "How do I create a context manager for database connections in SQLAlchemy 
    that automatically handles connection lifecycle and ensures connections are properly 
    closed?"
    ChatGPT provided the context manager pattern for safe connection handling.
  
  - ChatGPT (OpenAI). Database Query Functions with Parameter Binding.
    Date: 2025-10-15
    Prompt: "Can you help me create a fetch_all function using SQLAlchemy that executes 
    SQL queries with parameter binding to prevent SQL injection? It should return results 
    as a list of dictionaries, and use SQLAlchemy's text() function for raw SQL."
    ChatGPT provided fetch_all and fetch_one functions with parameterized queries and 
    dictionary result mapping.
  
  - ChatGPT (OpenAI). Database Transaction Management.
    Date: 2025-10-15
    Prompt: "How do I create an execute function for INSERT/UPDATE/DELETE operations in 
    SQLAlchemy that uses transactions and parameter binding? It should use begin() for 
    automatic transaction management and bindparams() for safe parameter binding."
    ChatGPT provided the execute function with transaction management and parameter binding.
  
  Reference: SQLAlchemy Documentation . Engine Configuration.
    URL: https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
  Reference: SQLAlchemy Documentation . Connection Management.
    URL: https://docs.sqlalchemy.org/en/20/core/connections.html#using-transactions
  The entire db_supabase.py module was created with ChatGPT assistance, providing 
  a clean abstraction layer for database operations with Supabase PostgreSQL.

================================================================================
FILE: services/analytics.py
================================================================================

Lines 47-77: DateTime Normalization with Multiple Fallbacks
Reference:
  - ChatGPT (OpenAI). DateTime Normalization with Multiple Fallbacks.
    Date: 2025-11-14
    Prompt: "I need a function that normalizes due dates from database rows. The row 
    might have a due_at (datetime), a due_date (date object), or a due_date string. I 
    need to handle all these cases and convert them to a datetime with timezone info, 
    defaulting to 23:59 on the due date. Can you help me write this normalization logic?"
    ChatGPT provided the algorithm for normalizing due dates with multiple fallback 
    strategies. It handles datetime objects, date objects, and ISO date strings, ensuring 
    all are converted to a consistent datetime format with timezone info for priority 
    calculations.

Lines 80-104: Priority Calculation Algorithm
Reference:
  - ChatGPT (OpenAI). Priority Calculation Algorithm.
    Date: 2025-11-14
    Prompt: "I need a priority scoring algorithm that combines assignment weight 
    (percentage) and urgency (hours until due). High weight assignments should score 
    higher, and assignments due soon should score higher. Urgency should have diminishing 
    returns as time increases. Can you help me design this scoring formula?"
    ChatGPT provided the priority calculation algorithm that combines weight and urgency 
    components. Weight is multiplied by 2.0, and urgency uses a hyperbolic decay function 
    (48.0 / (hours/24 + 0.5)) that heavily penalizes overdue tasks (100.0) while providing 
    diminishing urgency for tasks further out. This ensures high-weight and urgent tasks 
    appear first in priority lists.

================================================================================
FILE: services/chatgpt_client.py
================================================================================

Lines 149-180: OpenAI Response Text Extraction
Reference:
  - ChatGPT (OpenAI). OpenAI Response Text Extraction.
    Date: 2025-11-14
    Prompt: "The OpenAI Responses API returns nested response objects. I need to extract 
    the text content from response.output[].content[].text. But the API structure might 
    change, so I need a fallback to response.text if the nested structure isn't available. 
    Can you help me write robust text extraction with fallbacks?"
    ChatGPT provided the text extraction logic that navigates the nested response structure 
    (response.output -> segment.content -> part.text) with fallback to direct .text 
    attribute. This handles API variations and ensures text is extracted reliably even 
    when the response format changes.

Lines 182-208: Robust JSON Parsing with Fallbacks
Reference:
  - ChatGPT (OpenAI). Robust JSON Parsing with Fallbacks.
    Date: 2025-11-14
    Prompt: "OpenAI sometimes returns JSON wrapped in markdown code fences (```json ... ```), 
    or with extra text before/after. Sometimes the JSON is malformed. I need a function that 
    strips code fences, tries to parse the full text, and if that fails, extracts just the 
    JSON fragment (content between first '{' and last '}'). Can you help me write this 
    robust JSON parser?"
    ChatGPT provided the JSON parsing logic with multiple fallback strategies. It first 
    strips markdown code fences, then attempts to parse the full payload. If that fails, 
    it extracts the JSON fragment (first '{' to last '}') and tries parsing that. This 
    handles various OpenAI response formats and ensures JSON can be extracted even from 
    responses with extra text.

Lines 244-257: JSON Fragment Extraction
Reference:
  - ChatGPT (OpenAI). JSON Fragment Extraction.
    Date: 2025-11-14
    Prompt: "If a string contains JSON mixed with other text, how can I extract just the 
    JSON portion? I need to find the first '{' and the last '}' and extract everything 
    between them. Can you show me this extraction logic?"
    ChatGPT provided the JSON fragment extraction algorithm that finds the first '{' and 
    last '}' in a string to extract the JSON content. This is used as a fallback when 
    OpenAI returns JSON embedded in explanatory text.

Lines 128-223: Assignment Review Prompt + JSON Schema
Reference:
  - ChatGPT (OpenAI). Assignment Review Prompt Design.
    Date: 2026-01-22
    Prompt: "I need a strict JSON schema for assignment feedback, strengths, weaknesses,
    and suggestions. Can you help me craft the system/user prompts?"
  ChatGPT provided the grading prompt and JSON response structure.

Lines 225-352: Course Bot Prompt + Citation Rules
Reference:
  - ChatGPT (OpenAI). Course Bot Prompt Engineering with Citations.
    Date: 2026-01-22
    Prompt: "I need a prompt for a course assistant that answers only from provided sources
    and returns citations. Can you help with the rules and schema?"
  ChatGPT provided the source‑grounded prompt and citation output format.

Lines 737-795: Study Recommendations Prompt
Reference:
  - ChatGPT (OpenAI). Study Recommendations Prompt.
    Date: 2026-01-22
    Prompt: "I need a study planner prompt that outputs actionable advice in numbered
    steps without markdown. Can you craft a prompt for that?"
  ChatGPT provided the system/user prompts and output constraints.

Lines 554-600: Draft Lecturer Email Function
Reference:
  - ChatGPT (OpenAI). Professional Lecturer Email Draft.
    Date: 2026-01-23
    Prompt: "I need a professional email draft to a lecturer based on a subject
    and a short request from a student. It should be polite, concise, and sign off
    with the student's name and ID. Can you craft the prompt?"
    ChatGPT provided the drafting prompt and format for generating professional 
    academic emails. The function takes the student name, ID, lecturer name, subject, 
    and request text, then uses AI to generate a polished email draft that the student 
    can review before sending.

================================================================================
FILE: scripts/send_daily_summaries.py
================================================================================

Lines 1-73: Daily Summary Batch Runner
Reference:
  - ChatGPT (OpenAI). Daily Summary Batch Job Pattern.
    Date: 2026-01-22
    Prompt: "I need a script that iterates over students, checks a last‑sent date,
    generates a summary, sends email, and records status. Can you sketch that flow?"
  ChatGPT provided the batch logic and status tracking updates.

Reference:
  - Apple Launchd Jobs Guide.
    URL: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html
  - Apple Property List (plist) format.
    URL: https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/PropertyLists/

================================================================================
FILE: config.py
================================================================================

Lines 5-10: python-dotenv
Reference:
  - python-dotenv Documentation.
    URL: https://github.com/theskumar/python-dotenv
  Loads environment variables from .env file for configuration management.

Lines 43-52: IMAP Configuration Dataclass
Reference:
  - ChatGPT (OpenAI). IMAP Configuration Pattern.
    Date: 2026-02-03
    Prompt: "I need a configuration pattern for IMAP email settings using a Python 
    dataclass. It should store host, port, username, password, SSL flag, and folder 
    settings for connecting to an email server to receive lecturer replies."
    ChatGPT provided the ImapConfig dataclass with typed fields for IMAP connection 
    settings.

Lines 128-166: IMAP Configuration Loader Function
Reference:
  - ChatGPT (OpenAI). IMAP Configuration Loader.
    Date: 2026-02-03
    Prompt: "I need a function that loads IMAP settings from environment variables. 
    It should read host, port, username, password, SSL flag, and folder from env vars, 
    validate that required fields are present, and return None if not fully configured."
    ChatGPT provided the get_imap_config() function that reads IMAP settings from 
    environment variables with validation, default values for port (993) and SSL (true), 
    and returns None if the configuration is incomplete.

================================================================================
FILE: templates/calendar.html
================================================================================

Lines 26-30: FullCalendar.js Library
Reference:
  - FullCalendar.js. JavaScript Event Calendar.
    URL: https://fullcalendar.io/docs
  Using FullCalendar v6.1.15 CDN for interactive calendar display.

Lines 39-122: FullCalendar Configuration
Reference:
  - FullCalendar.js Documentation. Initialization.
    URL: https://fullcalendar.io/docs#toc
  - FullCalendar.js Documentation. Configuration Options.
    URL: https://fullcalendar.io/docs/event-object
  Configuration based on FullCalendar docs, customized for assignment display.
  Includes time grid views, event formatting, and custom date formats.

Print Timetable: Print-Friendly Calendar CSS
Reference:
  - ChatGPT (OpenAI). Print-Friendly Calendar CSS.
    Date: 2026-02-10
    Prompt: "I need @media print CSS rules to create a clean, printable
    timetable from my FullCalendar.js calendar. Hide navigation, buttons,
    modals, and non-essential UI, keep the calendar grid clean with high
    contrast and a student info header."
    ChatGPT provided the @media print rules, the print header pattern,
    and the JavaScript logic for switching views and filtering events
    before printing.

Print Timetable: Print View JavaScript Logic
Reference:
  - ChatGPT (OpenAI). Print Timetable JavaScript Logic.
    Date: 2026-02-10
    Prompt: "I need JavaScript that switches the FullCalendar view to weekly
    or monthly before printing, filters events by type (assignments, lectures,
    manual), populates a print header, and restores the view after printing."
    ChatGPT provided the selectPrintView, printTimetable functions, and
    the event filtering by title prefix pattern.

FullCalendar All-Day End Date (Exclusive)
Reference:
  - ChatGPT (OpenAI). FullCalendar All-Day End Date (Exclusive).
    Date: 2026-02-11
    Prompt: "FullCalendar treats all-day event end dates as exclusive. If I set
    end == start for an all-day event, it can render oddly. How should I set the
    end date for an all-day deadline so it displays on the correct day?"
    ChatGPT recommended using end = start + 1 day for all-day events. Used in
    the calendar events endpoint in main.py when formatting task deadlines that
    have a due_date but no due_at time.

Lines 80-106: Ordinal Date Formatter
Reference:
  - ChatGPT (OpenAI). Ordinal Date Formatter.
    Date: 2025-10-30
    Prompt: "I need a JavaScript function to convert numbers to ordinal format (1st, 
    2nd, 3rd, 4th, etc.). It should handle edge cases like 11th, 12th, 13th (which use 
    'th' not 'st', 'nd', 'rd'). Can you provide a function that handles all cases correctly?"
    ChatGPT provided the ordinal function algorithm that correctly handles all number 
    cases including edge cases like 11th, 12th, 13th, 21st, 22nd, etc.
  - FullCalendar.js Documentation. Custom Title Format.
    URL: https://fullcalendar.io/docs/titleFormat
  Used in custom titleFormat function for day view to display dates like "November 4th, 2025".

================================================================================
FILE: templates/base.html
================================================================================

Lines 7-10: Bootstrap 5 CSS
Reference:
  - Bootstrap 5 Documentation. Getting Started.
    URL: https://getbootstrap.com/docs/5.3/getting-started/introduction/
  Bootstrap 5.3.3 CDN for responsive UI components and styling.

Lines 53-55: Bootstrap 5 JavaScript
Reference:
  - Bootstrap 5 Documentation. JavaScript.
    URL: https://getbootstrap.com/docs/5.3/getting-started/javascript/
  Bootstrap JavaScript bundle for interactive components (dropdowns, modals,
  etc.).

Lines 34-470 (CSS), 754-810 (JS): Dynamic Island Navigation Component
Reference:
  - ChatGPT (OpenAI). Dynamic Island Navigation Design.
    Date: 2026-02-03
    Prompt: "I want to create a floating pill-shaped navigation bar inspired by Apple's 
    Dynamic Island. It should have glassmorphism styling, grouped navigation links, a 
    'More' dropdown for additional pages, user profile section, and be fully responsive 
    with a mobile hamburger menu. Can you help me design the CSS and JavaScript for this?"
    ChatGPT provided the complete CSS styling with glassmorphism effects (backdrop-filter, 
    rgba backgrounds), the grouped navigation structure, dropdown menu behavior, and 
    mobile-responsive transforms. JavaScript handles toggle functions for the More menu 
    and mobile navigation, plus click-outside-to-close behavior.
  - CSS-Tricks. Glassmorphism CSS Guide.
    URL: https://css-tricks.com/glassmorphism-css-generator/
  The Dynamic Island navigation was designed for improved user experience with a modern, 
  floating interface that adapts to different screen sizes.

================================================================================
LIBRARY LICENSES
================================================================================

All major libraries used are open source with permissive licenses:

- Flask: BSD License
  https://github.com/pallets/flask/blob/main/LICENSE.rst

- Flask-Login: MIT License
  https://github.com/maxcountryman/flask-login/blob/main/LICENSE

- Werkzeug: BSD License
  https://github.com/pallets/werkzeug/blob/main/LICENSE.rst

- SQLAlchemy: MIT License
  https://github.com/sqlalchemy/sqlalchemy/blob/main/LICENSE

- canvasapi: MIT License
  https://github.com/ucfopen/canvasapi/blob/main/LICENSE

- Requests: Apache 2.0 License
  https://github.com/psf/requests/blob/main/LICENSE

- FullCalendar.js: MIT License
  https://github.com/fullcalendar/fullcalendar/blob/master/LICENSE.md

- Bootstrap: MIT License
  https://github.com/twbs/bootstrap/blob/main/LICENSE

- python-dotenv: BSD 3-Clause License
  https://github.com/theskumar/python-dotenv/blob/main/LICENSE

- psycopg2-binary: LGPL v3
  https://github.com/psycopg/psycopg2/blob/master/COPYING

- Pandas: BSD 3-Clause License
  https://github.com/pandas-dev/pandas/blob/main/LICENSE

- Matplotlib: PSF-like License
  https://github.com/matplotlib/matplotlib/blob/main/LICENSE/LICENSE

- icalendar: BSD License
  https://github.com/collective/icalendar/blob/main/LICENSE.rst

================================================================================
STANDARD LIBRARY USAGE
================================================================================

The following Python standard library modules are used (no external references
needed):

- datetime: Date and time handling
- os: Operating system interface for environment variables
- typing: Type hints
- threading: Multi-threading for background tasks
- queue: Thread-safe queue for inter-thread communication
- contextlib: Context manager utilities

================================================================================
DATABASE SCHEMA REFERENCES
================================================================================

SQL scripts used for database migrations (in scripts/ directory):

FILE: scripts/authentication_migration.sql
Reference:
  - ChatGPT (OpenAI). Authentication Fields Migration.
    Date: 2025-10-10
    Prompt: "I need to add authentication fields to my students table in PostgreSQL. 
    I need email (unique), password_hash, canvas_api_token, created_at, and last_login 
    columns. Can you give me the migration SQL with proper indexes?"
    ChatGPT provided the ALTER TABLE statements for all authentication fields and 
    email index for login performance.
  - PostgreSQL Documentation . ALTER TABLE Statement.
    URL: https://www.postgresql.org/docs/current/sql-altertable.html

FILE: scripts/add_canvas_fields.sql
Reference:
  - ChatGPT (OpenAI). Canvas Integration Database Schema.
    Date: 2025-10-20
    Prompt: "I need to add Canvas LMS integration fields to my tasks table in PostgreSQL. 
    I need columns for canvas_assignment_id and canvas_course_id, plus indexes for performance 
    and a unique constraint to prevent duplicate assignments per student. Can you give me 
    the SQL migration script?"
    ChatGPT provided the ALTER TABLE statements, indexes, and unique constraint pattern.
  - PostgreSQL Documentation . CREATE INDEX Statement.
    URL: https://www.postgresql.org/docs/current/sql-createindex.html

FILE: scripts/add_calendar_events_table.sql
Reference:
  - ChatGPT (OpenAI). Calendar Events Table Schema.
    Date: 2025-10-25
    Prompt: "I need to create a PostgreSQL table for calendar events (lectures, meetings) 
    that syncs with Canvas. It should have start_at and end_at timestamps, location, 
    foreign keys to students and modules, and Canvas event IDs. Can you create the schema 
    with proper indexes and constraints?"
    ChatGPT provided the complete table schema with foreign keys, unique constraints, 
    and performance indexes.
  - PostgreSQL Documentation  CREATE TABLE Statement.
    URL: https://www.postgresql.org/docs/current/sql-createtable.html

FILE: scripts/add_due_at_to_tasks.sql
Reference:
  - ChatGPT (OpenAI). Adding Timestamp Column with Backfill.
    Date: 2025-10-28
    Prompt: "I have a tasks table with a due_date column (date only). I need to add a 
    due_at column (timestamp with timezone) for precise due times. Can you give me SQL 
    to add the column, backfill existing rows by setting due_at to 5 PM on the due_date, 
    and create an index?"
    ChatGPT provided the ALTER TABLE, UPDATE with interval arithmetic, and index creation.
  - PostgreSQL Documentation . ALTER TABLE Statement.
    URL: https://www.postgresql.org/docs/current/sql-altertable.html
  - PostgreSQL Documentation . Data Types.
    URL: https://www.postgresql.org/docs/current/datatype.html

FILE: scripts/add_assignment_reviews_table.sql
Reference:
  - ChatGPT (OpenAI). Assignment Review Storage Schema.
    Date: 2026-01-22
    Prompt: "I need a table to store AI assignment reviews with feedback and score
    estimates linked to tasks and students. Can you draft the schema and indexes?"
  ChatGPT provided the schema and indexing approach for storing AI review history.

FILE: scripts/add_course_bot_tables.sql
Reference:
  - ChatGPT (OpenAI). Course Bot Storage Tables.
    Date: 2026-01-22
    Prompt: "I need tables for course documents and Q&A history for a course bot.
    Can you draft the schema and indexes?"
  ChatGPT provided the schema and indexing approach for course document uploads and Q&A history.

FILE: scripts/add_email_preferences.sql
Reference:
  - ChatGPT (OpenAI). Email Preferences Fields.
    Date: 2026-01-22
    Prompt: "I need columns for email notification preferences and daily summary
    status tracking in my students table. Can you provide the SQL?"
  ChatGPT provided the ALTER TABLE statements for email preference fields and status tracking.

FILE: scripts/add_student_number.sql
Reference:
  - ChatGPT (OpenAI). Student Number Field.
    Date: 2026-01-23
    Prompt: "I need to store a student_number on the students table so it can be used
    in email signatures. Can you provide the SQL?"
  ChatGPT provided the schema update for student numbers.

FILE: scripts/add_reminders_email_fields.sql
Reference:
  - ChatGPT (OpenAI). Reminder Email Tracking Fields.
    Date: 2026-01-22
    Prompt: "I need fields to track reminder email sent time, status, and error.
    Can you add those columns to the reminders table?"
  ChatGPT provided the SQL for the reminder email tracking fields.

FILE: scripts/add_lecturer_replies_table.sql
Reference:
  - ChatGPT (OpenAI). Lecturer Replies Table Schema.
    Date: 2026-02-03
    Prompt: "I need a PostgreSQL table to store incoming email replies from lecturers. 
    It should track the student, optionally link to a lecturer record, store email 
    fields (from_email, from_name, subject, body, received_at), have a read/unread 
    flag, prevent duplicates using message-id, and optionally link to the original 
    outgoing message. Can you provide the schema?"
    ChatGPT provided the table schema with foreign keys to students, lecturers, and 
    lecturer_messages tables, indexes for student_id and is_read status queries, and 
    unique constraint on message_id for deduplication.
  - PostgreSQL Documentation. CREATE TABLE Statement.
    URL: https://www.postgresql.org/docs/current/sql-createtable.html

FILE: scripts/add_lecturers_table.sql
Reference:
  - ChatGPT (OpenAI). Lecturers Directory Table.
    Date: 2026-01-23
    Prompt: "I need a lecturers table to store names, emails, and optional module codes
    so students can contact lecturers from a dashboard form. Can you draft the schema
    and indexes?"
    ChatGPT provided the schema and indexing pattern for lecturer contacts, including 
    email and module_code indexes for efficient lookups.
  - PostgreSQL Documentation. CREATE TABLE Statement.
    URL: https://www.postgresql.org/docs/current/sql-createtable.html

FILE: scripts/add_lecturer_messages_table.sql
Reference:
  - ChatGPT (OpenAI). Lecturer Messages Table.
    Date: 2026-01-23
    Prompt: "I need a table to store messages sent to lecturers from a dashboard
    contact form, with student and lecturer references, email status tracking, and 
    timestamps. Can you draft the schema and indexes?"
    ChatGPT provided the schema and indexing pattern for lecturer messages, including 
    email_status and email_error fields for delivery tracking.
  - PostgreSQL Documentation. CREATE TABLE Statement.
    URL: https://www.postgresql.org/docs/current/sql-createtable.html

FILE: scripts/add_activity_logs_table.sql
Reference:
  - ChatGPT (OpenAI). Activity Logs Table Schema.
    Date: 2026-02-04
    Prompt: "I need a table to store all user actions with timestamps. It should log
    student_id, path, method, endpoint, status_code, duration, and metadata."
    ChatGPT provided the schema and indexing pattern for activity logs.
  - PostgreSQL Documentation. CREATE TABLE Statement.
    URL: https://www.postgresql.org/docs/current/sql-createtable.html

All database migration scripts were created with ChatGPT assistance to ensure proper 
PostgreSQL syntax, indexing strategies, and constraint definitions.

================================================================================
ITERATION 5 ADDITIONS (US 23, US 24, US 25)
================================================================================

FILE: main.py
Reference:
  - ChatGPT (OpenAI). Module-Based Collaborative Study Groups Route.
    Date: 2026-02-25
    Prompt: "I need a Flask route for module-based study groups where students can join
    by module code, post messages, and share links/notes. Please include membership
    checks so only joined users can post."
  ChatGPT provided the route flow and membership-guard branching for /study-groups,
  including join/leave actions, thread posting, and resource sharing.

  - ChatGPT (OpenAI). AI Reading Summary Route with JSON Guard.
    Date: 2026-02-25
    Prompt: "I need a Flask endpoint that accepts pasted text or an uploaded PDF/DOCX,
    generates a concise study summary with OpenAI, and returns JSON safely for a frontend
    voice reader. Can you provide a robust pattern with input validation?"
  ChatGPT provided the validation + JSON response pattern used in /audio-summary.

  - ChatGPT (OpenAI). Spotify Playlist Search + Embed Route.
    Date: 2026-02-25
    Prompt: "I need a Flask route that checks Spotify OAuth session tokens, derives a
    study mood query from upcoming tasks, searches playlists via Spotify API, and shows
    embeddable playlist cards."
  ChatGPT provided the token refresh, mood-query, and playlist shaping flow used in
  /spotify/auth, /spotify/callback, /spotify/disconnect, and /focus-music.

  - ChatGPT (OpenAI). Time-of-Day Playlist Mood Tuning.
    Date: 2026-02-25
    Prompt: "I already map task context to Spotify playlist queries. Can you add a
    second layer that adapts the query by time of day (morning/afternoon/evening/night)
    so suggestions feel more natural?"
  ChatGPT provided the time-bucket tuning pattern used to append morning/afternoon/
  evening/night mood terms onto the base playlist query in /focus-music.

  - ChatGPT (OpenAI). Admin Activity Overview Dashboard Route.
    Date: 2026-02-25
    Prompt: "I need an admin-only Flask route that aggregates activity logs across all
    users (24h/7d totals, top routes, top users, and recent actions). Can you provide
    a safe SQL + render pattern with access guards?"
  ChatGPT provided the admin guard and aggregate-query pattern used in /admin/overview,
  including top paths, top users, and recent activity tables.

FILE: scripts/add_study_groups_tables.sql
Reference:
  - ChatGPT (OpenAI). Study Groups Migration Script.
    Date: 2026-02-25
    Prompt: "I need a safe SQL migration for module-based collaborative study groups
    with members, message thread, and shared resources. Can you provide CREATE TABLE
    and index statements using IF NOT EXISTS so reruns are safe?"
  ChatGPT provided the idempotent CREATE TABLE and index migration pattern.

================================================================================
DOMAIN REGISTRAR
================================================================================

Domain Registration (Production Deployment)
Reference:
  - Namecheap. Domain Name Registrar.
    URL: https://www.namecheap.com
  I purchased the custom domain used for production email sending through
  Namecheap. After registration, I configured DNS records (DKIM, SPF, MX) at
  Namecheap to verify the domain with Resend and enable outbound email delivery
  from the deployed application on Render.

  - Namecheap. How to Add DNS Records.
    URL: https://www.namecheap.com/support/knowledgebase/article.aspx/434/2237/how-do-i-set-up-host-records-for-a-domain/
  Used to configure the required TXT (DKIM, SPF) and MX records in Namecheap's
  Advanced DNS panel so Resend could verify domain ownership and send emails on
  behalf of the custom domain.

================================================================================
END OF REFERENCES
================================================================================

