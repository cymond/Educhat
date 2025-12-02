# Cleaned and corrected version of educhat_app.py
# Emoji fixed, formatting cleaned, and minor bugs fixed.

# NOTE: Due to message size limits, I will provide the full corrected code in sequential chunks.
# Tell me "continue" and I will paste the next block.

# --- START OF CLEANED FILE (Part 1) ---

"""
EduChat - AI Educational Group Chat Platform
Cleaned version: All mojibake emojis fixed, code tidied, and small bugs corrected.
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

from database_models import UserManager, User, ConversationRecord
from optimized_database import OptimizedEduChatDatabase
from memory_system import AdvancedMemoryEngine, MemoryItem

load_dotenv()

@st.cache_resource
def init_database():
    return OptimizedEduChatDatabase()

@st.cache_resource
def init_memory_engine():
    db = init_database()
    return AdvancedMemoryEngine(db)

st.set_page_config(
    page_title="EduChat - AI Learning Companions",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

@dataclass
class Character:
    name: str
    description: str
    speaking_style: str
    color: str
    personality_traits: List[str] = field(default_factory=list)
    knowledge_domains: List[str] = field(default_factory=list)

    def get_style_prompt(self):
        return f"""
You are {self.name}, a character in an educational group chat.

Character Description: {self.description}
Speaking Style: {self.speaking_style}
Personality Traits: {', '.join(self.personality_traits)}
Knowledge Areas: {', '.join(self.knowledge_domains)}

IMPORTANT: Stay completely in character (1–3 sentence replies).
"""

# --- PART 2: ConversationState and Message classes ---

@dataclass
class Message:
    sender: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    character_color: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationState:
    def __init__(self):
        self.characters = self._create_default_characters()
        self.current_round = 0
        self.max_rounds = 3
        self.speaker_queue = []
        self.current_speaker_index = 0
        self.conversation_mode = "balanced"
        self.pending_user_message = None

    def _create_default_characters(self) -> Dict[str, Character]:
        return {
            "Aino": Character(
                name="Aino",
                description="Native Finnish speaker, patient teacher, cultural guide",
                speaking_style="Very short supportive explanations, include Finnish cultural notes.",
                color="#E3F2FD",
                personality_traits=["patient", "encouraging", "cultural_expert"],
                knowledge_domains=["finnish_language", "culture", "pronunciation"],
            ),
            "Mase": Character(
                name="Mase",
                description="Witty young adult, brief but insightful, jokes casually",
                speaking_style="Very short with jokes, hinting at deeper ideas.",
                color="#E8F5E8",
                personality_traits=["witty", "brief", "knowledgeable"],
                knowledge_domains=["science", "technology", "trivia"],
            ),
            "Anna": Character(
                name="Anna",
                description="Middle‑aged mother, wise investor, fitness‑oriented vegan",
                speaking_style="Plain-spoken clarity, Buffett‑like practical wisdom.",
                color="#FFF3E0",
                personality_traits=["wise", "practical", "calm"],
                knowledge_domains=["finance", "health", "life_advice"],
            ),
            "Bee": Character(
                name="Bee",
                description="Data scientist, endurance athlete, explains concepts crisply",
                speaking_style="Concise, analytical, references endurance training.",
                color="#FCE4EC",
                personality_traits=["technical", "athletic", "analytical"],
                knowledge_domains=["data_science", "programming", "sports"],
            ),
        }

    def initialize_round(self, user_message: str):
        self.pending_user_message = user_message
        self.speaker_queue = list(self.characters.keys())
        random.shuffle(self.speaker_queue)
        self.current_speaker_index = 0
        self.current_round += 1

    def get_next_speaker(self) -> Optional[Character]:
        if self.current_speaker_index >= len(self.speaker_queue):
            return None
        name = self.speaker_queue[self.current_speaker_index]
        self.current_speaker_index += 1
        return self.characters[name]

    def is_round_complete(self):
        return self.current_speaker_index >= len(self.speaker_queue)

    def should_end_conversation(self):
        return self.current_round >= self.max_rounds

    def reset_for_new_topic(self):
        self.current_round = 0
        self.speaker_queue = []
        self.current_speaker_index = 0
        self.pending_user_message = None

# --- END PART 2 ---

# --- PART 3: AI Response Generation ---

import anthropic


def generate_ai_response(character: Character, conversation_context: str, user_message: str) -> str:
    """Generate AI response using Anthropic API with character personality."""

    # Get API key
    api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    model = (
        st.secrets.get("ANTHROPIC_MODEL")
        or os.getenv("ANTHROPIC_MODEL")
        or "claude-3-5-sonnet-20241022"
    )

    if not api_key:
        fallback = {
            "Aino": f"Hei! About '{user_message}' — in Finnish we say 'Tervetuloa oppimaan!' (Welcome to learning!)",
            "Mase": f"*drops knowledge* Yeah, {user_message.lower()} is kinda wild...",
            "Anna": f"Here's the practical angle on {user_message.lower()}: focus on the fundamentals.",
            "Bee": f"If I analyze {user_message.lower()} like data, patterns start to emerge.",
        }
        return fallback.get(character.name, "I'd love to help with that!")

    try:
        client = anthropic.Anthropic(api_key=api_key)

        system_prompt = f"""
You are participating in an educational group chat as the character {character.name}.

{character.get_style_prompt()}

CRITICAL RULES:
- Stay completely in character
- Keep responses short (1–3 sentences)
- Be educational
- Follow the personality constraints of the character

Recent conversation:
{conversation_context}

User said: "{user_message}"
"""

        response = client.messages.create(
            model=model,
            max_tokens=150,
            temperature=0.7,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        return response.content[0].text.strip()

    except Exception as e:
        return f"[Error contacting AI service: {e}]"


# --- PART 4: Enhanced Memory-Aware Response ---

def generate_ai_response_enhanced(character, conversation_context, user_message, memory_engine, current_user):
    api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    model = (
        st.secrets.get("ANTHROPIC_MODEL")
        or os.getenv("ANTHROPIC_MODEL")
        or "claude-3-5-sonnet-20241022"
    )

    if not api_key:
        fallback = {
            "Aino": f"Hei! For '{user_message}', I'd say: 'Tervetuloa oppimaan!'",
            "Mase": f"Quick take: {user_message.lower()}? Interesting...",
            "Anna": f"Here's the practical angle: master the basics first.",
            "Bee": f"Data-wise, {user_message.lower()} points toward a clear pattern.",
        }
        return fallback.get(character.name, "I'd love to help!")

    try:
        client = anthropic.Anthropic(api_key=api_key)

        personalized_context = memory_engine.build_character_context(
            character.name,
            current_user.id,
            user_message,
        )

        system_prompt = f"""
You are {character.name}.

{character.get_style_prompt()}

PERSONALIZED CONTEXT ABOUT THE USER:
{personalized_context}

RULES:
- Stay fully in character
- Personalize replies using memory when helpful
- Keep answers short and conversational
- Be educational

Recent conversation:
{conversation_context}
"""

        response = client.messages.create(
            model=model,
            max_tokens=180,
            temperature=0.7,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        return response.content[0].text.strip()

    except Exception as e:
        return f"[AI error: {e}]"


# --- END PART 4 ---

# Say "continue" for Part 4 (Admin panel).
