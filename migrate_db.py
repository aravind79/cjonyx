#!/usr/bin/env python3
"""
Database migration script to add new columns to the blog table and create contact table
"""

import sqlite3
import os

def migrate_database():
    db_path = 'instance/cjonyx.db'
    
    if not os.path.exists(db_path):
        print("Database doesn't exist, will be created when server starts.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the new columns already exist in blog table
        cursor.execute("PRAGMA table_info(blog)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print(f"Current blog table columns: {columns}")
        
        # Add missing columns if they don't exist
        new_columns = [
            ("category", "VARCHAR(50) NOT NULL DEFAULT 'Business'"),
            ("tags", "VARCHAR(500)"),
            ("author_name", "VARCHAR(100) DEFAULT 'Shulammite P.'"),
            ("author_title", "VARCHAR(100) DEFAULT 'CEO & Founder at CJONYX'"),
            ("featured", "BOOLEAN DEFAULT 0")
        ]
        
        for column_name, column_def in new_columns:
            if column_name not in columns:
                try:
                    alter_sql = f"ALTER TABLE blog ADD COLUMN {column_name} {column_def}"
                    cursor.execute(alter_sql)
                    print(f"Added column: {column_name}")
                except sqlite3.Error as e:
                    print(f"Error adding column {column_name}: {e}")
        
        # Also make summary NOT NULL by updating existing NULL values
        try:
            cursor.execute("UPDATE blog SET summary = 'No summary provided' WHERE summary IS NULL OR summary = ''")
            print("Updated NULL summary values")
        except sqlite3.Error as e:
            print(f"Error updating summary values: {e}")
        
        # Create contact table if it doesn't exist
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contact (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) NOT NULL,
                    message TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    replied BOOLEAN DEFAULT 0
                )
            """)
            print("Contact table created or already exists")
        except sqlite3.Error as e:
            print(f"Error creating contact table: {e}")
        
        # Create chat_message table if it doesn't exist
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_message (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) NOT NULL,
                    message TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    replied BOOLEAN DEFAULT 0
                )
            """)
            print("ChatMessage table created or already exists")
        except sqlite3.Error as e:
            print(f"Error creating chat_message table: {e}")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
