"""
Canvas LMS Integration Module
Handles syncing assignments from Canvas to the Student Task Management System
"""

from canvasapi import Canvas
from datetime import datetime
from typing import List, Dict, Optional
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
        # Initialize Canvas connection with timeout
        canvas = Canvas(canvas_url, api_token)
        canvas._session.timeout = 30  # 30 second timeout for API calls
        
        # Get current user
        user = canvas.get_current_user()
        
        # Get active courses
        courses = list(user.get_courses(enrollment_state='active'))
        stats['courses_found'] = len(courses)
        
        for course in courses:
            try:
                # Get or create module for this course
                course_code = course.course_code if hasattr(course, 'course_code') else f"CANVAS-{course.id}"
                
                # Check if module exists
                module = db_fetch_one(
                    "SELECT id FROM modules WHERE code = :code",
                    {"code": course_code}
                )
                
                if not module:
                    # Create new module
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
                
                # Get assignments for this course (only upcoming/past 30 days to speed up sync)
                try:
                    assignments = list(course.get_assignments(bucket="upcoming"))
                    # Also get recent past assignments (last 30 days)
                    past_assignments = list(course.get_assignments(bucket="past"))
                    # Limit past to recent ones only
                    from datetime import datetime, timedelta
                    cutoff = datetime.now() - timedelta(days=30)
                    recent_past = [a for a in past_assignments if hasattr(a, 'due_at') and a.due_at and datetime.fromisoformat(a.due_at.replace('Z', '+00:00')) > cutoff]
                    assignments.extend(recent_past)
                except Exception:
                    # Fallback to all assignments if bucket filtering fails
                    assignments = list(course.get_assignments())
                
                for assignment in assignments:
                    try:
                        # Skip if no due date
                        if not hasattr(assignment, 'due_at') or not assignment.due_at:
                            stats['assignments_skipped'] += 1
                            continue
                        
                        # Parse due date and full timestamp (due_at)
                        due_dt_iso = assignment.due_at.replace('Z', '+00:00')
                        try:
                            due_dt = datetime.fromisoformat(due_dt_iso)
                        except Exception:
                            # Fallback to date-only
                            due_date_str = assignment.due_at.split('T')[0]
                            due_dt = datetime.strptime(due_date_str, '%Y-%m-%d')
                        due_date = due_dt.date()
                        
                        # Check if assignment already exists
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
                            # Update existing task
                            db_execute(
                                """UPDATE tasks 
                                   SET title = :title,
                                       due_date = :due_date,
                                       due_at = :due_at,
                                       module_id = :module_id
                                   WHERE id = :task_id""",
                                {
                                    "title": assignment.name,
                                    "due_date": due_date,
                                    "due_at": due_dt,
                                    "module_id": module_id,
                                    "task_id": existing_task['id']
                                }
                            )
                            stats['assignments_updated'] += 1
                        else:
                            # Insert new task
                            db_execute(
                                """INSERT INTO tasks 
                                   (title, student_id, module_id, due_date, due_at, status, canvas_assignment_id, canvas_course_id)
                                   VALUES (:title, :student_id, :module_id, :due_date, :due_at, :status, :canvas_assignment_id, :canvas_course_id)""",
                                {
                                    "title": assignment.name,
                                    "student_id": student_id,
                                    "module_id": module_id,
                                    "due_date": due_date,
                                    "due_at": due_dt,
                                    "status": "pending",
                                    "canvas_assignment_id": assignment.id,
                                    "canvas_course_id": course.id
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

    # Date window: default to past 14 days and next 90 days (Canvas prefers YYYY-MM-DD)
    if not start_iso or not end_iso:
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        start_iso = (now - timedelta(days=14)).date().isoformat()
        end_iso = (now + timedelta(days=90)).date().isoformat()

    headers = {"Authorization": f"Bearer {api_token}"}

    try:
        # Fetch user's active courses to build context codes
        canvas = Canvas(canvas_url, api_token)
        user = canvas.get_current_user()
        courses = list(user.get_courses(enrollment_state='active'))
        context_codes = [f"course_{c.id}" for c in courses if getattr(c, 'id', None)]
        # Include user's personal calendar for manually added lectures/events
        try:
            if getattr(user, 'id', None):
                context_codes.append(f"user_{user.id}")
        except Exception:
            pass

        # Paginate through calendar_events endpoint
        # API: GET /api/v1/calendar_events?type=event&context_codes[]=course_123
        params = {
            "type": "event",
            "all_events": "true",
            "start_date": start_iso,
            "end_date": end_iso,
        }

        events: List[Dict] = []
        # Query per-course to stay within URL length limits
        for code in context_codes:
            per_params = dict(params)
            per_params["context_codes[]"] = code
            url = f"{canvas_url}/api/v1/calendar_events"
            page_count = 0
            max_pages = 50  # Safety limit to prevent infinite loops
            while url and page_count < max_pages:
                try:
                    resp = requests.get(url, headers=headers, params=per_params, timeout=30)
                    if resp.status_code != 200:
                        stats["errors"] += 1
                        break
                    page_items = resp.json()
                    events.extend(page_items)
                    page_count += 1
                    # Pagination via Link header
                    next_url = None
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
                    per_params = None  # next pages include params in URL already
                except requests.exceptions.Timeout:
                    stats["errors"] += 1
                    break
                except Exception as e:
                    stats["errors"] += 1
                    break

        # Upsert events
        for ev in events:
            try:
                canvas_event_id = ev.get('id')
                title = ev.get('title') or "(Untitled event)"
                location = ev.get('location_address') or ev.get('location_name') or None
                start_at = ev.get('start_at')
                end_at = ev.get('end_at') or start_at
                # Ensure timed events have a positive duration so they appear in week/day views
                try:
                    from datetime import datetime, timedelta
                    start_dt = datetime.fromisoformat(start_at.replace('Z', '+00:00')) if isinstance(start_at, str) else start_at
                    end_dt = datetime.fromisoformat(end_at.replace('Z', '+00:00')) if isinstance(end_at, str) else end_at
                    if not end_dt or end_dt <= start_dt:
                        end_dt = start_dt + timedelta(minutes=60)
                        end_at = end_dt.isoformat()
                except Exception:
                    pass
                # Parse course id if available
                context_code = ev.get('context_code')  # e.g., "course_123"
                canvas_course_id = None
                if context_code and context_code.startswith('course_'):
                    try:
                        canvas_course_id = int(context_code.split('_')[1])
                    except Exception:
                        canvas_course_id = None

                # Map to module if possible
                module_id = None
                if canvas_course_id is not None:
                    mod = db_fetch_one(
                        "SELECT id FROM modules WHERE canvas_course_id = :cid OR code = :code",
                        {"cid": canvas_course_id, "code": ev.get('course_id') or ''}
                    )
                    if mod:
                        module_id = mod['id']

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

