"""
EduChat Database Models and User Management
Integrates with existing Streamlit app to add persistence
"""

import sqlite3
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import uuid
import streamlit as st
import pandas as pd

@dataclass
class User:
    """User profile with learning preferences and settings"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    age_group: str = "child"  # 'child', 'teen', 'adult'
    learning_preferences: Dict[str, Any] = field(default_factory=lambda: {
        'difficulty_level': 'beginner',
        'preferred_language': 'english',
        'target_language': 'finnish',
        'adhd_friendly_mode': False,
        'session_length_preference': 'medium',
        'favorite_characters': []
    })
    privacy_settings: Dict[str, Any] = field(default_factory=lambda: {
        'save_conversations': True,
        'track_progress': True,
        'share_with_family': True
    })
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

@dataclass
class ConversationRecord:
    """Stored conversation with metadata"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    title: str = ""
    topic: str = ""
    character_set: List[str] = field(default_factory=list)
    conversation_mode: str = "balanced"
    status: str = "active"
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    total_rounds: int = 0
    total_messages: int = 0
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class EduChatDatabase:
    """Database manager for EduChat persistence"""
    
    def __init__(self, db_path: str = "educhat.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age_group TEXT,
                learning_preferences TEXT, -- JSON
                privacy_settings TEXT, -- JSON
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
                character_set TEXT, -- JSON array
                conversation_mode TEXT,
                status TEXT,
                started_at TEXT,
                ended_at TEXT,
                total_rounds INTEGER,
                total_messages INTEGER,
                metadata TEXT, -- JSON
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
                metadata TEXT, -- JSON
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        """)
        
        # Character memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS character_memory (
                id TEXT PRIMARY KEY,
                character_name TEXT,
                user_id TEXT,
                memory_type TEXT, -- 'preference', 'fact', 'achievement'
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
        
        conn.commit()
        conn.close()
    
    def create_user(self, name: str, age_group: str = "child", 
                    learning_preferences: Dict = None) -> User:
        """Create a new user profile"""
        user = User(
            name=name,
            age_group=age_group,
            learning_preferences=learning_preferences or {}
        )
        
        conn = sqlite3.connect(self.db_path)
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
        conn.close()
        
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieve user by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
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
    
    def get_all_users(self) -> List[User]:
        """Get all users for family selection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users ORDER BY last_active DESC")
        rows = cursor.fetchall()
        conn.close()
        
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
        """Update user's last active timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET last_active = ? WHERE id = ?
        """, (datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
    
    def save_conversation(self, conversation: ConversationRecord):
        """Save conversation to database"""
        conn = sqlite3.connect(self.db_path)
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
        conn.close()
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversations for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM conversations 
            WHERE user_id = ? 
            ORDER BY started_at DESC 
            LIMIT ?
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
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
        """Store a memory for a character about a user"""
        conn = sqlite3.connect(self.db_path)
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
        conn.close()
    
    def get_character_memories(self, character_name: str, user_id: str, 
                              limit: int = 5) -> List[Dict]:
        """Get character's memories about a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT content, memory_type, importance_score, created_at
            FROM character_memory 
            WHERE character_name = ? AND user_id = ?
            ORDER BY importance_score DESC, last_accessed DESC
            LIMIT ?
        """, (character_name, user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        memories = []
        for row in rows:
            memories.append({
                'content': row[0],
                'type': row[1],
                'importance': row[2],
                'created_at': row[3]
            })
        
        return memories

class UserManager:
    """Streamlit integration for user management"""
    
    def __init__(self, db: EduChatDatabase):
        self.db = db
    
    def show_user_selection(self):
        """Display user selection/creation interface"""
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("👤 User Profile")
        
        # Get existing users
        users = self.db.get_all_users()
        
        if users:
            # Show existing users
            user_options = ["Select a user..."] + [f"{u.name} ({u.age_group})" for u in users]
            selected_option = st.sidebar.selectbox("Choose your profile:", user_options)
            
            if selected_option != "Select a user...":
                # Find selected user
                selected_index = user_options.index(selected_option) - 1
                selected_user = users[selected_index]
                
                # Store in session state
                st.session_state.current_user = selected_user
                self.db.update_user_activity(selected_user.id)
                
                # Show user info
                st.sidebar.success(f"Welcome back, {selected_user.name}! 👋")
                
                # Show quick stats if available
                conversations = self.db.get_user_conversations(selected_user.id, 5)
                if conversations:
                    st.sidebar.info(f"📚 {len(conversations)} recent conversations")
                
                return selected_user
        
        # Create new user section
        with st.sidebar.expander("➕ Create New User"):
            new_name = st.text_input("Name:")
            new_age_group = st.selectbox("Age Group:", ["child", "teen", "adult"])
            
            # Learning preferences
            st.write("**Learning Preferences:**")
            adhd_friendly = st.checkbox("ADHD-friendly mode")
            target_language = st.selectbox("Learning:", ["Finnish", "Spanish", "French"])
            difficulty = st.selectbox("Level:", ["beginner", "intermediate", "advanced"])
            
            if st.button("Create Profile") and new_name:
                # Create new user
                preferences = {
                    'difficulty_level': difficulty,
                    'target_language': target_language.lower(),
                    'adhd_friendly_mode': adhd_friendly,
                    'session_length_preference': 'medium'
                }
                
                new_user = self.db.create_user(new_name, new_age_group, preferences)
                st.session_state.current_user = new_user
                st.sidebar.success(f"Created profile for {new_name}! 🎉")
                st.rerun()
        
        return None
    
    def get_current_user(self) -> Optional[User]:
        """Get currently selected user"""
        return getattr(st.session_state, 'current_user', None)
    
    def show_user_analytics(self, user: User):
        """Display user-specific analytics"""
        if not user:
            return
        
        conversations = self.db.get_user_conversations(user.id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Conversations", len(conversations))
        
        with col2:
            total_messages = sum(c.get('total_messages', 0) for c in conversations)
            st.metric("Messages Exchanged", total_messages)
        
        # Recent conversations
        if conversations:
            st.write("**Recent Sessions:**")
            for conv in conversations[:3]:
                st.write(f"• {conv['title']} ({conv['total_messages']} messages)")
