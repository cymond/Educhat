"""
Migration Script: Current EduChat Database → Enhanced Character Personality Framework
Safely migrates existing data while adding new CPF capabilities
"""

import sqlite3
import json
from datetime import datetime
import shutil
import os
from enhanced_database_models import EnhancedEduChatDatabase
from character_personality_framework import CharacterFactory, get_enhanced_character_set

class DatabaseMigration:
    """Handles migration from current EduChat DB to enhanced CPF database"""
    
    def __init__(self, current_db_path: str = "educhat.db", 
                 enhanced_db_path: str = "educhat_enhanced.db"):
        self.current_db_path = current_db_path
        self.enhanced_db_path = enhanced_db_path
        self.backup_db_path = f"{current_db_path}.backup_{int(datetime.now().timestamp())}"
    
    def run_migration(self, create_backup: bool = True) -> bool:
        """
        Run complete migration process
        Returns: True if successful, False if failed
        """
        try:
            print("🚀 Starting EduChat Database Migration to Enhanced CPF...")
            
            # Step 1: Create backup
            if create_backup and os.path.exists(self.current_db_path):
                print(f"📦 Creating backup: {self.backup_db_path}")
                shutil.copy2(self.current_db_path, self.backup_db_path)
            
            # Step 2: Initialize enhanced database
            print("🏗️  Initializing enhanced database...")
            enhanced_db = EnhancedEduChatDatabase(self.enhanced_db_path)
            
            # Step 3: Migrate existing data
            if os.path.exists(self.current_db_path):
                print("📊 Migrating existing data...")
                self._migrate_existing_data(enhanced_db)
            
            # Step 4: Initialize enhanced characters
            print("🎭 Initializing enhanced characters...")
            self._initialize_enhanced_characters(enhanced_db)
            
            # Step 5: Convert old memories to enhanced format
            print("🧠 Converting character memories...")
            self._migrate_character_memories(enhanced_db)
            
            print("✅ Migration completed successfully!")
            print(f"   Enhanced database: {self.enhanced_db_path}")
            if create_backup and os.path.exists(self.backup_db_path):
                print(f"   Backup saved: {self.backup_db_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            return False
    
    def _migrate_existing_data(self, enhanced_db: EnhancedEduChatDatabase) -> None:
        """Migrate users, conversations, and messages from current database"""
        
        # Connect to current database
        current_conn = sqlite3.connect(self.current_db_path)
        current_cursor = current_conn.cursor()
        
        # Connect to enhanced database
        enhanced_conn = sqlite3.connect(enhanced_db.db_path)
        enhanced_cursor = enhanced_conn.cursor()
        
        # Migrate users
        print("   👥 Migrating users...")
        current_cursor.execute("SELECT * FROM users")
        users = current_cursor.fetchall()
        
        for user in users:
            enhanced_cursor.execute("""
                INSERT OR IGNORE INTO users 
                (id, name, age_group, learning_preferences, privacy_settings, created_at, last_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, user)
        
        # Migrate conversations
        print("   💬 Migrating conversations...")
        try:
            current_cursor.execute("SELECT * FROM conversations")
            conversations = current_cursor.fetchall()
            
            for conv in conversations:
                enhanced_cursor.execute("""
                    INSERT OR IGNORE INTO conversations
                    (id, user_id, title, topic, character_set, conversation_mode, 
                     status, started_at, ended_at, total_rounds, total_messages, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, conv)
        except sqlite3.OperationalError:
            print("     ⚠️  No conversations table found in current database")
        
        # Migrate messages
        print("   📝 Migrating messages...")
        try:
            current_cursor.execute("SELECT * FROM messages")
            messages = current_cursor.fetchall()
            
            for msg in messages:
                enhanced_cursor.execute("""
                    INSERT OR IGNORE INTO messages
                    (id, conversation_id, sender, content, timestamp, 
                     round_number, message_order, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, msg)
        except sqlite3.OperationalError:
            print("     ⚠️  No messages table found in current database")
        
        enhanced_conn.commit()
        current_conn.close()
        enhanced_conn.close()
    
    def _initialize_enhanced_characters(self, enhanced_db: EnhancedEduChatDatabase) -> None:
        """Initialize enhanced character personalities in database"""
        
        enhanced_characters = get_enhanced_character_set()
        
        for name, character in enhanced_characters.items():
            print(f"   🎭 Setting up {name}...")
            enhanced_db.save_character_personality(character)
    
    def _migrate_character_memories(self, enhanced_db: EnhancedEduChatDatabase) -> None:
        """Convert old character memories to enhanced format"""
        
        if not os.path.exists(self.current_db_path):
            return
        
        current_conn = sqlite3.connect(self.current_db_path)
        current_cursor = current_conn.cursor()
        
        try:
            current_cursor.execute("SELECT * FROM character_memory")
            old_memories = current_cursor.fetchall()
            
            for memory in old_memories:
                # Old format: id, character_name, user_id, memory_type, content, importance_score, created_at, last_accessed
                old_id, character_name, user_id, memory_type, content, importance, created_at, last_accessed = memory
                
                # Convert to enhanced format with additional context
                enhanced_db.store_enhanced_memory(
                    character_name=character_name,
                    user_id=user_id,
                    memory_type=memory_type,
                    content=content,
                    importance=float(importance),
                    emotional_context="neutral",  # Default for migrated memories
                    confidence=0.8  # Default confidence for existing memories
                )
                
                print(f"     🧠 Migrated memory: {character_name} -> {content[:50]}...")
        
        except sqlite3.OperationalError:
            print("     ⚠️  No character_memory table found in current database")
        
        current_conn.close()
    
    def verify_migration(self) -> Dict[str, Any]:
        """Verify migration was successful and return stats"""
        
        if not os.path.exists(self.enhanced_db_path):
            return {"success": False, "error": "Enhanced database not found"}
        
        enhanced_conn = sqlite3.connect(self.enhanced_db_path)
        cursor = enhanced_conn.cursor()
        
        stats = {}
        
        # Count records in each table
        tables = ['users', 'conversations', 'messages', 'character_personalities', 
                 'enhanced_character_memory']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
            except sqlite3.OperationalError:
                stats[table] = 0
        
        # Check character personalities
        cursor.execute("SELECT character_name FROM character_personalities")
        characters = [row[0] for row in cursor.fetchall()]
        stats['characters_initialized'] = characters
        
        enhanced_conn.close()
        
        return {
            "success": True,
            "stats": stats,
            "enhanced_db_path": self.enhanced_db_path,
            "backup_path": self.backup_db_path if hasattr(self, 'backup_db_path') else None
        }
    
    def rollback_migration(self) -> bool:
        """Rollback to original database if migration failed"""
        try:
            if os.path.exists(self.backup_db_path):
                shutil.copy2(self.backup_db_path, self.current_db_path)
                print(f"✅ Rollback completed. Restored from {self.backup_db_path}")
                return True
            else:
                print("❌ No backup found for rollback")
                return False
        except Exception as e:
            print(f"❌ Rollback failed: {str(e)}")
            return False

def create_test_environment():
    """Create a test environment with sample data for migration testing"""
    
    # Create test current database with sample data
    test_db_path = "test_current_educhat.db"
    
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Create old schema
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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_memory (
            id TEXT PRIMARY KEY,
            character_name TEXT,
            user_id TEXT,
            memory_type TEXT,
            content TEXT,
            importance_score INTEGER,
            created_at TEXT,
            last_accessed TEXT
        )
    """)
    
    # Insert test data
    import uuid
    now = datetime.now().isoformat()
    
    test_user_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (test_user_id, "Test Family", "adult", '{}', '{}', now, now))
    
    # Insert test memories
    test_memories = [
        ("Aino", test_user_id, "preference", "User enjoys learning about Finnish culture", 8, now, now),
        ("Mase", test_user_id, "fact", "User is interested in science", 6, now, now),
        ("Anna", test_user_id, "achievement", "User successfully learned about investing", 7, now, now)
    ]
    
    for memory in test_memories:
        memory_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO character_memory VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (memory_id,) + memory)
    
    conn.commit()
    conn.close()
    
    return test_db_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate EduChat database to Enhanced CPF")
    parser.add_argument("--test", action="store_true", help="Run migration test with sample data")
    parser.add_argument("--current-db", default="educhat.db", help="Path to current database")
    parser.add_argument("--enhanced-db", default="educhat_enhanced.db", help="Path to enhanced database")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backup")
    parser.add_argument("--verify", action="store_true", help="Only verify existing migration")
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Creating test environment...")
        test_db = create_test_environment()
        migration = DatabaseMigration(test_db, "test_enhanced.db")
        success = migration.run_migration()
        
        if success:
            verification = migration.verify_migration()
            print("\n📊 Migration Verification:")
            print(json.dumps(verification, indent=2))
    
    elif args.verify:
        migration = DatabaseMigration(args.current_db, args.enhanced_db)
        verification = migration.verify_migration()
        print("📊 Migration Verification:")
        print(json.dumps(verification, indent=2))
    
    else:
        migration = DatabaseMigration(args.current_db, args.enhanced_db)
        success = migration.run_migration(create_backup=not args.no_backup)
        
        if success:
            verification = migration.verify_migration()
            print("\n📊 Migration Verification:")
            print(json.dumps(verification, indent=2))
        else:
            print("\n🔄 Would you like to rollback? (y/N)")
            response = input().lower()
            if response == 'y':
                migration.rollback_migration()
