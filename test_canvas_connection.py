#!/usr/bin/env python3
"""
Test Canvas API connection and fetch user data
Run this to verify your Canvas token works before integrating
"""

from canvasapi import Canvas
from datetime import datetime

# UCC Canvas configuration
CANVAS_URL = "https://ucc.instructure.com"
API_TOKEN = "13518~WXBMkD6LHmBmJeePx3t2ZAeFNNwyUkTZ4yUy4c4eP3Q4EkBZyuLZUGKr47ycrCrA"

def test_canvas_connection():
    print("\n" + "="*70)
    print("🎓 TESTING UCC CANVAS CONNECTION")
    print("="*70)
    
    try:
        # Initialize Canvas
        canvas = Canvas(CANVAS_URL, API_TOKEN)
        print(f"\n✅ Connected to: {CANVAS_URL}")
        
        # Get current user
        user = canvas.get_current_user()
        print(f"✅ Authenticated User: {user.name}")
        print(f"   └─ Email: {user.email if hasattr(user, 'email') else 'N/A'}")
        print(f"   └─ User ID: {user.id}")
        
        # Get enrolled courses
        print(f"\n📚 Fetching Your Courses...")
        courses = list(user.get_courses(enrollment_state='active'))
        print(f"✅ Found {len(courses)} Active Courses:")
        
        for course in courses[:10]:  # Show first 10
            print(f"\n   📖 {course.name}")
            print(f"      └─ Course ID: {course.id}")
            print(f"      └─ Code: {course.course_code if hasattr(course, 'course_code') else 'N/A'}")
            
            # Get assignments for this course
            try:
                assignments = list(course.get_assignments())
                print(f"      └─ Assignments: {len(assignments)}")
                
                # Show upcoming assignments
                upcoming = [a for a in assignments if hasattr(a, 'due_at') and a.due_at]
                if upcoming:
                    print(f"      └─ Upcoming due dates:")
                    for assignment in upcoming[:3]:  # Show first 3
                        try:
                            due_date = datetime.strptime(assignment.due_at.split('T')[0], '%Y-%m-%d')
                            print(f"         • {assignment.name}: {due_date.strftime('%d/%m/%Y')}")
                        except:
                            print(f"         • {assignment.name}: {assignment.due_at}")
            except Exception as e:
                print(f"      └─ Could not fetch assignments: {str(e)}")
        
        print("\n" + "="*70)
        print("🎉 CANVAS CONNECTION SUCCESSFUL!")
        print("="*70)
        print("\nYou can now integrate Canvas with your Student Task Management System!")
        print("Next steps:")
        print("1. Run database migration (add authentication fields)")
        print("2. Register/Login to your account")
        print("3. Store this token in your user profile")
        print("4. Sync assignments from Canvas to your dashboard")
        print("\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("="*70 + "\n")
        print("Troubleshooting:")
        print("1. Check your Canvas API token is correct")
        print("2. Ensure your token hasn't expired")
        print("3. Verify you're using the correct Canvas URL")
        print("4. Check your internet connection")
        return False


if __name__ == "__main__":
    test_canvas_connection()

