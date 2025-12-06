"""
EduChat - AI Educational Group Chat Platform
Built with Streamlit for interactive learning conversations
Now with persistent user profiles and conversation history!
"""

import streamlit as st
import asyncio
import time
import random
import json
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd
from dotenv import load_dotenv

# Import our new database models
from database_models import EduChatDatabase, UserManager, User, ConversationRecord

# Load environment variables from .env file
load_dotenv()

# Initialize database
@st.cache_resource
def init_database():
    """Initialize database connection (cached for performance)"""
    return EduChatDatabase()

# Configure Streamlit
st.set_page_config(
    page_title="EduChat - AI Learning Companions", 
    page_icon="ðŸŽ“",
    layout="wide",
    initial_sidebar_state="expanded"
)

@dataclass
class Character:
    """Character definition with personality and behavior patterns"""
    name: str
    description: str
    speaking_style: str
    color: str
    personality_traits: List[str] = field(default_factory=list)
    knowledge_domains: List[str] = field(default_factory=list)
    
    def get_style_prompt(self) -> str:
        """Generate AI prompt style instructions for this character"""
        return f"""
        You are {self.name}, a character in an educational group chat.
        
        Character Description: {self.description}
        Speaking Style: {self.speaking_style}
        Personality Traits: {', '.join(self.personality_traits)}
        Knowledge Areas: {', '.join(self.knowledge_domains)}
        
        IMPORTANT: Stay completely in character. Keep responses conversational and brief (1-3 sentences).
        """

