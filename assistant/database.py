"""
Database module for persistent conversation history and user data.
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import threading

class Database:
    def __init__(self, db_path: str = "assistant.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    plugin_used TEXT,
                    tokens_used INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON conversations(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON conversations(created_at)')
            
            # Create user settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id TEXT PRIMARY KEY DEFAULT 'default',
                    default_city TEXT,
                    preferred_news_category TEXT DEFAULT 'general',
                    timezone TEXT DEFAULT 'UTC',
                    assistant_name TEXT DEFAULT 'Jarvis',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create plugin usage statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plugin_stats (
                    plugin_name TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    execution_count INTEGER DEFAULT 0,
                    last_used TIMESTAMP,
                    PRIMARY KEY (plugin_name, session_id)
                )
            ''')
            
            # Create reminders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    reminder_text TEXT NOT NULL,
                    due_time TIMESTAMP NOT NULL,
                    completed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def save_conversation(self, session_id: str, role: str, content: str, 
                         plugin_used: Optional[str] = None, tokens_used: int = 0):
        """Save a conversation turn to the database."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conversations (session_id, role, content, plugin_used, tokens_used)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, role, content, plugin_used, tokens_used))
            
            conn.commit()
            conn.close()
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT role, content, plugin_used, created_at
                FROM conversations
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (session_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to list of dicts and reverse to chronological order
            history = [dict(row) for row in rows]
            return list(reversed(history))
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of recent sessions."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    session_id,
                    COUNT(*) as message_count,
                    MAX(created_at) as last_activity,
                    MIN(created_at) as first_activity
                FROM conversations
                GROUP BY session_id
                ORDER BY MAX(created_at) DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
    
    def update_plugin_stats(self, plugin_name: str, session_id: str):
        """Update plugin usage statistics."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO plugin_stats (plugin_name, session_id, execution_count, last_used)
                VALUES (?, ?, 
                    COALESCE((SELECT execution_count + 1 FROM plugin_stats 
                              WHERE plugin_name = ? AND session_id = ?), 1),
                    CURRENT_TIMESTAMP)
            ''', (plugin_name, session_id, plugin_name, session_id))
            
            conn.commit()
            conn.close()
    
    def get_plugin_stats(self) -> Dict[str, Any]:
        """Get overall plugin usage statistics."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    plugin_name,
                    SUM(execution_count) as total_executions,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    MAX(last_used) as last_used
                FROM plugin_stats
                WHERE plugin_name IS NOT NULL
                GROUP BY plugin_name
                ORDER BY total_executions DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            stats = {
                "total_plugins": len(rows),
                "plugins": [dict(row) for row in rows],
                "total_executions": sum(row['total_executions'] for row in rows)
            }
            return stats
    
    def save_reminder(self, session_id: str, reminder_text: str, due_time: datetime):
        """Save a reminder to the database."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO reminders (session_id, reminder_text, due_time)
                VALUES (?, ?, ?)
            ''', (session_id, reminder_text, due_time.isoformat()))
            
            conn.commit()
            conn.close()
    
    def get_due_reminders(self, session_id: str) -> List[Dict[str, Any]]:
        """Get reminders that are due for a session."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, reminder_text, due_time
                FROM reminders
                WHERE session_id = ? 
                  AND completed = 0 
                  AND due_time <= CURRENT_TIMESTAMP
                ORDER BY due_time ASC
            ''', (session_id,))
            
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
    
    def mark_reminder_completed(self, reminder_id: int):
        """Mark a reminder as completed."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE reminders
                SET completed = 1
                WHERE id = ?
            ''', (reminder_id,))
            
            conn.commit()
            conn.close()
    
    def get_user_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get user settings."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM user_settings
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            else:
                # Return default settings
                return {
                    "user_id": user_id,
                    "default_city": "London",
                    "preferred_news_category": "general",
                    "timezone": "UTC",
                    "assistant_name": "Jarvis"
                }
    
    def update_user_settings(self, user_id: str, settings: Dict[str, Any]):
        """Update user settings."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get existing settings to update only provided fields
            existing = self.get_user_settings(user_id)
            updated_settings = {**existing, **settings}
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_settings 
                (user_id, default_city, preferred_news_category, timezone, assistant_name, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                updated_settings.get("default_city"),
                updated_settings.get("preferred_news_category"),
                updated_settings.get("timezone"),
                updated_settings.get("assistant_name")
            ))
            
            conn.commit()
            conn.close()
    
    def cleanup_old_conversations(self, days_to_keep: int = 30):
        """Clean up old conversations to save space."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM conversations
                WHERE created_at < datetime('now', ?)
            ''', (f'-{days_to_keep} days',))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            # Vacuum to reclaim space
            cursor.execute('VACUUM')
            conn.close()
            
            return deleted_count