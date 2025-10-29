#!/usr/bin/env python3
"""
Database migration script to add authentication fields to students table
Run this once to upgrade your database schema for user authentication
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_supabase import execute, fetch_all

def add_authentication_fields():
    """Add authentication fields to students table"""
    
    print("\n" + "="*70)
    print("🔐 ADDING AUTHENTICATION FIELDS TO DATABASE")
    print("="*70)
    
    try:
        # Add email field (unique, for login)
        print("\n1. Adding email field...")
        execute("""
            ALTER TABLE students 
            ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE
        """)
        print("   ✅ Email field added")
        
        # Add password_hash field
        print("\n2. Adding password_hash field...")
        execute("""
            ALTER TABLE students 
            ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)
        """)
        print("   ✅ Password hash field added")
        
        # Add canvas_api_token field (for future Canvas integration)
        print("\n3. Adding canvas_api_token field...")
        execute("""
            ALTER TABLE students 
            ADD COLUMN IF NOT EXISTS canvas_api_token VARCHAR(500)
        """)
        print("   ✅ Canvas API token field added")
        
        # Add created_at timestamp
        print("\n4. Adding created_at timestamp...")
        execute("""
            ALTER TABLE students 
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        """)
        print("   ✅ Created at timestamp added")
        
        # Add last_login timestamp
        print("\n5. Adding last_login timestamp...")
        execute("""
            ALTER TABLE students 
            ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE
        """)
        print("   ✅ Last login timestamp added")
        
        # Check current students
        students = fetch_all("SELECT id, name, email FROM students")
        print(f"\n📊 Current students in database: {len(students)}")
        
        if len(students) > 0:
            print("\n⚠️  WARNING: Existing students found!")
            print("   These students don't have email/password yet.")
            print("   They will need to register with their email.")
            print("\n   Existing students:")
            for student in students:
                email_status = student['email'] if student.get('email') else "❌ No email"
                print(f"      - {student['name']}: {email_status}")
        
        print("\n" + "="*70)
        print("🎉 DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\nNext steps:")
        print("1. Students can now register with email/password")
        print("2. Existing students need to register to get email/password")
        print("3. Canvas API tokens can be added later in user profile")
        print("\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR during migration: {str(e)}")
        print("="*70 + "\n")
        return False


if __name__ == "__main__":
    success = add_authentication_fields()
    sys.exit(0 if success else 1)

