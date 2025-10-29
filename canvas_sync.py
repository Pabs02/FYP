"""
Canvas LMS Integration Module
Handles syncing assignments from Canvas to the Student Task Management System
"""

from canvasapi import Canvas
from datetime import datetime
from typing import List, Dict, Optional
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
        # Initialize Canvas connection
        canvas = Canvas(canvas_url, api_token)
        
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
                
                # Get assignments for this course
                assignments = list(course.get_assignments())
                
                for assignment in assignments:
                    try:
                        # Skip if no due date
                        if not hasattr(assignment, 'due_at') or not assignment.due_at:
                            stats['assignments_skipped'] += 1
                            continue
                        
                        # Parse due date
                        due_date_str = assignment.due_at.split('T')[0]
                        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                        
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
                                       module_id = :module_id
                                   WHERE id = :task_id""",
                                {
                                    "title": assignment.name,
                                    "due_date": due_date,
                                    "module_id": module_id,
                                    "task_id": existing_task['id']
                                }
                            )
                            stats['assignments_updated'] += 1
                        else:
                            # Insert new task
                            db_execute(
                                """INSERT INTO tasks 
                                   (title, student_id, module_id, due_date, status, canvas_assignment_id, canvas_course_id)
                                   VALUES (:title, :student_id, :module_id, :due_date, :status, :canvas_assignment_id, :canvas_course_id)""",
                                {
                                    "title": assignment.name,
                                    "student_id": student_id,
                                    "module_id": module_id,
                                    "due_date": due_date,
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

