#!/usr/bin/env python3
"""
Migration script to add 'cancelled' column to documents table
"""
import os
import sys
import psycopg2
from urllib.parse import urlparse

def run_migration():
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL environment variable not found")
        return False
    
    try:
        # Parse database URL
        parsed = urlparse(db_url)
        db_config = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path[1:]  # Remove leading slash
        }
        
        print(f"🔗 Connecting to database: {db_config['host']}")
        
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'documents' AND column_name = 'cancelled'
        """)
        
        if cursor.fetchone():
            print("✅ Column 'cancelled' already exists in documents table")
            return True
        
        # Add the cancelled column
        print("📝 Adding 'cancelled' column to documents table...")
        cursor.execute("""
            ALTER TABLE documents 
            ADD COLUMN cancelled BOOLEAN DEFAULT FALSE
        """)
        
        # Update any existing documents to have cancelled = false
        cursor.execute("""
            UPDATE documents 
            SET cancelled = FALSE 
            WHERE cancelled IS NULL
        """)
        
        # Commit the changes
        conn.commit()
        
        print("✅ Successfully added 'cancelled' column to documents table")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Running database migration...")
    success = run_migration()
    sys.exit(0 if success else 1) 