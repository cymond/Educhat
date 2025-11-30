"""
EduChat - AI Educational Group Chat Platform
Built with Streamlit for interactive learning conversations
"""

import streamlit as st
import asyncio
import time
import random
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd

# Configure Streamlit
st.set_page_config(
    page_title="EduChat - AI Learning Companions", 
    page_icon="🎓",
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
    """Manages conversation flow and character interactions"""
    
    def __init__(self):
        self.characters = self._create_default_characters()
        self.current_round = 0
        self.max_rounds = 3
        self.speaker_queue = []
        self.current_speaker_index = 0
        self.conversation_mode = "balanced"
        self.pending_user_message = None
        
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
    
    def initialize_round(self, user_message: str):
        """Start a new round with user message"""
        self.pending_user_message = user_message
        self.speaker_queue = list(self.characters.keys())
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

def generate_ai_response(character: Character, conversation_context: str, user_message: str) -> str:
    """Generate AI response for character - placeholder for now"""
    # This is where we'd integrate with Anthropic/OpenAI
    # For now, using character-appropriate responses
    
    responses_by_character = {
        "Aino": [
            f"Hei! About '{user_message.lower()}' - that's a great question for learning Finnish!",
            f"In Finnish culture, we have a saying about this topic...",
            f"Let me help you understand this - 'Tervetuloa!' (Welcome to learning!)"
        ],
        "Mase": [
            f"Lol, easy one. {user_message} is basically...",
            f"Fun fact about that...",
            f"*drops knowledge casually* Yeah, so..."
        ],
        "Anna": [
            f"That's a practical question. Here's what I've learned about {user_message.lower()}...",
            f"From my experience investing in education, this matters because...",
            f"Simple truth: understanding {user_message.lower()} builds discipline."
        ],
        "Bee": [
            f"Interesting data point on {user_message.lower()}...",
            f"If I were to analyze this like a dataset...",
            f"Train harder, not smarter applies here too..."
        ]
    }
    
    return random.choice(responses_by_character.get(character.name, ["I'd love to help with that!"]))

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
    """Main Streamlit application"""
    
    # Initialize session state
    if 'conversation_state' not in st.session_state:
        st.session_state.conversation_state = ConversationState()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        welcome_msg = Message(
            sender="System",
            content="Welcome to EduChat! 🎓 Your AI learning companions are here to help. What would you like to explore today?",
            character_color="#F5F5F5"
        )
        st.session_state.messages.append(welcome_msg)
    
    if 'generating' not in st.session_state:
        st.session_state.generating = False
    
    # Sidebar for controls and analytics
    with st.sidebar:
        st.title("🎓 EduChat Controls")
        
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
        
        # Character info
        st.subheader("Active Characters")
        for char_name, char in st.session_state.conversation_state.characters.items():
            with st.expander(f"{char_name}"):
                st.write(f"**Role:** {char.description}")
                st.write(f"**Style:** {char.speaking_style[:100]}...")
        
        # Quick topic buttons
        st.subheader("Quick Topics")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🇫🇮 Finnish Lesson", use_container_width=True):
                st.session_state.pending_topic = "Let's practice Finnish! Can you help me with basic greetings?"
        
        with col2:
            if st.button("📚 Study Help", use_container_width=True):
                st.session_state.pending_topic = "I need help organizing my study schedule. Any tips?"
        
        # Analytics section
        if len(st.session_state.messages) > 1:
            st.subheader("📊 Session Analytics")
            
            # Create simple analytics dataframe
            messages_df = pd.DataFrame([
                {
                    'sender': msg.sender,
                    'length': len(msg.content),
                    'timestamp': msg.timestamp
                } 
                for msg in st.session_state.messages
            ])
            
            st.metric("Messages Exchanged", len(messages_df))
            
            # Character participation
            char_counts = messages_df[messages_df['sender'] != 'You']['sender'].value_counts()
            if not char_counts.empty:
                st.write("**Character Participation:**")
                st.bar_chart(char_counts)
    
    # Main chat interface
    st.title("💬 Learning Conversation")
    
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
        
        # Generate AI responses
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
                
                # Generate response
                conversation_context = "\n".join([
                    f"{msg.sender}: {msg.content}" 
                    for msg in st.session_state.messages[-5:]  # Last 5 messages
                ])
                
                response = generate_ai_response(character, conversation_context, user_input)
                
                # Add character message
                char_msg = Message(
                    sender=character.name,
                    content=response,
                    character_color=character.color
                )
                st.session_state.messages.append(char_msg)
                display_message(char_msg)
        
        finally:
            # Cleanup
            progress_bar.empty()
            status_text.empty()
            st.session_state.generating = False
            
            # Check if round/conversation is complete
            if conv_state.is_round_complete():
                if conv_state.should_end_conversation():
                    completion_msg = Message(
                        sender="System",
                        content=f"Great conversation! 🎉 Ready for a new topic?",
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
