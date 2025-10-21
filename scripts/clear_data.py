#!/usr/bin/env python3
"""
Clear all data from the database tables.
WARNING: This will delete ALL data from students, modules, and tasks tables.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_supabase import execute

def clear_all_data():
    """Delete all data from all tables"""
    print("⚠️  WARNING: This will delete ALL data from your database!")
    print("Tables to be cleared: tasks, students, modules")
    
    confirm = input("\nType 'YES' to confirm deletion: ")
    
    if confirm != "YES":
        print("❌ Cancelled. No data was deleted.")
        return
    
    try:
        # Delete in order to respect foreign key constraints
        print("\n🗑️  Deleting tasks...")
        tasks_deleted = execute("DELETE FROM tasks")
        print(f"   ✅ Deleted {tasks_deleted} tasks")
        
        print("🗑️  Deleting students...")
        students_deleted = execute("DELETE FROM students")
        print(f"   ✅ Deleted {students_deleted} students")
        
        print("🗑️  Deleting modules...")
        modules_deleted = execute("DELETE FROM modules")
        print(f"   ✅ Deleted {modules_deleted} modules")
        
        print("\n✨ Database cleared successfully!")
        print("You can now add data through the web interface at http://127.0.0.1:5001/add-data")
        
    except Exception as e:
        print(f"\n❌ Error clearing data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    clear_all_data()