@dataclass 
class Message:
    """Chat message with metadata"""
    sender: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    character_color: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ConversationState:
    """Enhanced conversation manager with @mention detection and targeted responses"""
    
    def __init__(self):
        self.characters = self._create_default_characters()
        self.current_round = 0
        self.max_rounds = 3
        self.speaker_queue = []
        self.current_speaker_index = 0
        self.conversation_mode = "balanced"
        self.pending_user_message = None
        self.mentioned_characters = set()  # Track @mentions
        self.is_targeted_message = False   # Whether message targets specific characters
        
    def _create_default_characters(self) -> Dict[str, Character]:
        """Create the default character set for Finnish learning"""
        return {
            "Aino": Character(
                name="Aino",
                description="Native Finnish speaker, patient teacher, explains cultural context",
                speaking_style="Keep responses very short (1-2 sentences max). Patient and encouraging. Include Finnish cultural insights.",
                color="#E3F2FD",  # Light blue
                personality_traits=["patient", "encouraging", "cultural_expert"],
                knowledge_domains=["finnish_language", "culture", "pronunciation"]
            ),
            "Mase": Character(
                name="Mase", 
                description="Young adult, surprisingly knowledgeable, jokes regularly, extremely brief",
                speaking_style="Keep responses very short (1-2 sentences max). Drop knowledge casually. Make jokes. Leave things unsaid to prompt follow-ups.",
                color="#E8F5E8",  # Light green
                personality_traits=["witty", "brief", "knowledgeable"],
                knowledge_domains=["science", "technology", "trivia"]
            ),
            "Anna": Character(
                name="Anna",
                description="Middle-aged mother, expert investor, fitness enthusiast, vegan, wise", 
                speaking_style="Speak plainly with Warren Buffett-like clarity. Offer calm, pragmatic wisdom. Reference fitness/discipline occasionally.",
                color="#FFF3E0",  # Light orange
                personality_traits=["wise", "practical", "calm"],
                knowledge_domains=["finance", "health", "life_advice"]
            ),
            "Bee": Character(
                name="Bee",
                description="Late 20s female, data scientist, Python programmer, endurance athlete",
                speaking_style="Share tech developments concisely. Explain concepts well. Mention endurance training. 'Train harder, not smarter.'",
                color="#FCE4EC",  # Light pink
                personality_traits=["technical", "athletic", "analytical"],
                knowledge_domains=["data_science", "programming", "sports"]
            )
        }
    
    def detect_mentions(self, user_message: str) -> set:
        """
        Detect @mentions in user message
        Supports various mention formats:
        - @Aino, @Bee, @Mase, @Anna
        - Case insensitive
        - Partial matches (e.g., @ai for Aino)
        """
        import re
        mentions = set()
        message_lower = user_message.lower()
        
        # Direct @mentions pattern
        mention_pattern = r'@(\w+)'
        found_mentions = re.findall(mention_pattern, user_message, re.IGNORECASE)
        
        for mention in found_mentions:
            mention_lower = mention.lower()
            
            # Exact match
            for char_name in self.characters.keys():
                if mention_lower == char_name.lower():
                    mentions.add(char_name)
                    break
            
            # Partial match (first few characters)
            if mention not in [char.lower() for char in mentions]:
                for char_name in self.characters.keys():
                    if char_name.lower().startswith(mention_lower) and len(mention_lower) >= 2:
                        mentions.add(char_name)
                        break
        
        # Also check for direct character name mentions without @
        for char_name in self.characters.keys():
            # Look for character name mentioned naturally in text
            name_patterns = [
                f"\\b{char_name.lower()}\\b",
                f"\\b{char_name.lower()},",
                f"^{char_name.lower()}\\b",
                f"\\b{char_name.lower()}:"
            ]
            
            for pattern in name_patterns:
                if re.search(pattern, message_lower):
                    mentions.add(char_name)
                    break
        
        return mentions
    
    def should_character_respond(self, character_name: str, user_message: str, mentioned_chars: set) -> bool:
        """
        Determine if a character should respond based on mentions and relevance
        """
        # If specific characters were mentioned, only they should respond
        if mentioned_chars:
            return character_name in mentioned_chars
        
        # For general messages, apply intelligent filtering based on content relevance
        message_lower = user_message.lower()
        character = self.characters[character_name]
        
        # Character-specific keyword triggers
        relevance_keywords = {
            "Aino": ["finnish", "suomi", "language", "culture", "pronunciation", "grammar", "translate"],
            "Mase": ["science", "technology", "interesting", "knowledge", "fact", "explain", "how", "why"],
            "Anna": ["advice", "wisdom", "invest", "money", "health", "fitness", "practical", "life"],
            "Bee": ["data", "analysis", "programming", "python", "technical", "algorithm", "math", "stats"]
        }
        
        # Check if message contains relevant keywords for this character
        char_keywords = relevance_keywords.get(character_name, [])
        keyword_matches = sum(1 for keyword in char_keywords if keyword in message_lower)
        
        # Probability-based selection for general messages
        base_probability = 0.6  # Base chance for any character to respond
        keyword_bonus = min(keyword_matches * 0.2, 0.3)  # Bonus for relevant keywords
        
        final_probability = base_probability + keyword_bonus
        
        return random.random() < final_probability
    
    def initialize_round(self, user_message: str):
        """Start a new round with user message and @mention detection"""
        self.pending_user_message = user_message
        
        # Detect @mentions
        self.mentioned_characters = self.detect_mentions(user_message)
        self.is_targeted_message = len(self.mentioned_characters) > 0
        
        # Build speaker queue based on mentions and relevance
        if self.is_targeted_message:
            # Only mentioned characters respond
            self.speaker_queue = list(self.mentioned_characters)
        else:
            # Intelligent selection based on content relevance
            responding_characters = []
            for char_name in self.characters.keys():
                if self.should_character_respond(char_name, user_message, self.mentioned_characters):
                    responding_characters.append(char_name)
            
            # Ensure at least one character responds, but not necessarily all
            if not responding_characters:
                responding_characters = [random.choice(list(self.characters.keys()))]
            elif len(responding_characters) > 3:
                # Limit to max 3 characters for general messages
                responding_characters = random.sample(responding_characters, 3)
            
            self.speaker_queue = responding_characters
        
        # Randomize order for more natural conversation flow
        random.shuffle(self.speaker_queue)
        self.current_speaker_index = 0
        self.current_round += 1
        
    def get_next_speaker(self) -> Optional[Character]:
        """Get the next character to speak"""
        if self.current_speaker_index >= len(self.speaker_queue):
            return None
        
        speaker_name = self.speaker_queue[self.current_speaker_index]
        self.current_speaker_index += 1
        return self.characters[speaker_name]
    
    def is_round_complete(self) -> bool:
        """Check if current round is finished"""
        return self.current_speaker_index >= len(self.speaker_queue)
    
    def should_end_conversation(self) -> bool:
        """Check if conversation should end"""
        return self.current_round >= self.max_rounds
    
    def reset_for_new_topic(self):
        """Reset conversation state for new topic"""
        self.current_round = 0
        self.speaker_queue = []
        self.current_speaker_index = 0
        self.pending_user_message = None
        self.mentioned_characters = set()
        self.is_targeted_message = False
    
    def get_mention_summary(self) -> str:
        """Get a summary of current mention status for debugging"""
        if self.is_targeted_message:
            return f"🎯 Targeted to: {', '.join(self.mentioned_characters)}"
        else:
            return f"💬 General message (responding: {', '.join(self.speaker_queue)})"

