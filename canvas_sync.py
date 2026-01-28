"""
Canvas LMS Integration Module
Handles syncing assignments from Canvas to the Student Task Management System
"""

# Reference: canvasapi Library (UCF Open)
# https://github.com/ucfopen/canvasapi
# Python wrapper for Canvas LMS API
from canvasapi import Canvas

from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Reference: Requests Library - HTTP for Humans
# https://requests.readthedocs.io/
# Used for direct Canvas REST API calls (calendar events endpoint)
import requests
import pytz

def sync_canvas_assignments(canvas_url: str, api_token: str, student_id: int, db_execute, db_fetch_all, db_fetch_one):
    """
    Sync all assignments from Canvas for a student
    
    Args:
        canvas_url: Canvas instance URL (e.g., https://ucc.instructure.com)
        api_token: Canvas API token for the student
        student_id: Database ID of the student
        db_execute: Database execute function
        db_fetch_all: Database fetch_all function
        db_fetch_one: Database fetch_one function
    
    Returns:
        dict: Sync statistics (new, updated, skipped assignments)
    """
    
    stats = {
        'courses_found': 0,
        'assignments_new': 0,
        'assignments_updated': 0,
        'assignments_skipped': 0,
        'modules_created': 0,
        'errors': []
    }
    
    try:
        # Reference: canvasapi Documentation - Getting Started
        # https://canvasapi.readthedocs.io/en/stable/getting_started.html
        # Connection pattern from canvasapi library examples
        canvas = Canvas(canvas_url, api_token)
        user = canvas.get_current_user()
        courses = list(user.get_courses(enrollment_state='active'))
        stats['courses_found'] = len(courses)
        
        if not courses:
            return stats
        
        for course in courses:
            try:
                # Reference: ChatGPT (OpenAI) - Module Matching and Auto-Creation
                # Date: 2025-10-20
                # Prompt: "When syncing Canvas courses, I need to match them to modules in my database. 
                # If a module doesn't exist, I should create it. If the course_code is missing, I should 
                # generate a fallback. Can you show me the pattern for checking existence and creating 
                # if needed?"
                # ChatGPT provided the upsert pattern for modules with fallback course code generation.
                course_code = course.course_code if hasattr(course, 'course_code') else f"CANVAS-{course.id}"
                
                module = db_fetch_one(
                    "SELECT id FROM modules WHERE code = :code",
                    {"code": course_code}
                )
                
                if not module:
                    db_execute(
                        "INSERT INTO modules (code) VALUES (:code)",
                        {"code": course_code}
                    )
                    module = db_fetch_one(
                        "SELECT id FROM modules WHERE code = :code",
                        {"code": course_code}
                    )
                    stats['modules_created'] += 1
                
                module_id = module['id']
                
                # Reference: Canvas API Documentation - List Assignments
                # https://canvas.instructure.com/doc/api/assignments.html#method.assignments.index
                # Fetch ALL assignments to ensure we don't miss any new ones, including past ones with grades
                # Also fetch assignments we already have in the database to update their grades
                try:
                    # Try to get all assignments without bucket filtering first (most comprehensive)
                    assignments = list(course.get_assignments())
                    
                    # If that fails or returns empty, fall back to bucket-based approach
                    if not assignments:
                        assignments = list(course.get_assignments(bucket="upcoming"))
                        past_assignments = list(course.get_assignments(bucket="past"))
                        # Include past assignments from last 180 days (wider window to catch graded assignments)
                        cutoff = datetime.now() - timedelta(days=180)
                        recent_past = [a for a in past_assignments if hasattr(a, 'due_at') and a.due_at and datetime.fromisoformat(a.due_at.replace('Z', '+00:00')) > cutoff]
                        assignments.extend(recent_past)
                    
                    # Also fetch assignments we already have in the database for this course to update grades
                    # This ensures we get grades for assignments that might be older than 180 days
                    existing_assignments = db_fetch_all(
                        """SELECT canvas_assignment_id FROM tasks 
                           WHERE student_id = :student_id 
                           AND canvas_course_id = :course_id
                           AND canvas_assignment_id IS NOT NULL
                           AND canvas_score IS NULL""",
                        {"student_id": student_id, "course_id": course.id}
                    )
                    
                    # Fetch submissions for existing assignments to get their grades
                    for existing in existing_assignments:
                        assignment_id = existing.get('canvas_assignment_id')
                        if assignment_id:
                            try:
                                # Try to fetch the assignment if we don't already have it in our list
                                if not any(a.id == assignment_id for a in assignments if hasattr(a, 'id')):
                                    try:
                                        assignment = course.get_assignment(assignment_id)
                                        if assignment:
                                            assignments.append(assignment)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                except Exception as fetch_error:
                    print(f"[sync] Error fetching assignments for course {course.id}: {fetch_error}")
                    # Last resort: try without any parameters
                    try:
                        assignments = list(course.get_assignments())
                    except Exception:
                        assignments = []
                
                for assignment in assignments:
                    try:
                        # Ensure full assignment details are loaded (description, points, etc.)
                        try:
                            assignment = course.get_assignment(assignment.id, include=['submission'])
                        except Exception:
                            pass

                        if not hasattr(assignment, 'due_at') or not assignment.due_at:
                            stats['assignments_skipped'] += 1
                            continue

                        due_dt_iso = assignment.due_at.replace('Z', '+00:00')
                        try:
                            due_dt = datetime.fromisoformat(due_dt_iso)
                        except Exception:
                            due_date_str = assignment.due_at.split('T')[0]
                            due_dt = datetime.strptime(due_date_str, '%Y-%m-%d')
                        due_date = due_dt.date()

                        assignment_description = getattr(assignment, 'description', None)
                        points_possible = getattr(assignment, 'points_possible', None)
                        # Canvas points_possible is NOT the same as weight_percentage
                        # Weight percentage is configured at assignment group level and requires
                        # additional API calls to calculate. Setting to None - users can manually set it
                        # when they know the assignment's percentage of the module grade.
                        weight_percentage = None

                        canvas_score = None
                        canvas_possible = None
                        canvas_graded_at = None
                        try:
                            submission = assignment.get_submission(user.id, include=["submission_history", "total_scores"])
                            if submission:
                                canvas_score = getattr(submission, 'score', None)
                                if canvas_score is None and hasattr(submission, 'entered_score'):
                                    canvas_score = getattr(submission, 'entered_score', None)
                                canvas_possible = getattr(submission, 'points_possible', None) or points_possible
                                if canvas_possible is None and assignment.points_possible:
                                    canvas_possible = assignment.points_possible
                                graded_raw = getattr(submission, 'graded_at', None) or getattr(submission, 'entered_grade_at', None)
                                if graded_raw:
                                    canvas_graded_at = datetime.fromisoformat(str(graded_raw).replace('Z', '+00:00'))
                        except Exception as submission_error:
                            print(f"[sync] submission fetch failed assignment={assignment.id} error={submission_error}")

                        existing_task = db_fetch_one(
                            """SELECT id FROM tasks 
                               WHERE canvas_assignment_id = :canvas_id 
                               AND student_id = :student_id""",
                            {
                                "canvas_id": assignment.id,
                                "student_id": student_id
                            }
                        )

                        if existing_task:
                            # Always update grades even if other fields haven't changed
                            # This ensures we get the latest grades from Canvas
                            db_execute(
                                """UPDATE tasks 
                                   SET title = :title,
                                       due_date = :due_date,
                                       due_at = :due_at,
                                       module_id = :module_id,
                                       description = :description,
                                       weight_percentage = COALESCE(:weight_percentage, weight_percentage),
                                       canvas_score = COALESCE(:canvas_score, canvas_score),
                                       canvas_possible = COALESCE(:canvas_possible, canvas_possible),
                                       canvas_graded_at = COALESCE(:canvas_graded_at, canvas_graded_at)
                                   WHERE id = :task_id""",
                                {
                                    "title": assignment.name,
                                    "due_date": due_date,
                                    "due_at": due_dt,
                                    "module_id": module_id,
                                    "description": assignment_description,
                                    "weight_percentage": weight_percentage,
                                    "canvas_score": canvas_score,
                                    "canvas_possible": canvas_possible,
                                    "canvas_graded_at": canvas_graded_at,
                                    "task_id": existing_task['id']
                                }
                            )
                            stats['assignments_updated'] += 1
                        else:
                            db_execute(
                                """INSERT INTO tasks 
                                   (title, student_id, module_id, due_date, due_at, status, canvas_assignment_id, canvas_course_id,
                                    description, weight_percentage, canvas_score, canvas_possible, canvas_graded_at)
                                   VALUES (:title, :student_id, :module_id, :due_date, :due_at, :status, :canvas_assignment_id, :canvas_course_id,
                                           :description, :weight_percentage, :canvas_score, :canvas_possible, :canvas_graded_at)""",
                                {
                                    "title": assignment.name,
                                    "student_id": student_id,
                                    "module_id": module_id,
                                    "due_date": due_date,
                                    "due_at": due_dt,
                                    "status": "pending",
                                    "canvas_assignment_id": assignment.id,
                                    "canvas_course_id": course.id,
                                    "description": assignment_description,
                                    "weight_percentage": weight_percentage,
                                    "canvas_score": canvas_score,
                                    "canvas_possible": canvas_possible,
                                    "canvas_graded_at": canvas_graded_at
                                }
                            )
                            stats['assignments_new'] += 1
                    
                    except Exception as e:
                        stats['errors'].append(f"Error syncing assignment {assignment.name}: {str(e)}")
                        continue
            
            except Exception as e:
                stats['errors'].append(f"Error syncing course {course.name}: {str(e)}")
                continue
        
    except Exception as e:
        stats['errors'].append(f"Canvas connection error: {str(e)}")
    
    return stats


