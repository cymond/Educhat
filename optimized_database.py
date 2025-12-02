"""
Database Performance Optimizations for EduChat
Compatible with your existing database_models.py structure
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

class OptimizedEduChatDatabase:
    """Enhanced database that extends your existing EduChatDatabase with optimizations"""
    
    def __init__(self, db_path: str = "educhat.db"):
        self.db_path = db_path
        self.init_optimized_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with optimization settings"""
        conn = sqlite3.connect(self.db_path)
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys=ON")
        # Optimize for speed
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        try:
            yield conn
        finally:
            conn.close()
    
    def init_optimized_database(self):
        """Initialize database with your existing schema + performance indexes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create your existing tables (keeping compatibility)
            self._create_existing_tables(cursor)
            
            # Add performance indexes
            self._create_performance_indexes(cursor)
            
            conn.commit()
    
    def _create_existing_tables(self, cursor):
        """Create tables matching your existing database_models.py structure"""
        
        # Users table (from your database_models.py)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age_group TEXT,
                learning_preferences TEXT,
                privacy_settings TEXT,
                created_at TEXT,
                last_active TEXT
            )
        """)
        
        # Conversations table  
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT,
                topic TEXT,
                character_set TEXT,
                conversation_mode TEXT,
                status TEXT,
                started_at TEXT,
                ended_at TEXT,
                total_rounds INTEGER,
                total_messages INTEGER,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                sender TEXT,
                content TEXT,
                timestamp TEXT,
                round_number INTEGER,
                message_order INTEGER,
                metadata TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        """)
        
        # Character memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS character_memory (
                id TEXT PRIMARY KEY,
                character_name TEXT,
                user_id TEXT,
                memory_type TEXT,
                content TEXT,
                importance_score INTEGER,
                created_at TEXT,
                last_accessed TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Learning progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_progress (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                subject TEXT,
                skill TEXT,
                current_level INTEGER,
                confidence_score REAL,
                last_practiced TEXT,
                practice_count INTEGER,
                mastery_achieved BOOLEAN,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
    
    def _create_performance_indexes(self, cursor):
        """Create indexes for frequently queried columns"""
        indexes = [
            # User queries
            "CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active)",
            "CREATE INDEX IF NOT EXISTS idx_users_name ON users(name)",
            
            # Conversation queries
            "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_conversations_started_at ON conversations(started_at)",
            "CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status)",
            
            # Message queries
            "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender)",
            
            # Character memory queries (most important for performance)
            "CREATE INDEX IF NOT EXISTS idx_character_memory_user_char ON character_memory(user_id, character_name)",
            "CREATE INDEX IF NOT EXISTS idx_character_memory_importance ON character_memory(importance_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_character_memory_accessed ON character_memory(last_accessed)",
            
            # Learning progress queries
            "CREATE INDEX IF NOT EXISTS idx_learning_progress_user_subject ON learning_progress(user_id, subject)",
            "CREATE INDEX IF NOT EXISTS idx_learning_progress_last_practiced ON learning_progress(last_practiced)",
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.Error as e:
                print(f"Index creation info: {e}")
    
    # ==================================================================
    # OPTIMIZED METHODS (keeping your existing method signatures)
    # ==================================================================
    
    def get_admin_stats_optimized(self) -> Dict[str, Any]:
        """Optimized admin panel statistics with single query"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Single query for all table counts
            stats_query = """
            SELECT 
                (SELECT COUNT(*) FROM users) as user_count,
                (SELECT COUNT(*) FROM conversations) as conversation_count,
                (SELECT COUNT(*) FROM messages) as message_count,
                (SELECT COUNT(*) FROM character_memory) as memory_count,
                (SELECT COUNT(*) FROM learning_progress) as progress_count
            """
            
            cursor.execute(stats_query)
            counts = cursor.fetchone()
            
            return {
                'users': counts[0],
                'conversations': counts[1],
                'messages': counts[2],
                'memories': counts[3],
                'progress_records': counts[4]
            }
    
    def get_character_memories_optimized(self, character_name: str, user_id: str, 
                                       limit: int = 5) -> List[Dict]:
        """Optimized character memory retrieval with better query"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Update last_accessed when memories are retrieved
            cursor.execute("""
                UPDATE character_memory 
                SET last_accessed = ?
                WHERE character_name = ? AND user_id = ?
            """, (datetime.now().isoformat(), character_name, user_id))
            
            # Optimized memory query with proper sorting
            cursor.execute("""
                SELECT content, memory_type, importance_score, created_at
                FROM character_memory 
                WHERE character_name = ? AND user_id = ?
                ORDER BY 
                    importance_score DESC, 
                    datetime(last_accessed) DESC,
                    datetime(created_at) DESC
                LIMIT ?
            """, (character_name, user_id, limit))
            
            rows = cursor.fetchall()
            conn.commit()
            
            return [{
                'content': row[0],
                'type': row[1],
                'importance': row[2],
                'created_at': row[3]
            } for row in rows]
    
    # ==================================================================
    # EXISTING METHODS (keeping full compatibility with your code)
    # ==================================================================
    
    def create_user(self, name: str, age_group: str = "child", 
                    learning_preferences: Dict = None):
        """Create a new user profile (same as your existing method)"""
        from database_models import User
        import uuid
        
        user = User(
            id=str(uuid.uuid4()),
            name=name,
            age_group=age_group,
            learning_preferences=learning_preferences or {}
        )
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (id, name, age_group, learning_preferences, 
                                 privacy_settings, created_at, last_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user.id, user.name, user.age_group,
                json.dumps(user.learning_preferences),
                json.dumps(user.privacy_settings),
                user.created_at.isoformat(),
                user.last_active.isoformat()
            ))
            
            conn.commit()
        
        return user
    
    def get_user(self, user_id: str):
        """Retrieve user by ID (same as your existing method)"""
        from database_models import User
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
        
        if not row:
            return None
        
        return User(
            id=row[0],
            name=row[1],
            age_group=row[2],
            learning_preferences=json.loads(row[3]) if row[3] else {},
            privacy_settings=json.loads(row[4]) if row[4] else {},
            created_at=datetime.fromisoformat(row[5]),
            last_active=datetime.fromisoformat(row[6])
        )
    
    def get_all_users(self) -> List:
        """Get all users for family selection (same as your existing method)"""
        from database_models import User
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users ORDER BY last_active DESC")
            rows = cursor.fetchall()
        
        users = []
        for row in rows:
            user = User(
                id=row[0],
                name=row[1], 
                age_group=row[2],
                learning_preferences=json.loads(row[3]) if row[3] else {},
                privacy_settings=json.loads(row[4]) if row[4] else {},
                created_at=datetime.fromisoformat(row[5]),
                last_active=datetime.fromisoformat(row[6])
            )
            users.append(user)
        
        return users
    
    def update_user_activity(self, user_id: str):
        """Update user's last active timestamp (same as your existing method)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users SET last_active = ? WHERE id = ?
            """, (datetime.now().isoformat(), user_id))
            
            conn.commit()
    
    def save_conversation(self, conversation):
        """Save conversation to database (same as your existing method)"""
        import uuid
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert or update conversation record
            cursor.execute("""
                INSERT OR REPLACE INTO conversations 
                (id, user_id, title, topic, character_set, conversation_mode, 
                 status, started_at, ended_at, total_rounds, total_messages, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conversation.id, conversation.user_id, conversation.title,
                conversation.topic, json.dumps(conversation.character_set),
                conversation.conversation_mode, conversation.status,
                conversation.started_at.isoformat(),
                conversation.ended_at.isoformat() if conversation.ended_at else None,
                conversation.total_rounds, conversation.total_messages,
                json.dumps(conversation.metadata)
            ))
            
            # Save messages
            for i, message in enumerate(conversation.messages):
                msg_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT OR REPLACE INTO messages
                    (id, conversation_id, sender, content, timestamp, 
                     round_number, message_order, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    msg_id, conversation.id, message['sender'], message['content'],
                    message['timestamp'].isoformat() if isinstance(message['timestamp'], datetime) 
                    else datetime.now().isoformat(),
                    message.get('round_number', 1), i,
                    json.dumps(message.get('metadata', {}))
                ))
            
            conn.commit()
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversations for a user (same as your existing method)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM conversations 
                WHERE user_id = ? 
                ORDER BY started_at DESC 
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
        
        conversations = []
        for row in rows:
            conv = {
                'id': row[0],
                'title': row[2],
                'topic': row[3],
                'started_at': row[7],
                'total_messages': row[10],
                'status': row[6]
            }
            conversations.append(conv)
        
        return conversations
    
    def store_character_memory(self, character_name: str, user_id: str, 
                              memory_type: str, content: str, importance: int = 5):
        """Store a memory for a character about a user (same as your existing method)"""
        import uuid
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            memory_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO character_memory
                (id, character_name, user_id, memory_type, content, 
                 importance_score, created_at, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_id, character_name, user_id, memory_type, content,
                importance, now, now
            ))
            
            conn.commit()
    
    def get_character_memories(self, character_name: str, user_id: str, 
                              limit: int = 5) -> List[Dict]:
        """Get character's memories about a user (backwards compatible)"""
        # This method calls the optimized version for backwards compatibility
        return self.get_character_memories_optimized(character_name, user_id, limit)
    
    def cleanup_old_memories(self, max_memories_per_character: int = 50):
        """Cleanup old, low-importance memories to maintain performance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Keep only top N memories per character-user pair
            cursor.execute("""
                DELETE FROM character_memory 
                WHERE id NOT IN (
                    SELECT id FROM character_memory cm1
                    WHERE cm1.character_name = character_memory.character_name 
                    AND cm1.user_id = character_memory.user_id
                    ORDER BY importance_score DESC, last_accessed DESC
                    LIMIT ?
                )
            """, (max_memories_per_character,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count
    
    def get_recent_activity_optimized(self, days: int = 7) -> Dict[str, Any]:
        """Get optimized activity analytics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Daily message counts
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as date, 
                    COUNT(*) as message_count,
                    COUNT(DISTINCT sender) as unique_speakers
                FROM messages 
                WHERE datetime(timestamp) >= datetime('now', '-{} days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """.format(days))
            
            daily_activity = cursor.fetchall()
            
            # User engagement
            cursor.execute("""
                SELECT 
                    u.name,
                    COUNT(DISTINCT c.id) as conversation_count,
                    COUNT(m.id) as total_messages,
                    MAX(datetime(u.last_active)) as last_active
                FROM users u
                LEFT JOIN conversations c ON u.id = c.user_id
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE datetime(u.last_active) >= datetime('now', '-{} days')
                GROUP BY u.id, u.name
                ORDER BY total_messages DESC
            """.format(days))
            
            user_engagement = cursor.fetchall()
            
            return {
                'daily_activity': [
                    {'date': row[0], 'messages': row[1], 'speakers': row[2]} 
                    for row in daily_activity
                ],
                'user_engagement': [
                    {
                        'name': row[0], 'conversations': row[1], 
                        'total_messages': row[2], 'last_active': row[3]
                    }
                    for row in user_engagement
                ]
            }

    def store_enhanced_memory(self, memory_item):
        """Store enhanced memory item in database"""
        self.store_character_memory(
            memory_item.character_name,
            memory_item.user_id,
            memory_item.memory_type,
            memory_item.content,
            memory_item.importance_score
        )
