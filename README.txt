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

All database migration scripts were created with ChatGPT assistance to ensure proper 
PostgreSQL syntax, indexing strategies, and constraint definitions.

================================================================================
END OF REFERENCES
================================================================================

