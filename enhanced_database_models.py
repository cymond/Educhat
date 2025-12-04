"""
Enhanced Database Models for Character Personality Framework
Extends existing EduChat database with personality persistence and advanced memory systems
"""

import sqlite3
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
from character_personality_framework import (
    EnhancedCharacter, BehavioralAttributes, DynamicState, CharacterMemory,
    EmotionalState, ResponseStyle, PatientLevel
)

class EnhancedEduChatDatabase:
    """Enhanced database manager with Character Personality Framework support"""
    
    def __init__(self, db_path: str = "educhat_enhanced.db"):
        self.db_path = db_path
        self.init_enhanced_database()
    
    def init_enhanced_database(self):
        """Initialize SQLite database with enhanced tables for CPF"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Existing tables (users, conversations, messages) - keep as is
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
        
        # Enhanced Character Personality Tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS character_personalities (
                id TEXT PRIMARY KEY,
                character_name TEXT UNIQUE,
                archetype TEXT,
                core_attributes TEXT, -- JSON: BehavioralAttributes
                knowledge_domains TEXT, -- JSON
                teaching_specialties TEXT, -- JSON
                conversation_starters TEXT, -- JSON
                adaptation_prompts TEXT, -- JSON
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS character_states (
                id TEXT PRIMARY KEY,
                character_name TEXT,
                user_id TEXT,
                dynamic_state TEXT, -- JSON: DynamicState
                character_memory TEXT, -- JSON: CharacterMemory
                last_interaction TEXT,
                session_count INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Enhanced Memory System
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enhanced_character_memory (
                id TEXT PRIMARY KEY,
                character_name TEXT,
                user_id TEXT,
                memory_type TEXT, -- 'preference', 'fact', 'achievement', 'relationship', 'learning_pattern'
                content TEXT,
                importance_score REAL, -- 0.0-10.0
                emotional_context TEXT, -- Associated emotional state
                confidence_score REAL, -- How confident we are in this memory
                created_at TEXT,
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0,
                validated BOOLEAN DEFAULT FALSE, -- Whether this memory has been confirmed
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Learning Interaction Analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_interactions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                character_name TEXT,
                message_id TEXT,
                user_emotion_detected TEXT, -- EmotionalState
                character_adaptation TEXT, -- What adaptation was applied
                response_effectiveness REAL, -- How effective was the response (0-1)
                user_engagement_score REAL, -- Engagement level detected (0-1)
                learning_progress_indicator REAL, -- Progress made in this interaction (0-1)
                timestamp TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (message_id) REFERENCES messages (id)
            )
        """)
        
        # A/B Testing Framework Tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personality_experiments (
                id TEXT PRIMARY KEY,
                experiment_name TEXT,
                character_name TEXT,
                variant_name TEXT, -- 'control', 'variant_a', 'variant_b', etc.
                personality_config TEXT, -- JSON: modified personality attributes
                start_date TEXT,
                end_date TEXT,
                active BOOLEAN DEFAULT TRUE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_participants (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                experiment_id TEXT,
                variant_assigned TEXT,
                assigned_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (experiment_id) REFERENCES personality_experiments (id)
            )
        """)
        
        # Performance Metrics for Characters
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS character_performance_metrics (
                id TEXT PRIMARY KEY,
                character_name TEXT,
                user_id TEXT,
                metric_type TEXT, -- 'engagement', 'learning_speed', 'user_satisfaction'
                metric_value REAL,
                measurement_period_start TEXT,
                measurement_period_end TEXT,
                recorded_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_character_personality(self, character: EnhancedCharacter) -> None:
        """Save enhanced character personality to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        personality_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Convert enums to serializable format
        core_attrs_dict = asdict(character.core_attributes)
        core_attrs_dict['patience_level'] = character.core_attributes.patience_level.name
        core_attrs_dict['default_response_style'] = character.core_attributes.default_response_style.value
        
        cursor.execute("""
            INSERT OR REPLACE INTO character_personalities
            (id, character_name, archetype, core_attributes, knowledge_domains,
             teaching_specialties, conversation_starters, adaptation_prompts,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            personality_id,
            character.name,
            character.archetype,
            json.dumps(core_attrs_dict),
            json.dumps(character.knowledge_domains),
            json.dumps(character.teaching_specialties),
            json.dumps(character.conversation_starters),
            json.dumps(character.adaptation_prompts),
            now,
            now
        ))
        
        conn.commit()
        conn.close()
    
    def load_character_personality(self, character_name: str) -> Optional[EnhancedCharacter]:
        """Load enhanced character personality from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM character_personalities WHERE character_name = ?
        """, (character_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Reconstruct character from database
        character = EnhancedCharacter()
        character.name = row[1]
        character.archetype = row[2]
        
        # Deserialize core attributes and reconstruct enums
        attrs_data = json.loads(row[3])
        
        # Convert enum strings back to enums
        if 'patience_level' in attrs_data:
            from character_personality_framework import PatientLevel
            attrs_data['patience_level'] = PatientLevel[attrs_data['patience_level']]
        
        if 'default_response_style' in attrs_data:
            from character_personality_framework import ResponseStyle
            attrs_data['default_response_style'] = ResponseStyle(attrs_data['default_response_style'])
        
        character.core_attributes = BehavioralAttributes(**attrs_data)
        
        character.knowledge_domains = json.loads(row[4])
        character.teaching_specialties = json.loads(row[5])
        character.conversation_starters = json.loads(row[6])
        character.adaptation_prompts = json.loads(row[7])
        
        return character
    
    def save_character_state(self, character: EnhancedCharacter, user_id: str) -> None:
        """Save character's dynamic state and memory for a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        state_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Convert enums to serializable format
        dynamic_state_dict = asdict(character.dynamic_state)
        dynamic_state_dict['detected_user_emotion'] = character.dynamic_state.detected_user_emotion.value
        
        cursor.execute("""
            INSERT OR REPLACE INTO character_states
            (id, character_name, user_id, dynamic_state, character_memory,
             last_interaction, session_count, total_messages)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            state_id,
            character.name,
            user_id,
            json.dumps(dynamic_state_dict),
            json.dumps(asdict(character.character_memory)),
            now,
            character.dynamic_state.messages_this_session,
            getattr(character, 'total_messages', 0)
        ))
        
        conn.commit()
        conn.close()
    
    def load_character_state(self, character_name: str, user_id: str) -> Tuple[Optional[DynamicState], Optional[CharacterMemory]]:
        """Load character's dynamic state and memory for a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT dynamic_state, character_memory FROM character_states
            WHERE character_name = ? AND user_id = ?
            ORDER BY last_interaction DESC LIMIT 1
        """, (character_name, user_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None, None
        
        # Deserialize and reconstruct enums
        dynamic_state_dict = json.loads(row[0])
        if 'detected_user_emotion' in dynamic_state_dict:
            from character_personality_framework import EmotionalState
            dynamic_state_dict['detected_user_emotion'] = EmotionalState(dynamic_state_dict['detected_user_emotion'])
        
        dynamic_state = DynamicState(**dynamic_state_dict)
        character_memory = CharacterMemory(**json.loads(row[1]))
        
        return dynamic_state, character_memory
    
    def store_enhanced_memory(self, character_name: str, user_id: str, 
                            memory_type: str, content: str, importance: float = 5.0,
                            emotional_context: str = "neutral", confidence: float = 0.8) -> None:
        """Store enhanced character memory with additional context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        memory_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO enhanced_character_memory
            (id, character_name, user_id, memory_type, content, importance_score,
             emotional_context, confidence_score, created_at, last_accessed, access_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id, character_name, user_id, memory_type, content, importance,
            emotional_context, confidence, now, now, 0
        ))
        
        conn.commit()
        conn.close()
    
    def get_enhanced_memories(self, character_name: str, user_id: str, 
                            limit: int = 10, min_importance: float = 3.0) -> List[Dict]:
        """Get enhanced character memories with filtering"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT content, memory_type, importance_score, emotional_context,
                   confidence_score, created_at, access_count
            FROM enhanced_character_memory
            WHERE character_name = ? AND user_id = ? AND importance_score >= ?
            ORDER BY importance_score DESC, confidence_score DESC, last_accessed DESC
            LIMIT ?
        """, (character_name, user_id, min_importance, limit))
        
        rows = cursor.fetchall()
        
        # Update access count
        memory_ids = []
        cursor.execute("""
            SELECT id FROM enhanced_character_memory
            WHERE character_name = ? AND user_id = ? AND importance_score >= ?
            ORDER BY importance_score DESC, confidence_score DESC, last_accessed DESC
            LIMIT ?
        """, (character_name, user_id, min_importance, limit))
        
        ids = cursor.fetchall()
        for id_row in ids:
            cursor.execute("""
                UPDATE enhanced_character_memory 
                SET access_count = access_count + 1, last_accessed = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), id_row[0]))
        
        conn.commit()
        conn.close()
        
        memories = []
        for row in rows:
            memories.append({
                'content': row[0],
                'type': row[1],
                'importance': row[2],
                'emotional_context': row[3],
                'confidence': row[4],
                'created_at': row[5],
                'access_count': row[6]
            })
        
        return memories
    
    def record_learning_interaction(self, user_id: str, character_name: str, 
                                  message_id: str, user_emotion: EmotionalState,
                                  adaptation_applied: str, effectiveness: float,
                                  engagement: float, progress: float) -> None:
        """Record detailed learning interaction analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        interaction_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO learning_interactions
            (id, user_id, character_name, message_id, user_emotion_detected,
             character_adaptation, response_effectiveness, user_engagement_score,
             learning_progress_indicator, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interaction_id, user_id, character_name, message_id, user_emotion.value,
            adaptation_applied, effectiveness, engagement, progress,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def create_ab_test_experiment(self, experiment_name: str, character_name: str,
                                variants: Dict[str, Dict]) -> str:
        """Create A/B test experiment for character personality variants"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        experiment_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Create experiment record
        cursor.execute("""
            INSERT INTO personality_experiments
            (id, experiment_name, character_name, variant_name, personality_config,
             start_date, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (experiment_id, experiment_name, character_name, "control", 
              json.dumps({}), now, True))
        
        # Create variant records
        for variant_name, config in variants.items():
            variant_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO personality_experiments
                (id, experiment_name, character_name, variant_name, personality_config,
                 start_date, active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (variant_id, experiment_name, character_name, variant_name,
                  json.dumps(config), now, True))
        
        conn.commit()
        conn.close()
        
        return experiment_id
    
    def assign_user_to_experiment(self, user_id: str, experiment_name: str) -> str:
        """Assign user to an experiment variant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get available variants
        cursor.execute("""
            SELECT id, variant_name FROM personality_experiments
            WHERE experiment_name = ? AND active = TRUE
        """, (experiment_name,))
        
        variants = cursor.fetchall()
        if not variants:
            conn.close()
            return "control"
        
        # Simple random assignment (could be more sophisticated)
        import random
        selected_variant = random.choice(variants)
        variant_id, variant_name = selected_variant
        
        # Record assignment
        assignment_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO experiment_participants
            (id, user_id, experiment_id, variant_assigned, assigned_at)
            VALUES (?, ?, ?, ?, ?)
        """, (assignment_id, user_id, variant_id, variant_name,
              datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return variant_name
    
    def get_user_experiment_variant(self, user_id: str, experiment_name: str) -> Optional[str]:
        """Get user's assigned experiment variant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ep.variant_assigned FROM experiment_participants ep
            JOIN personality_experiments pe ON ep.experiment_id = pe.id
            WHERE ep.user_id = ? AND pe.experiment_name = ?
            ORDER BY ep.assigned_at DESC LIMIT 1
        """, (user_id, experiment_name))
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    def record_character_performance_metric(self, character_name: str, user_id: str,
                                          metric_type: str, value: float,
                                          period_start: str, period_end: str) -> None:
        """Record character performance metrics for analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metric_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO character_performance_metrics
            (id, character_name, user_id, metric_type, metric_value,
             measurement_period_start, measurement_period_end, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metric_id, character_name, user_id, metric_type, value,
            period_start, period_end, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_character_performance_analytics(self, character_name: str, 
                                          days_back: int = 30) -> Dict[str, List]:
        """Get character performance analytics for the last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate date range
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        cursor.execute("""
            SELECT metric_type, metric_value, recorded_at, user_id
            FROM character_performance_metrics
            WHERE character_name = ? 
            AND recorded_at >= ? AND recorded_at <= ?
            ORDER BY recorded_at DESC
        """, (character_name, start_date.isoformat(), end_date.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        analytics = {
            'engagement': [],
            'learning_speed': [],
            'user_satisfaction': [],
            'total_interactions': len(rows)
        }
        
        for row in rows:
            metric_type, value, recorded_at, user_id = row
            if metric_type in analytics:
                analytics[metric_type].append({
                    'value': value,
                    'timestamp': recorded_at,
                    'user_id': user_id
                })
        
        return analytics

if __name__ == "__main__":
    # Test the enhanced database
    db = EnhancedEduChatDatabase("test_enhanced.db")
    
    # Test character personality storage
    from character_personality_framework import CharacterFactory
    
    aino = CharacterFactory.create_aino_enhanced()
    db.save_character_personality(aino)
    
    loaded_aino = db.load_character_personality("Aino")
    print(f"Loaded character: {loaded_aino.name}, Age: {loaded_aino.core_attributes.age}")
    
    # Test enhanced memory storage
    db.store_enhanced_memory("Aino", "test_user", "preference", 
                           "User enjoys learning about Finnish culture",
                           importance=8.0, emotional_context="excited")
    
    memories = db.get_enhanced_memories("Aino", "test_user")
    print(f"Retrieved {len(memories)} memories")
    
    print("Enhanced database system ready!")