def generate_ai_response(character: Character, conversation_context: str, user_message: str, 
                        is_mentioned: bool = True, mentioned_characters: set = None) -> str:
    """Generate AI response using Anthropic API with character personality"""
    
    # Check if we have an API key configured
    # Try st.secrets first (Streamlit Cloud), then environment variables
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        model = st.secrets.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        st.info("ðŸ”‘ Using Streamlit secrets for API key")
    except:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        st.info("ðŸ”‘ Using environment variables for API key")
    
    # Debug info for Streamlit Cloud (remove this after testing)
    if api_key:
        st.info(f"ðŸ”‘ API Key found: {api_key[:10]}... (length: {len(api_key)})")
        st.info(f"ðŸ¤– Using model: {model}")
    
    if not api_key or api_key == 'your_anthropic_api_key_here':
        # Fallback to placeholder responses if no API key
        st.warning("âš ï¸ Add ANTHROPIC_API_KEY to .env file for real AI responses")
        fallback_responses = {
            "Aino": f"Hei! About '{user_message}' - in Finnish we say 'Tervetuloa oppimaan!' (Welcome to learning!)",
            "Mase": f"*drops knowledge* Yeah, {user_message.lower()} is actually pretty interesting...",
            "Anna": f"Here's practical wisdom about {user_message.lower()}: focus on the fundamentals first.",
            "Bee": f"If I analyze {user_message.lower()} like data... there are patterns here worth exploring."
        }
        return fallback_responses.get(character.name, "I'd love to help with that!")
    
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        
        # Build mention context
        mention_context = ""
        if mentioned_characters:
            if len(mentioned_characters) > 0:
                mentioned_list = ", ".join(mentioned_characters)
                if is_mentioned:
                    mention_context = f"\n\nIMPORTANT: You were specifically mentioned/addressed in this message, so respond directly and helpfully."
                else:
                    mention_context = f"\n\nNOTE: This message was directed to {mentioned_list}, not you. Only respond if your specific expertise is absolutely needed."
        
        # Build the character-specific prompt
        system_prompt = f"""You are participating in an educational group chat as the character {character.name}.

{character.get_style_prompt()}

CRITICAL INSTRUCTIONS:
- Stay completely in character as {character.name}
- Keep responses conversational and brief (1-3 sentences)
- Be helpful and educational
- If you're Aino, include Finnish language/cultural elements naturally
- If you're Mase, be witty but informative
- If you're Anna, offer practical wisdom
- If you're Bee, bring analytical/data perspectives

{mention_context}

Recent conversation context:
{conversation_context}

The user just said: "{user_message}"

Respond naturally as {character.name} would."""

        # Call Anthropic API  
        response = client.messages.create(
            model=model,
            max_tokens=150,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        return response.content[0].text.strip()
        
    except Exception as e:
        # Graceful fallback if API call fails
        st.error(f"ðŸ”„ AI service error: {str(e)}")
        return f"[{character.name} would respond here, but I'm having connection issues. Please try again!]"

def show_admin_panel(db: 'EduChatDatabase', current_user: User):
    """Database administration panel for monitoring and debugging"""
    
    st.subheader("ðŸ“Š Database Overview")
    
    # Quick stats
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    # Count records in each table
    tables_info = {}
    for table in ['users', 'conversations', 'messages', 'character_memory']:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        tables_info[table] = count
    
    # Display stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Users", tables_info['users'])
    with col2:
        st.metric("Conversations", tables_info['conversations'])
    with col3:
        st.metric("Messages", tables_info['messages'])
    with col4:
        st.metric("Memories", tables_info['character_memory'])
    
    # Table browser
    st.subheader("ðŸ” Table Explorer")
    table_options = ['users', 'conversations', 'messages', 'character_memory', 'learning_progress']
    selected_table = st.selectbox("Select table to view:", table_options)
    
    if selected_table:
        # Show table structure first
        cursor.execute(f"PRAGMA table_info({selected_table})")
        schema = cursor.fetchall()
        
        with st.expander(f"ðŸ“‹ {selected_table} Schema"):
            schema_df = pd.DataFrame(schema, columns=['ID', 'Name', 'Type', 'NotNull', 'Default', 'PK'])
            st.dataframe(schema_df, use_container_width=True)
        
        # Show recent data
        limit = st.slider(f"Show last N records from {selected_table}:", 1, 50, 10)
        
        try:
            if selected_table == 'messages':
                # Special handling for messages - join with conversation info
                query = """
                SELECT m.id, m.sender, m.content, m.timestamp, c.title as conversation_title, u.name as user_name
                FROM messages m
                LEFT JOIN conversations c ON m.conversation_id = c.id
                LEFT JOIN users u ON c.user_id = u.id
                ORDER BY m.timestamp DESC
                LIMIT ?
                """
                df = pd.read_sql(query, conn, params=(limit,))
                
                # Truncate long messages for display
                if 'content' in df.columns:
                    df['content'] = df['content'].str[:100] + '...'
                    
            elif selected_table == 'character_memory':
                # Enhanced character memory view
                query = """
                SELECT cm.character_name, cm.memory_type, cm.content, cm.importance_score, 
                       cm.created_at, u.name as user_name
                FROM character_memory cm
                LEFT JOIN users u ON cm.user_id = u.id
                ORDER BY cm.created_at DESC
                LIMIT ?
                """
                df = pd.read_sql(query, conn, params=(limit,))
                
            else:
                # Standard table query
                df = pd.read_sql(f"SELECT * FROM {selected_table} ORDER BY rowid DESC LIMIT ?", conn, params=(limit,))
            
            st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error querying {selected_table}: {str(e)}")
    
    # Character Memory Analysis
    st.subheader("ðŸ§  Character Memory Analysis")
    
    # Memory by character
    memory_query = """
    SELECT character_name, COUNT(*) as memory_count, AVG(importance_score) as avg_importance
    FROM character_memory 
    GROUP BY character_name
    ORDER BY memory_count DESC
    """
    memory_stats = pd.read_sql(memory_query, conn)
    
    if not memory_stats.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Memories by Character:**")
            st.dataframe(memory_stats, use_container_width=True)
        
        with col2:
            st.write("**Memory Distribution:**")
            st.bar_chart(memory_stats.set_index('character_name')['memory_count'])
    
    # Recent Activity Analysis
    st.subheader("ðŸ“ˆ Activity Analysis")
    
    # Messages per day
    activity_query = """
    SELECT DATE(timestamp) as date, COUNT(*) as message_count
    FROM messages 
    WHERE timestamp >= date('now', '-7 days')
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    """
    activity_df = pd.read_sql(activity_query, conn)
    
    if not activity_df.empty:
        st.write("**Messages per Day (Last 7 Days):**")
        st.bar_chart(activity_df.set_index('date')['message_count'])
    
    # User engagement
    engagement_query = """
    SELECT u.name, COUNT(DISTINCT c.id) as conversation_count, 
           COUNT(m.id) as total_messages, 
           MAX(u.last_active) as last_active
    FROM users u
    LEFT JOIN conversations c ON u.id = c.user_id
    LEFT JOIN messages m ON c.id = m.conversation_id
    GROUP BY u.id, u.name
    ORDER BY total_messages DESC
    """
    engagement_df = pd.read_sql(engagement_query, conn)
    
    if not engagement_df.empty:
        st.write("**User Engagement:**")
        st.dataframe(engagement_df, use_container_width=True)
    
    # Database maintenance
    st.subheader("ðŸ› ï¸ Database Maintenance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("ðŸ§¹ Clean Old Sessions"):
            # Clean up old temporary data if needed
            st.success("Cleanup completed!")
    
    with col2:
        if st.button("ðŸ“Š Export Data"):
            # Export data to CSV
            export_data = {
                'users': pd.read_sql("SELECT * FROM users", conn),
                'conversations': pd.read_sql("SELECT * FROM conversations", conn),
                'character_memory': pd.read_sql("SELECT * FROM character_memory", conn)
            }
            st.success("Data exported! (Download functionality would be added here)")
    
    with col3:
        # Database file size
        import os
        if os.path.exists(db.db_path):
            size_mb = os.path.getsize(db.db_path) / (1024 * 1024)
            st.metric("DB Size", f"{size_mb:.2f} MB")
    
    # Raw SQL Query Interface
    st.subheader("ðŸ’» SQL Query Interface")
    with st.expander("Execute Custom SQL Query"):
        custom_query = st.text_area(
            "Enter SQL query:", 
            placeholder="SELECT * FROM users LIMIT 5;",
            help="Be careful with UPDATE/DELETE queries!"
        )
        
        if st.button("Execute Query") and custom_query:
            try:
                if custom_query.strip().upper().startswith(('SELECT', 'PRAGMA')):
                    result_df = pd.read_sql(custom_query, conn)
                    st.dataframe(result_df, use_container_width=True)
                else:
                    st.warning("Only SELECT and PRAGMA queries allowed for safety!")
            except Exception as e:
                st.error(f"Query error: {str(e)}")
    
    conn.close()

def display_message(message: Message):
    """Display a chat message with proper styling"""
    if message.sender == "You":
        # User message - right aligned, blue
        st.chat_message("user").write(message.content)
    else:
        # Character message - left aligned, with character styling  
        with st.chat_message("assistant"):
            # Character name as bold header
            st.markdown(f"**{message.sender}**")
            st.write(message.content)

def main():
    """Main Streamlit application with persistent user profiles"""
    
    # Initialize database and user manager
    db = init_database()
    user_manager = UserManager(db)
    
    # User selection/creation interface
    current_user = user_manager.show_user_selection()
    
    # If no user is selected, show welcome message and stop
    if not current_user:
        st.title("ðŸŽ“ Welcome to EduChat!")
        st.markdown("""
        ### Your AI Learning Companions
        
        EduChat helps you learn through conversations with AI characters who have distinct personalities:
        - **Aino** ðŸ‡«ðŸ‡® - Your Finnish language tutor and cultural guide
        - **Mase** ðŸ§  - Witty knowledge-dropper who makes learning fun  
        - **Anna** ðŸ’¡ - Wise advisor with practical life lessons
        - **Bee** ðŸ“Š - Data scientist who explains concepts analytically
        
        **ðŸ‘ˆ Create your profile in the sidebar to get started!**
        """)
        return
    
    # Initialize session state for this user
    if 'conversation_state' not in st.session_state:
        st.session_state.conversation_state = ConversationState()
    
    if 'messages' not in st.session_state or st.session_state.get('current_user_id') != current_user.id:
        # New user or user switched - load their conversation history
        st.session_state.current_user_id = current_user.id
        st.session_state.messages = []
        
        # Load most recent conversation or start fresh
        recent_conversations = db.get_user_conversations(current_user.id, 1)
        if recent_conversations:
            st.sidebar.info(f"ðŸ“š Found {len(db.get_user_conversations(current_user.id))} previous conversations")
        
        # Add personalized welcome message
        welcome_msg = Message(
            sender="System",
            content=f"Welcome back, {current_user.name}! ðŸŽ“ Your AI learning companions remember you. What would you like to explore today?",
            character_color="#F5F5F5"
        )
        st.session_state.messages.append(welcome_msg)
    
    if 'generating' not in st.session_state:
        st.session_state.generating = False
    
    # Sidebar for controls and analytics  
    with st.sidebar:
        st.title("ðŸŽ“ EduChat Controls")
        
        # User info and analytics
        user_manager.show_user_analytics(current_user)
        
        # Admin panel for database exploration (Pete only)
        if current_user.name.lower() == "pete":
            st.markdown("---")
            with st.expander("ðŸ”§ Database Admin Panel"):
                show_admin_panel(db, current_user)
        
        st.markdown("---")
        
        # Conversation settings
        st.subheader("Settings")
        conversation_mode = st.selectbox(
            "Conversation Mode",
            ["balanced", "focused", "casual"],
            index=0,
            help="How the characters should approach the conversation"
        )
        st.session_state.conversation_state.conversation_mode = conversation_mode
        
        max_rounds = st.slider("Rounds per topic", 1, 5, 3)
        st.session_state.conversation_state.max_rounds = max_rounds
        
        # Debug info for @mentions (show current conversation state)
        if hasattr(st.session_state.conversation_state, 'is_targeted_message'):
            if st.session_state.conversation_state.is_targeted_message or st.session_state.conversation_state.mentioned_characters:
                st.info(f"🎯 **@Mention Detection**\n{st.session_state.conversation_state.get_mention_summary()}")
        
        # Quick usage guide for @mentions
        with st.expander("📝 How to use @mentions"):
            st.markdown("""
            **Direct a question to specific characters:**
            - `@Aino` - Finnish language help
            - `@Mase` - Science & trivia  
            - `@Anna` - Life advice & wisdom
            - `@Bee` - Data & tech topics
            
            **Examples:**
            - `@Aino, how do I say hello in Finnish?`
            - `@Mase @Bee, explain quantum computing`
            - `Anna, I need career advice`
            """)
        
        # Character info with personalization hints
        st.subheader("Your Learning Companions")
        for char_name, char in st.session_state.conversation_state.characters.items():
            with st.expander(f"{char_name}"):
                st.write(f"**Role:** {char.description}")
                
                # Show character memories if available
                memories = db.get_character_memories(char_name, current_user.id, 2)
                if memories:
                    st.write("**Remembers about you:**")
                    for memory in memories:
                        st.write(f"â€¢ {memory['content']}")
                
                st.write(f"**Style:** {char.speaking_style[:100]}...")
        
        # Quick topic buttons with @mention targeting
        st.subheader("🚀 Quick Learning Topics")
        
        # Create a 2x2 grid for the 4 topics
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🇫🇮 F1 Adaptive Finnish", use_container_width=True, key="finnish_topic"):
                st.session_state.pending_topic = "@Aino, I'd like to practice Finnish today. Can you adapt the lesson to my current level and help me learn something new?"
            
            if st.button("🧠 Smart Study Tips", use_container_width=True, key="study_tips"):
                st.session_state.pending_topic = "@Anna, I need some practical wisdom about effective study strategies. What are your best tips for learning efficiently?"
        
        with col2:
            if st.button("📊 Data Deep Dive", use_container_width=True, key="data_dive"):
                st.session_state.pending_topic = "@Bee, I want to explore data science concepts. Can you explain something technical in a way that builds my understanding?"
                
            if st.button("🎯 Knowledge Challenge", use_container_width=True, key="knowledge_challenge"):
                st.session_state.pending_topic = "@Mase, surprise me with an interesting knowledge challenge! Give me something that will make me think and learn."

        # Analytics section
        if len(st.session_state.messages) > 1:
            st.subheader("ðŸ“Š Session Analytics")
            
            # Create simple analytics dataframe
            messages_df = pd.DataFrame([
                {
                    'sender': msg.sender,
                    'length': len(msg.content),
                    'timestamp': msg.timestamp
                } 
                for msg in st.session_state.messages
            ])
            
            st.metric("Messages This Session", len(messages_df))
            
            # Character participation
            char_counts = messages_df[messages_df['sender'] != 'You']['sender'].value_counts()
            if not char_counts.empty:
                st.write("**Character Participation:**")
                st.bar_chart(char_counts)
    
    # Main chat interface
    st.title("ðŸ’¬ Learning Conversation")
    
    # Display conversation history
    for message in st.session_state.messages:
        display_message(message)
    
    # Handle pending topic from quick buttons
    if 'pending_topic' in st.session_state:
        user_input = st.session_state.pending_topic
        del st.session_state.pending_topic
    else:
        # Chat input
        user_input = st.chat_input(
            "Ask a question or start a new topic...",
            disabled=st.session_state.generating
        )
    
    # Process user input
    if user_input and not st.session_state.generating:
        # Add user message
        user_msg = Message(sender="You", content=user_input)
        st.session_state.messages.append(user_msg)
        display_message(user_msg)
        
        # Initialize conversation round
        conv_state = st.session_state.conversation_state
        conv_state.initialize_round(user_input)
        
        # Generate AI responses with character memory
        st.session_state.generating = True
        
        # Progress indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            total_characters = len(conv_state.speaker_queue)
            
            for i in range(total_characters):
                character = conv_state.get_next_speaker()
                if not character:
                    break
                
                # Update progress
                progress = (i + 1) / total_characters
                progress_bar.progress(progress)
                status_text.text(f"{character.name} is thinking...")
                
                # Add typing delay for realism
                time.sleep(1.5)
                
                # Build conversation context with character memory
                conversation_context = "\n".join([
                    f"{msg.sender}: {msg.content}" 
                    for msg in st.session_state.messages[-5:]  # Last 5 messages
                ])
                
                # Get character memories to personalize response
                memories = db.get_character_memories(character.name, current_user.id, 3)
                memory_context = ""
                if memories:
                    memory_context = "You remember: " + "; ".join([m['content'] for m in memories])
                
                response = generate_ai_response(
                    character, 
                    conversation_context + "\n" + memory_context, 
                    user_input,
                    is_mentioned=character.name in conv_state.mentioned_characters,
                    mentioned_characters=conv_state.mentioned_characters
                )
                
                # Add character message
                char_msg = Message(
                    sender=character.name,
                    content=response,
                    character_color=character.color
                )
                st.session_state.messages.append(char_msg)
                display_message(char_msg)
                
                # Store character memory about this interaction
                if not response.startswith('[Error'):
                    # Simple memory extraction - in production we'd use more sophisticated analysis
                    if any(word in user_input.lower() for word in ['like', 'enjoy', 'love']):
                        db.store_character_memory(
                            character.name, current_user.id, 'preference',
                            f"User enjoys discussing {user_input.lower()}", 6
                        )
                    elif any(word in user_input.lower() for word in ['finnish', 'suomi']):
                        db.store_character_memory(
                            character.name, current_user.id, 'learning',
                            f"User practiced Finnish: {user_input[:50]}", 7
                        )
        
        finally:
            # Cleanup
            progress_bar.empty()
            status_text.empty()
            st.session_state.generating = False
            
            # Save conversation to database
            if current_user:
                conversation_record = ConversationRecord(
                    user_id=current_user.id,
                    title=f"Chat about: {user_input[:30]}...",
                    topic=user_input[:50],
                    character_set=[char.name for char in st.session_state.conversation_state.characters.values()],
                    conversation_mode=conversation_mode,
                    total_rounds=conv_state.current_round,
                    total_messages=len(st.session_state.messages),
                    messages=[{
                        'sender': msg.sender,
                        'content': msg.content,
                        'timestamp': msg.timestamp
                    } for msg in st.session_state.messages]
                )
                db.save_conversation(conversation_record)
            
            # Check if round/conversation is complete
            if conv_state.is_round_complete():
                if conv_state.should_end_conversation():
                    completion_msg = Message(
                        sender="System",
                        content=f"Great conversation, {current_user.name}! ðŸŽ‰ Ready for a new topic?",
                        character_color="#E8F5E8"
                    )
                    st.session_state.messages.append(completion_msg)
                    conv_state.reset_for_new_topic()
                else:
                    round_msg = Message(
                        sender="System", 
                        content=f"Round {conv_state.current_round} complete! Continue the conversation or start a new topic.",
                        character_color="#E8F5E8"
                    )
                    st.session_state.messages.append(round_msg)
            
            # Trigger rerun to show new messages
            st.rerun()

if __name__ == "__main__":
    main()
