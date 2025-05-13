import sqlite3
import time
from datetime import datetime

class Memory:
    """Memory manager for the voice assistant."""
    
    def __init__(self, db_path='assistant.db'):
        self.db_path = db_path
        self._ensure_db_setup()
    
    def _ensure_db_setup(self):
        """Ensure the database is properly set up with the required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we need to migrate from old schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='History_data'")
        old_table_exists = cursor.fetchone() is not None
        
        # Create enhanced memory table with timestamps and session tracking
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            speaker TEXT NOT NULL,
            message TEXT NOT NULL
        )
        ''')
        
        # Migrate data if needed
        if old_table_exists:
            cursor.execute("SELECT COUNT(*) FROM conversation_memory")
            if cursor.fetchone()[0] == 0:  # Only migrate if new table is empty
                cursor.execute("SELECT command, response FROM History_data")
                old_data = cursor.fetchall()
                
                # Generate a session ID for old data
                session_id = f"migrated_{int(time.time())}"
                
                # Insert old data into new table
                for command, response in old_data:
                    now = datetime.now().isoformat()
                    cursor.execute(
                        "INSERT INTO conversation_memory (timestamp, session_id, speaker, message) VALUES (?, ?, ?, ?)",
                        (now, session_id, "user", command)
                    )
                    cursor.execute(
                        "INSERT INTO conversation_memory (timestamp, session_id, speaker, message) VALUES (?, ?, ?, ?)",
                        (now, session_id, "assistant", response)
                    )
        
        conn.commit()
        conn.close()
    
    def add_interaction(self, user_message, assistant_response, session_id=None):
        """Add a complete interaction to memory."""
        if session_id is None:
            session_id = f"session_{int(time.time())}"
            
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store user message
        cursor.execute(
            "INSERT INTO conversation_memory (timestamp, session_id, speaker, message) VALUES (?, ?, ?, ?)",
            (now, session_id, "user", user_message)
        )
        
        # Store assistant response
        cursor.execute(
            "INSERT INTO conversation_memory (timestamp, session_id, speaker, message) VALUES (?, ?, ?, ?)",
            (now, session_id, "assistant", assistant_response)
        )
        
        conn.commit()
        conn.close()
    
    def get_recent_history(self, limit=5, session_id=None):
        """Get recent conversation history, optionally filtered by session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if session_id:
            cursor.execute(
                "SELECT speaker, message FROM conversation_memory WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
                (session_id, limit * 2)  # Multiply by 2 to get pairs of interactions
            )
        else:
            cursor.execute(
                "SELECT speaker, message FROM conversation_memory ORDER BY timestamp DESC LIMIT ?",
                (limit * 2,)  # Multiply by 2 to get pairs of interactions
            )
        
        history = cursor.fetchall()
        conn.close()
        
        # Reverse to get chronological order
        history.reverse()
        
        return history
    
    def format_history_for_llm(self, limit=3, session_id=None):
        """Format conversation history for inclusion in LLM prompt."""
        history = self.get_recent_history(limit, session_id)
        
        if not history:
            return ""
        
        formatted_history = "Previous conversation:\n"
        for speaker, message in history:
            speaker_name = "User" if speaker == "user" else "Assistant"
            formatted_history += f"{speaker_name}: {message}\n"
        
        return formatted_history + "\n"
    
    def search_memory(self, query, limit=5):
        """Search memory for relevant information based on query."""
        conn = sqlite3.connect(self.db_path)
        conn.create_function("LIKE_SCORE", 2, lambda x, y: 1 if y.lower() in x.lower() else 0)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT speaker, message, LIKE_SCORE(message, ?) as score
            FROM conversation_memory
            WHERE score > 0
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (query, limit * 2)
        )
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return ""
        
        formatted_results = "Relevant previous interactions:\n"
        for speaker, message, _ in results:
            speaker_name = "User" if speaker == "user" else "Assistant"
            formatted_results += f"{speaker_name}: {message}\n"
        
        return formatted_results + "\n"
    
    def get_current_session_id(self):
        """Generate or retrieve the current session ID."""
        # For now, just create a time-based session ID
        # In a production system, you might want to track sessions differently
        return f"session_{int(time.time())}"
    
    def clear_memory(self, session_id=None):
        """Clear memory, optionally just for a specific session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if session_id:
            cursor.execute("DELETE FROM conversation_memory WHERE session_id = ?", (session_id,))
        else:
            cursor.execute("DELETE FROM conversation_memory")
        
        conn.commit()
        conn.close()