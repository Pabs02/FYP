#!/usr/bin/env python3
"""
Simple script to add realistic data using the existing working database connection.
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_supabase_database_url
from db_supabase import execute, fetch_all

def add_sample_data():
    """Add realistic sample data for analytics."""
    print("🌱 Adding realistic sample data...")
    
    try:
        # Add more students
        students = [
            (2, 'Bob Smith'),
            (3, 'Carol Davis'),
            (4, 'David Wilson'),
            (5, 'Emma Brown'),
            (6, 'Frank Miller'),
            (7, 'Grace Lee'),
            (8, 'Henry Taylor'),
            (9, 'Ivy Chen'),
            (10, 'Jack Anderson')
        ]
        
        for student_id, name in students:
            execute(
                "INSERT INTO students (id, name) VALUES (:id, :name) ON CONFLICT (id) DO NOTHING",
                {"id": student_id, "name": name}
            )
        print("✅ Added students")
        
        # Add more modules
        modules = [
            (2, 'MATH201'),
            (3, 'PHYS301'),
            (4, 'ENG401'),
            (5, 'BIO202')
        ]
        
        for module_id, code in modules:
            execute(
                "INSERT INTO modules (id, code) VALUES (:id, :code) ON CONFLICT (id) DO NOTHING",
                {"id": module_id, "code": code}
            )
        print("✅ Added modules")
        
        # Add realistic tasks with varied completion patterns
        tasks = [
            # Completed tasks (on time)
            (3, 'Complete calculus homework', 'completed', '2025-10-20 23:59:59+00', '2025-10-19 15:45:00+00', 2, 2),
            (4, 'Physics lab report', 'completed', '2025-10-18 23:59:59+00', '2025-10-17 14:20:00+00', 3, 3),
            (5, 'Database design project', 'completed', '2025-10-22 23:59:59+00', '2025-10-21 16:10:00+00', 4, 1),
            (6, 'Linear algebra exercises', 'completed', '2025-10-25 23:59:59+00', '2025-10-24 11:30:00+00', 5, 2),
            (7, 'Chemistry experiment', 'completed', '2025-10-19 23:59:59+00', '2025-10-18 09:15:00+00', 6, 3),
            (8, 'Software engineering assignment', 'completed', '2025-10-21 23:59:59+00', '2025-10-20 13:45:00+00', 7, 1),
            (9, 'Statistics project', 'completed', '2025-10-23 23:59:59+00', '2025-10-22 10:20:00+00', 8, 2),
            (10, 'Biology research paper', 'completed', '2025-10-17 23:59:59+00', '2025-10-16 15:30:00+00', 9, 3),
            (11, 'Computer networks lab', 'completed', '2025-10-24 23:59:59+00', '2025-10-23 12:00:00+00', 10, 1),
            
            # Late completions (for analytics)
            (12, 'Advanced calculus problems', 'completed', '2025-10-16 23:59:59+00', '2025-10-17 08:30:00+00', 1, 2),
            (13, 'Thermodynamics assignment', 'completed', '2025-10-14 23:59:59+00', '2025-10-15 14:20:00+00', 2, 3),
            (14, 'Data structures project', 'completed', '2025-10-13 23:59:59+00', '2025-10-14 16:45:00+00', 3, 1),
            
            # In progress tasks
            (15, 'Prepare presentation slides', 'in_progress', '2025-10-25 23:59:59+00', None, 1, 1),
            (16, 'Machine learning project', 'in_progress', '2025-10-28 23:59:59+00', None, 2, 1),
            (17, 'Differential equations', 'in_progress', '2025-10-26 23:59:59+00', None, 3, 2),
            (18, 'Quantum mechanics homework', 'in_progress', '2025-10-27 23:59:59+00', None, 4, 3),
            (19, 'Web development assignment', 'in_progress', '2025-10-29 23:59:59+00', None, 5, 1),
            
            # Pending tasks
            (20, 'Final project proposal', 'pending', '2025-11-05 23:59:59+00', None, 6, 1),
            (21, 'Advanced statistics', 'pending', '2025-11-08 23:59:59+00', None, 7, 2),
            (22, 'Organic chemistry lab', 'pending', '2025-11-10 23:59:59+00', None, 8, 3),
            (23, 'Software testing project', 'pending', '2025-11-12 23:59:59+00', None, 9, 1),
            (24, 'Mathematical modeling', 'pending', '2025-11-15 23:59:59+00', None, 10, 2),
            
            # More completed tasks for better analytics (spread across weeks)
            (25, 'Algorithm analysis', 'completed', '2025-10-08 23:59:59+00', '2025-10-07 14:30:00+00', 1, 1),
            (26, 'Probability theory', 'completed', '2025-10-09 23:59:59+00', '2025-10-08 16:20:00+00', 2, 2),
            (27, 'Electromagnetism lab', 'completed', '2025-10-10 23:59:59+00', '2025-10-09 11:45:00+00', 3, 3),
            (28, 'Data mining project', 'completed', '2025-10-11 23:59:59+00', '2025-10-10 13:15:00+00', 4, 1),
            (29, 'Complex analysis', 'completed', '2025-10-12 23:59:59+00', '2025-10-11 09:30:00+00', 5, 2),
            (30, 'Machine learning basics', 'completed', '2025-10-06 23:59:59+00', '2025-10-07 10:20:00+00', 6, 1),
            (31, 'Numerical methods', 'completed', '2025-10-05 23:59:59+00', '2025-10-06 15:40:00+00', 7, 2),
            (32, 'System design project', 'completed', '2025-10-19 23:59:59+00', '2025-10-19 14:30:00+00', 8, 1),
            (33, 'Abstract algebra', 'completed', '2025-10-20 23:59:59+00', '2025-10-20 11:20:00+00', 9, 2),
            (34, 'Molecular biology', 'completed', '2025-10-21 23:59:59+00', '2025-10-21 16:45:00+00', 10, 3),
            (35, 'Computer graphics', 'completed', '2025-10-22 23:59:59+00', '2025-10-22 13:10:00+00', 1, 1),
            (36, 'Topology exercises', 'completed', '2025-10-23 23:59:59+00', '2025-10-23 10:30:00+00', 2, 2),
        ]
        
        for task_id, title, status, due_date, completed_at, student_id, module_id in tasks:
            execute(
                """INSERT INTO tasks (id, title, status, due_date, completed_at, student_id, module_id) 
                   VALUES (:id, :title, :status, :due_date, :completed_at, :student_id, :module_id) 
                   ON CONFLICT (id) DO NOTHING""",
                {
                    "id": task_id,
                    "title": title,
                    "status": status,
                    "due_date": due_date,
                    "completed_at": completed_at,
                    "student_id": student_id,
                    "module_id": module_id
                }
            )
        print("✅ Added tasks")
        
        # Verify data
        print("\n📊 Data Verification:")
        
        # Count students
        students_count = fetch_all("SELECT COUNT(*) as count FROM students")
        print(f"Students: {students_count[0]['count']}")
        
        # Count modules
        modules_count = fetch_all("SELECT COUNT(*) as count FROM modules")
        print(f"Modules: {modules_count[0]['count']}")
        
        # Count tasks by status
        task_stats = fetch_all("""
            SELECT status, COUNT(*) as count 
            FROM tasks 
            GROUP BY status 
            ORDER BY status
        """)
        print("Tasks by status:")
        for stat in task_stats:
            print(f"  {stat['status']}: {stat['count']}")
        
        # Count completed vs late tasks
        completion_stats = fetch_all("""
            SELECT 
                COUNT(*) as total_completed,
                SUM(CASE WHEN completed_at > due_date THEN 1 ELSE 0 END) as late_completed
            FROM tasks 
            WHERE status = 'completed' AND completed_at IS NOT NULL
        """)
        if completion_stats:
            stats = completion_stats[0]
            print(f"Completion stats:")
            print(f"  Total completed: {stats['total_completed']}")
            print(f"  Late completions: {stats['late_completed']}")
            if stats['total_completed'] > 0:
                on_time_rate = ((stats['total_completed'] - stats['late_completed']) / stats['total_completed']) * 100
                print(f"  On-time rate: {on_time_rate:.1f}%")
        
        print("\n✅ Sample data added successfully!")
        print("🔄 Now regenerate your analytics charts:")
        print("   python3 analytics_report.py")
        print("🌐 Then refresh your analytics page to see the new data!")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to add sample data."""
    # Load environment variables
    load_dotenv()
    
    # Check if we have database connection
    if not get_supabase_database_url():
        print("❌ No Supabase database URL found. Please set SUPABASE_DATABASE_URL environment variable.")
        return
    
    add_sample_data()

if __name__ == "__main__":
    main()