def get_canvas_assignment_url(canvas_url: str, course_id: int, assignment_id: int) -> str:
    """Generate Canvas assignment URL"""
    return f"{canvas_url}/courses/{course_id}/assignments/{assignment_id}"


def sync_canvas_calendar_events(
    canvas_url: str,
    api_token: str,
    student_id: int,
    db_execute,
    db_fetch_all,
    db_fetch_one,
    start_iso: Optional[str] = None,
    end_iso: Optional[str] = None,
) -> Dict[str, int]:
    """
    Syncs Canvas calendar events (e.g., lectures) into an events table with start/end times.

    Creates the event if not present for this student, otherwise updates title/time/location.

    Returns: { 'events_new': X, 'events_updated': Y, 'errors': Z }
    """
    stats = {"events_new": 0, "events_updated": 0, "errors": 0}

    if not start_iso or not end_iso:
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        start_iso = (now - timedelta(days=30)).date().isoformat()
        end_iso = (now + timedelta(days=30)).date().isoformat()

    headers = {"Authorization": f"Bearer {api_token}"}

    try:
        canvas = Canvas(canvas_url, api_token)
        user = canvas.get_current_user()
        courses = list(user.get_courses(enrollment_state='active'))
        context_codes = [f"course_{c.id}" for c in courses[:10] if getattr(c, 'id', None)]
        try:
            if getattr(user, 'id', None):
                context_codes.append(f"user_{user.id}")
        except Exception:
            pass

        params = {
            "type": "event",
            "start_date": start_iso,
            "end_date": end_iso,
        }

        events: List[Dict] = []
        for code in context_codes:
            per_params = dict(params)
            per_params["context_codes[]"] = code
            # Reference: ChatGPT (OpenAI) - Canvas API Pagination with Link Header
            # Date: 2025-11-04
            # Prompt: "How can I fetch all Canvas API events or assignments when the API response is paginated? 
            # Can you give me Python code that loops through each page using the Link header until all results are retrieved?"
            # ChatGPT provided a pagination pattern for the Canvas API that follows the Link headers returned by 
            # each response. The loop repeatedly calls the API, appends JSON items to the local list, and updates 
            # the request URL using the rel="next" link until there are no more pages or a maximum page limit is reached.
            # Changes Made: Adapted to handle case-insensitive headers, added timeout and max page limit,
            # integrated with Canvas calendar events endpoint.
            # Reference: Canvas API Documentation - Calendar Events
            # https://canvas.instructure.com/doc/api/calendar_events.html#method.calendar_events.index
            # Reference: Canvas API Documentation - Pagination
            # https://canvas.instructure.com/doc/api/file.pagination.html
            # Reference: RFC 5988 - Web Linking (Link Header)
            # https://tools.ietf.org/html/rfc5988
            url = f"{canvas_url}/api/v1/calendar_events"
            page_count = 0
            max_pages = 50
            while url and page_count < max_pages:
                try:
                    resp = requests.get(url, headers=headers, params=per_params, timeout=30)
                    if resp.status_code != 200:
                        stats["errors"] += 1
                        break
                    page_items = resp.json()
                    events.extend(page_items)
                    page_count += 1
                    next_url = None
                    # Parse Link header for next page URL
                    link_header = resp.headers.get('Link') or resp.headers.get('link')
                    if link_header:
                        for part in link_header.split(','):
                            if 'rel="next"' in part:
                                start = part.find('<') + 1
                                end = part.find('>')
                                if start > 0 and end > start:
                                    next_url = part[start:end]
                                break
                    url = next_url
                    per_params = None
                except requests.exceptions.Timeout:
                    stats["errors"] += 1
                    break
                except Exception as e:
                    stats["errors"] += 1
                    break

        for ev in events:
            try:
                canvas_event_id = ev.get('id')
                title = ev.get('title') or "(Untitled event)"
                location = ev.get('location_address') or ev.get('location_name') or None
                start_at = ev.get('start_at')
                end_at = ev.get('end_at') or start_at
                # Reference: ChatGPT (OpenAI) - Date/Time Parsing and Normalization
                # Date: 2025-11-04
                # Prompt: "Sometimes Canvas events don't have an end time. Can you give me Python code that 
                # checks the start and end times, and if the end is missing or earlier than the start, sets it 
                # one hour later automatically?"
                # ChatGPT provided a guard block around event timestamps to guarantee that each event has a 
                # sensible end time. The code converts ISO timestamps to datetime objects and, if an event is 
                # missing an end time or has an end time earlier than its start, it automatically assigns a 
                # default duration of 60 minutes. This prevents invalid time ranges from breaking the calendar 
               # rendering or analytics.
                # Reference: Python datetime Documentation - ISO Format Parsing
                # https://docs.python.org/3/library/datetime.html#datetime.datetime.fromisoformat
                try:
                    from datetime import datetime, timedelta
                    start_dt = datetime.fromisoformat(start_at.replace('Z', '+00:00')) if isinstance(start_at, str) else start_at
                    end_dt = datetime.fromisoformat(end_at.replace('Z', '+00:00')) if isinstance(end_at, str) else end_at
                    if not end_dt or end_dt <= start_dt:
                        end_dt = start_dt + timedelta(minutes=60)
                        end_at = end_dt.isoformat()
                except Exception:
                    pass
                # Reference: ChatGPT (OpenAI) - Context Code Parsing and Module Matching
                # Date: 2025-10-25
                # Prompt: "Canvas API returns context codes like 'course_12345' or 'user_67890'. I need 
                # to extract the course ID from these strings and match them to modules in my database. 
                # Can you show me how to parse the context code and handle cases where it might not be 
                # a course?"
                # ChatGPT provided the pattern for parsing Canvas context codes and matching to modules 
                # with fallback logic.
                context_code = ev.get('context_code')
                canvas_course_id = None
                if context_code and context_code.startswith('course_'):
                    try:
                        canvas_course_id = int(context_code.split('_')[1])
                    except Exception:
                        canvas_course_id = None

                module_id = None
                if canvas_course_id is not None:
                    mod = db_fetch_one(
                        "SELECT id FROM modules WHERE canvas_course_id = :cid OR code = :code",
                        {"cid": canvas_course_id, "code": ev.get('course_id') or ''}
                    )
                    if mod:
                        module_id = mod['id']

                # Reference: ChatGPT (OpenAI) - Database Upsert Pattern for Events
                # Date: 2025-11-04
                # Prompt: "How do I update an event if it already exists in my Supabase table, or insert a new 
                # one if it doesn't? Can you show me an SQL example using Python and Supabase?"
                # ChatGPT provided pattern for checking if event exists, then updating or inserting.
                # Changes Made: Adapted for events table with canvas_event_id for deduplication.
                existing = db_fetch_one(
                    """
                    SELECT id FROM events 
                    WHERE student_id = :student_id AND canvas_event_id = :canvas_event_id
                    """,
                    {"student_id": student_id, "canvas_event_id": canvas_event_id}
                )

                if existing:
                    db_execute(
                        """
                        UPDATE events
                        SET title = :title,
                            start_at = :start_at,
                            end_at = :end_at,
                            location = :location,
                            module_id = :module_id,
                            canvas_course_id = :canvas_course_id
                        WHERE id = :id
                        """,
                        {
                            "title": title,
                            "start_at": start_at,
                            "end_at": end_at,
                            "location": location,
                            "module_id": module_id,
                            "canvas_course_id": canvas_course_id,
                            "id": existing['id'],
                        }
                    )
                    stats["events_updated"] += 1
                else:
                    db_execute(
                        """
                        INSERT INTO events
                        (student_id, module_id, title, start_at, end_at, location, canvas_event_id, canvas_course_id)
                        VALUES (:student_id, :module_id, :title, :start_at, :end_at, :location, :canvas_event_id, :canvas_course_id)
                        """,
                        {
                            "student_id": student_id,
                            "module_id": module_id,
                            "title": title,
                            "start_at": start_at,
                            "end_at": end_at,
                            "location": location,
                            "canvas_event_id": canvas_event_id,
                            "canvas_course_id": canvas_course_id,
                        }
                    )
                    stats["events_new"] += 1
            except Exception:
                stats["errors"] += 1

    except Exception:
        stats["errors"] += 1

    return stats

