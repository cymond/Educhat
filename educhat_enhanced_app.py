"""
EduChat Enhanced - AI Educational Chat Platform with Character Personality Framework
Enhanced version integrating multi-layered character personalities and adaptive learning
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

# Enhanced CPF imports
from enhanced_database_models import EnhancedEduChatDatabase
from enhanced_response_generator import EnhancedResponseGenerator, generate_enhanced_ai_response
from character_personality_framework import get_enhanced_character_set, EmotionalState
from database_models import UserManager, User, ConversationRecord

# Load environment variables from .env file
load_dotenv()

# Initialize enhanced database
@st.cache_resource
def init_enhanced_database():
    """Initialize enhanced database connection (cached for performance)"""
    return EnhancedEduChatDatabase()

# Configure Streamlit
st.set_page_config(
    page_title="EduChat Enhanced - AI Learning Companions", 
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

@dataclass 
class Message:
    """Chat message with metadata (keeping compatibility)"""
    sender: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    character_color: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class EnhancedConversationState:
    """Enhanced conversation flow management with CPF integration"""
    
    def __init__(self):
        self.enhanced_characters = get_enhanced_character_set()
        self.current_round = 0
        self.max_rounds = 3
        self.speaker_queue = []
        self.current_speaker_index = 0
        self.conversation_mode = "balanced"
        self.pending_user_message = None
        self.response_generator = None
        
    def initialize_response_generator(self, db: EnhancedEduChatDatabase):
        """Initialize the enhanced response generator"""
        if self.response_generator is None:
            self.response_generator = EnhancedResponseGenerator(db)
    
    def get_character_info(self, character_name: str) -> Dict[str, Any]:
        """Get character information for display"""
        if self.response_generator:
            return self.response_generator.get_character_for_streamlit(character_name)
        
        # Fallback to basic character info
        if character_name in self.enhanced_characters:
            char = self.enhanced_characters[character_name]
            return {
                'name': char.name,
                'archetype': char.archetype,
                'description': f"{char.core_attributes.occupation}, age {char.core_attributes.age}",
                'color': char.color,
                'knowledge_domains': char.knowledge_domains
            }
        return {}
    
    def initialize_round(self, user_message: str):
        """Start a new round with user message"""
        self.pending_user_message = user_message
        self.speaker_queue = list(self.enhanced_characters.keys())
        random.shuffle(self.speaker_queue)
        self.current_speaker_index = 0
        self.current_round += 1
        
    def get_next_speaker(self) -> Optional[str]:
        """Get the next character to speak"""
        if self.current_speaker_index >= len(self.speaker_queue):
            return None
        
        speaker_name = self.speaker_queue[self.current_speaker_index]
        self.current_speaker_index += 1
        return speaker_name
    
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

def show_enhanced_admin_panel(db: EnhancedEduChatDatabase, current_user: User):
    """Enhanced database administration panel with CPF analytics"""
    
    st.subheader("🎭 Enhanced Character Analytics")
    
    # Character performance metrics
    character_names = ["Aino", "Mase", "Anna", "Bee"]
    
    for char_name in character_names:
        with st.expander(f"📊 {char_name} Analytics"):
            # Get performance data (last 30 days)
            analytics = db.get_character_performance_analytics(char_name, days_back=30)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Interactions", analytics['total_interactions'])
                
                if analytics['engagement']:
                    avg_engagement = sum(m['value'] for m in analytics['engagement']) / len(analytics['engagement'])
                    st.metric("Avg Engagement", f"{avg_engagement:.2f}")
            
            with col2:
                if analytics['user_satisfaction']:
                    avg_satisfaction = sum(m['value'] for m in analytics['user_satisfaction']) / len(analytics['user_satisfaction'])
                    st.metric("Avg Satisfaction", f"{avg_satisfaction:.2f}")
                
                if analytics['learning_speed']:
                    avg_speed = sum(m['value'] for m in analytics['learning_speed']) / len(analytics['learning_speed'])
                    st.metric("Learning Speed", f"{avg_speed:.2f}")
            
            # Character memory overview
            memories = db.get_enhanced_memories(char_name, current_user.id, limit=3)
            if memories:
                st.write("**Recent Memories:**")
                for memory in memories:
                    st.write(f"• {memory['content'][:60]}... (importance: {memory['importance']:.1f})")
    
    # A/B Testing Dashboard
    st.subheader("🧪 A/B Testing Dashboard")
    
    with st.expander("Personality Experiments"):
        col1, col2 = st.columns(2)
        
        with col1:
            experiment_name = st.text_input("Experiment Name", value="patience_test_v1")
            character_to_test = st.selectbox("Character", character_names)
            
            if st.button("Create Patience Level Test"):
                # Create a simple A/B test
                variants = {
                    "high_patience": {"patience_multiplier": 1.5},
                    "low_patience": {"patience_multiplier": 0.7}
                }
                
                try:
                    experiment_id = db.create_ab_test_experiment(experiment_name, character_to_test, variants)
                    st.success(f"Created experiment: {experiment_id}")
                except Exception as e:
                    st.error(f"Failed to create experiment: {str(e)}")
        
        with col2:
            # Show user's current experiment assignment
            if current_user:
                variant = db.get_user_experiment_variant(current_user.id, experiment_name)
                if variant:
                    st.info(f"You're in variant: {variant}")
                else:
                    st.info("Not assigned to any experiment")
    
    # Enhanced Memory Analytics
    st.subheader("🧠 Enhanced Memory System")
    
    # Memory distribution by type
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    
    memory_type_query = """
    SELECT memory_type, COUNT(*) as count, AVG(importance_score) as avg_importance
    FROM enhanced_character_memory
    WHERE user_id = ?
    GROUP BY memory_type
    ORDER BY count DESC
    """
    
    memory_stats = pd.read_sql(memory_type_query, conn, params=(current_user.id,))
    
    if not memory_stats.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Memory Types Distribution:**")
            st.dataframe(memory_stats)
        
        with col2:
            st.write("**Memory Importance Distribution:**")
            st.bar_chart(memory_stats.set_index('memory_type')['avg_importance'])
    
    # Emotional context analysis
    emotion_query = """
    SELECT emotional_context, COUNT(*) as count
    FROM enhanced_character_memory
    WHERE user_id = ?
    GROUP BY emotional_context
    ORDER BY count DESC
    """
    
    emotion_stats = pd.read_sql(emotion_query, conn, params=(current_user.id,))
    
    if not emotion_stats.empty:
        st.write("**Emotional Context of Memories:**")
        st.bar_chart(emotion_stats.set_index('emotional_context')['count'])
    
    conn.close()

def display_enhanced_message(message: Message, message_index: int = 0):
    """Display a chat message with enhanced styling and metadata"""
    if message.sender == "You":
        # User message - right aligned, blue
        st.chat_message("user").write(message.content)
    else:
        # Character message - left aligned, with enhanced character styling  
        with st.chat_message("assistant"):
            # Character name with enhanced info
            character_info = st.session_state.conversation_state.get_character_info(message.sender)
            
            if character_info:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{message.sender}** *({character_info.get('archetype', 'teacher')})*")
                with col2:
                    if 'emotion_detected' in message.metadata:
                        st.caption(f"😊 {message.metadata['emotion_detected']}")
            else:
                st.markdown(f"**{message.sender}**")
            
            st.write(message.content)
            
            # Show enhanced metadata if available - Use message index for unique, stable keys
            if message.metadata:
                unique_key = f"msg_debug_{message.sender}_{message_index}"
                if st.sidebar.checkbox(f"Show {message.sender} Debug", value=False, key=unique_key):
                    with st.expander(f"Debug: {message.sender}"):
                        st.json(message.metadata)

def main():
    """Main enhanced Streamlit application"""
    
    # Initialize enhanced database and user manager
    enhanced_db = init_enhanced_database()
    user_manager = UserManager(enhanced_db)  # Now uses EnhancedEduChatDatabase with compatibility methods
    
    # User selection/creation interface
    current_user = user_manager.show_user_selection()
    
    # If no user is selected, show welcome message
    if not current_user:
        st.title("🎓 Welcome to EduChat Enhanced!")
        st.markdown("""
        ### Your Enhanced AI Learning Companions
        
        EduChat Enhanced features next-generation AI personalities that adapt to your learning style:
        - **Aino** 🇫🇮 - Finnish language tutor with cultural expertise (Enhanced with emotional adaptation)
        - **Mase** 🧠 - Knowledge expert with dynamic personality (Enhanced with adaptive humor)  
        - **Anna** 💡 - Life wisdom advisor (Enhanced with contextual patience)
        - **Bee** 📊 - Data scientist with performance optimization (Enhanced with technical depth)
        
        ### ✨ New Enhanced Features:
        - **Adaptive Personalities**: Characters change their approach based on your emotional state
        - **Deep Memory System**: Characters remember your preferences and learning patterns
        - **Contextual Intelligence**: 4-layer context awareness for personalized responses
        - **Learning Analytics**: Track your progress and engagement patterns
        
        **👈 Create your profile in the sidebar to get started!**
        """)
        return
    
    # Initialize enhanced session state
    if 'conversation_state' not in st.session_state:
        st.session_state.conversation_state = EnhancedConversationState()
    
    # Initialize response generator
    st.session_state.conversation_state.initialize_response_generator(enhanced_db)
    
    if 'messages' not in st.session_state or st.session_state.get('current_user_id') != current_user.id:
        # New user or user switched - load their conversation history
        st.session_state.current_user_id = current_user.id
        st.session_state.messages = []
        
        # Add personalized welcome message with enhanced character awareness
        welcome_msg = Message(
            sender="System",
            content=f"Welcome back, {current_user.name}! 🎓 Your AI learning companions have been enhanced with deeper personalities and remember your learning journey. What would you like to explore today?",
            character_color="#F5F5F5"
        )
        st.session_state.messages.append(welcome_msg)
    
    if 'generating' not in st.session_state:
        st.session_state.generating = False
    
    # Enhanced sidebar with character personality insights
    with st.sidebar:
        st.title("🎓 EduChat Enhanced Controls")
        
        # User info and analytics  
        user_manager.show_user_analytics(current_user)
        
        # Enhanced Character Personalities Display
        st.subheader("🎭 Enhanced Learning Companions")
        
        for char_name in ["Aino", "Mase", "Anna", "Bee"]:
            char_info = st.session_state.conversation_state.get_character_info(char_name)
            
            with st.expander(f"{char_name} - {char_info.get('archetype', 'Teacher').title()}"):
                if char_info:
                    st.write(f"**Role:** {char_info.get('description', 'AI Teacher')}")
                    
                    # Show personality attributes
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Patience", char_info.get('patience_level', 'Unknown'))
                        formality = char_info.get('formality_level', 0.5)
                        st.metric("Formality", f"{formality:.1f}/1.0")
                    
                    with col2:
                        enthusiasm = char_info.get('enthusiasm_level', 0.5)
                        st.metric("Enthusiasm", f"{enthusiasm:.1f}/1.0")
                        style = char_info.get('default_response_style', 'moderate')
                        st.metric("Response Style", style.title())
                    
                    # Show character memories if available
                    memories = enhanced_db.get_enhanced_memories(char_name, current_user.id, limit=2)
                    if memories:
                        st.write("**Remembers about you:**")
                        for memory in memories:
                            importance_color = "🟢" if memory['importance'] > 7 else "🟡" if memory['importance'] > 5 else "⚪"
                            st.write(f"{importance_color} {memory['content'][:50]}...")
                
                st.write(f"**Expertise:** {', '.join(char_info.get('knowledge_domains', ['Learning']))}")
        
        # Admin panel for database exploration (Pete only)
        if current_user.name.lower() == "pete":
            st.markdown("---")
            with st.expander("🔧 Enhanced Admin Panel"):
                show_enhanced_admin_panel(enhanced_db, current_user)
        
        st.markdown("---")
        
        # Enhanced conversation settings
        st.subheader("⚙️ Enhanced Settings")
        
        conversation_mode = st.selectbox(
            "Conversation Mode",
            ["balanced", "supportive", "challenging", "exploratory"],
            index=0,
            help="How the characters should adapt their approach"
        )
        st.session_state.conversation_state.conversation_mode = conversation_mode
        
        max_rounds = st.slider("Rounds per topic", 1, 5, 3)
        st.session_state.conversation_state.max_rounds = max_rounds
        
        # Enhanced features toggle
        st.write("**Enhanced Features:**")
        enable_emotion_detection = st.checkbox("Emotion Detection", value=True, 
                                             help="Characters adapt based on your emotional state",
                                             key="enable_emotion_detection")
        enable_memory_integration = st.checkbox("Memory Integration", value=True,
                                               help="Characters remember your learning history",
                                               key="enable_memory_integration") 
        enable_ab_testing = st.checkbox("A/B Testing", value=False,
                                       help="Participate in character improvement experiments",
                                       key="enable_ab_testing")
        
        # Quick enhanced topic buttons
        st.subheader("🚀 Quick Learning Topics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🇫🇮 Adaptive Finnish", use_container_width=True):
                st.session_state.pending_topic = "Hi Aino! I'd like an adaptive Finnish lesson that matches my current mood and energy level."
            
            if st.button("🧠 Smart Study Tips", use_container_width=True):
                st.session_state.pending_topic = "Anna, I need study advice that considers my personality and past performance."
        
        with col2:
            if st.button("📊 Data Deep Dive", use_container_width=True):
                st.session_state.pending_topic = "Bee, can you analyze something using your enhanced analytical perspective?"
            
            if st.button("🎯 Knowledge Challenge", use_container_width=True):
                st.session_state.pending_topic = "Mase, surprise me with something interesting that matches my curiosity level!"
        
        # Enhanced analytics section
        if len(st.session_state.messages) > 1:
            st.subheader("📈 Enhanced Session Analytics")
            
            # Create enhanced analytics dataframe
            messages_df = pd.DataFrame([
                {
                    'sender': msg.sender,
                    'length': len(msg.content),
                    'timestamp': msg.timestamp,
                    'has_emotion_data': 'emotion_detected' in msg.metadata,
                    'character_adapted': 'adaptation_mode' in msg.metadata
                } 
                for msg in st.session_state.messages
            ])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Messages This Session", len(messages_df))
                
                emotion_detected_count = messages_df['has_emotion_data'].sum()
                st.metric("Emotion Adaptations", emotion_detected_count)
            
            with col2:
                # Character participation
                char_counts = messages_df[messages_df['sender'] != 'You']['sender'].value_counts()
                if not char_counts.empty:
                    most_active = char_counts.index[0]
                    st.metric("Most Active Character", f"{most_active} ({char_counts.iloc[0]})")
                
                adapted_count = messages_df['character_adapted'].sum()
                st.metric("Adaptive Responses", adapted_count)
    
    # Main enhanced chat interface
    st.title("💬 Enhanced Learning Conversation")
    
    # Display conversation history with enhanced formatting
    for i, message in enumerate(st.session_state.messages):
        display_enhanced_message(message, message_index=i)
    
    # Handle pending topic from quick buttons
    if 'pending_topic' in st.session_state:
        user_input = st.session_state.pending_topic
        del st.session_state.pending_topic
    else:
        # Chat input
        user_input = st.chat_input(
            "Ask a question or start a new topic... (Enhanced AI will adapt to your style)",
            disabled=st.session_state.generating
        )
    
    # Process user input with enhanced response generation
    if user_input and not st.session_state.generating:
        # Add user message
        user_msg = Message(sender="You", content=user_input)
        st.session_state.messages.append(user_msg)
        display_enhanced_message(user_msg, len(st.session_state.messages) - 1)
        
        # Initialize conversation round
        conv_state = st.session_state.conversation_state
        conv_state.initialize_round(user_input)
        
        # Generate enhanced AI responses
        st.session_state.generating = True
        
        # Enhanced progress indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            total_characters = len(conv_state.speaker_queue)
            
            for i in range(total_characters):
                character_name = conv_state.get_next_speaker()
                if not character_name:
                    break
                
                # Update progress
                progress = (i + 1) / total_characters
                progress_bar.progress(progress)
                status_text.text(f"{character_name} is thinking with enhanced personality...")
                
                # Add realistic typing delay
                time.sleep(1.5)
                
                # Build conversation context
                conversation_context = [
                    {
                        'sender': msg.sender,
                        'content': msg.content,
                        'timestamp': msg.timestamp
                    }
                    for msg in st.session_state.messages[-8:]  # Last 8 messages
                ]
                
                # Generate enhanced response
                response_text, metadata = conv_state.response_generator.generate_enhanced_response(
                    character_name, current_user.id, user_input, conversation_context,
                    detect_emotion=enable_emotion_detection if 'enable_emotion_detection' in locals() else True
                )
                
                # Add character message with enhanced metadata
                char_msg = Message(
                    sender=character_name,
                    content=response_text,
                    character_color=conv_state.enhanced_characters[character_name].color,
                    metadata=metadata
                )
                st.session_state.messages.append(char_msg)
                display_enhanced_message(char_msg, len(st.session_state.messages) - 1)
        
        finally:
            # Cleanup
            progress_bar.empty()
            status_text.empty()
            st.session_state.generating = False
            
            # Save enhanced conversation to database
            if current_user:
                conversation_record = ConversationRecord(
                    user_id=current_user.id,
                    title=f"Enhanced Chat: {user_input[:30]}...",
                    topic=user_input[:50],
                    character_set=[char_name for char_name in conv_state.enhanced_characters.keys()],
                    conversation_mode=conversation_mode,
                    total_rounds=conv_state.current_round,
                    total_messages=len(st.session_state.messages),
                    messages=[{
                        'sender': msg.sender,
                        'content': msg.content,
                        'timestamp': msg.timestamp,
                        'metadata': msg.metadata
                    } for msg in st.session_state.messages]
                )
                enhanced_db.save_conversation(conversation_record)
            
            # Check if round/conversation is complete
            if conv_state.is_round_complete():
                if conv_state.should_end_conversation():
                    completion_msg = Message(
                        sender="System",
                        content=f"Excellent enhanced conversation, {current_user.name}! 🎉 The AI companions have learned more about your style. Ready for a new topic?",
                        character_color="#E8F5E8"
                    )
                    st.session_state.messages.append(completion_msg)
                    conv_state.reset_for_new_topic()
                else:
                    round_msg = Message(
                        sender="System", 
                        content=f"Enhanced Round {conv_state.current_round} complete! The characters are adapting to your responses. Continue or start fresh!",
                        character_color="#E8F5E8"
                    )
                    st.session_state.messages.append(round_msg)
            
            # Trigger rerun to show new messages
            st.rerun()

if __name__ == "__main__":
    main()
