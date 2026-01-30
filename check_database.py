"""
Check database contents without requiring sqlite3 command line.
"""
import sqlite3
import sys

def check_database():
    try:
        conn = sqlite3.connect('assistant.db')
        cursor = conn.cursor()
        
        print("Database Structure:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  Table: {table[0]}")
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"    Column: {col[1]} ({col[2]})")
        
        print("\nRecent Conversations:")
        cursor.execute("""
            SELECT session_id, role, content, created_at 
            FROM conversations 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        rows = cursor.fetchall()
        for row in rows:
            print(f"  Session: {row[0][:8]}... | Role: {row[1]} | Time: {row[3]}")
            print(f"    Content: {row[2][:80]}...")
            print()
        
        print("\nSessions Found:")
        cursor.execute("SELECT DISTINCT session_id FROM conversations")
        sessions = cursor.fetchall()
        for session in sessions:
            cursor.execute("SELECT COUNT(*) FROM conversations WHERE session_id=?", (session[0],))
            count = cursor.fetchone()[0]
            print(f"  {session[0][:12]}...: {count} messages")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return False

if __name__ == "__main__":
    check_database()