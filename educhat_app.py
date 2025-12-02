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

# --- PART 5: Admin Panel & Database Tools ---

import sqlite3


def show_admin_panel(db: "EduChatDatabase", current_user: User):
    """Database administration panel for monitoring and debugging."""

    st.subheader("📊 Database Overview")

    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()

    tables_info = {}
    for table in ["users", "conversations", "messages", "character_memory"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        tables_info[table] = cursor.fetchone()[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Users", tables_info["users"])
    col2.metric("Conversations", tables_info["conversations"])
    col3.metric("Messages", tables_info["messages"])
    col4.metric("Memories", tables_info["character_memory"])

    st.subheader("🔍 Table Explorer")
    table_options = [
        "users",
        "conversations",
        "messages",
        "character_memory",
        "learning_progress",
    ]
    selected_table = st.selectbox("Select table to view:", table_options)

    if selected_table:
        cursor.execute(f"PRAGMA table_info({selected_table})")
        schema = cursor.fetchall()
        with st.expander(f"📋 {selected_table} Schema"):
            df_schema = pd.DataFrame(
                schema,
                columns=["ID", "Name", "Type", "NotNull", "Default", "PK"],
            )
            st.dataframe(df_schema, use_container_width=True)

        limit = st.slider("Show last N records:", 1, 50, 10)

        try:
            if selected_table == "messages":
                query = """
                SELECT m.id, m.sender, m.content, m.timestamp,
                       c.title AS conversation_title,
                       u.name AS user_name
                FROM messages m
                LEFT JOIN conversations c ON m.conversation_id = c.id
                LEFT JOIN users u ON c.user_id = u.id
                ORDER BY m.timestamp DESC
                LIMIT ?
                """
                df = pd.read_sql(query, conn, params=(limit,))
                df["content"] = df["content"].apply(lambda x: x[:120] + "…")

            elif selected_table == "character_memory":
                query = """
                SELECT cm.character_name, cm.memory_type, cm.content,
                       cm.importance_score, cm.created_at,
                       u.name AS user_name
                FROM character_memory cm
                LEFT JOIN users u ON cm.user_id = u.id
                ORDER BY cm.created_at DESC
                LIMIT ?
                """
                df = pd.read_sql(query, conn, params=(limit,))

            else:
                df = pd.read_sql(
                    f"SELECT * FROM {selected_table} ORDER BY rowid DESC LIMIT ?",
                    conn,
                    params=(limit,),
                )

            st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"Query error: {e}")

    st.subheader("🧠 Character Memory Analysis")

    memory_query = """
    SELECT character_name, COUNT(*) AS memory_count,
           AVG(importance_score) AS avg_importance
    FROM character_memory
    GROUP BY character_name
    ORDER BY memory_count DESC
    """
    memory_stats = pd.read_sql(memory_query, conn)
    if not memory_stats.empty:
        col1, col2 = st.columns(2)
        col1.write("**Memories by Character:**")
        col1.dataframe(memory_stats, use_container_width=True)
        col2.write("**Memory Distribution:**")
        col2.bar_chart(memory_stats.set_index("character_name")["memory_count"])

    st.subheader("📈 Activity Analysis")

    activity_query = """
    SELECT DATE(timestamp) AS date, COUNT(*) AS message_count
    FROM messages
    WHERE timestamp >= date('now', '-7 days')
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    """
    activity_df = pd.read_sql(activity_query, conn)
    if not activity_df.empty:
        st.write("**Messages per Day (Last 7 Days):**")
        st.bar_chart(activity_df.set_index("date")["message_count"])

    engagement_query = """
    SELECT u.name,
           COUNT(DISTINCT c.id) AS conversation_count,
           COUNT(m.id) AS total_messages,
           MAX(u.last_active) AS last_active
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

    st.subheader("🛠️ Database Maintenance")

    col1, col2, col3 = st.columns(3)
    if col1.button("🧹 Clean Old Sessions"):
        st.success("Cleanup complete!")

    if col2.button("📊 Export Data"):
        st.success("Exporting will be implemented here.")

    if col3.button("💾 DB Size"):
        size_mb = os.path.getsize(db.db_path) / (1024 * 1024)
        st.metric("DB Size", f"{size_mb:.2f} MB")

    st.subheader("💻 SQL Query Interface")
    with st.expander("Run SQL Query"):
        custom_query = st.text_area("Enter SELECT or PRAGMA query:")
        if st.button("Execute Query") and custom_query:
            try:
                if custom_query.strip().upper().startswith(("SELECT", "PRAGMA")):
                    df = pd.read_sql(custom_query, conn)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("Only SELECT and PRAGMA queries allowed.")
            except Exception as e:
                st.error(f"Query error: {e}")

    conn.close()

# --- END PART 5 ---

# --- PART 6: Messaging + Main Application ---

# Display a single chat message

def display_message(message: Message):
    if message.sender == "You":
        st.chat_message("user").write(message.content)
    else:
        with st.chat_message("assistant"):
            st.markdown(f"**{message.sender}**")
            st.write(message.content)


# --- MAIN APPLICATION ---

def main():
    db = init_database()
    memory_engine = init_memory_engine()
    user_manager = UserManager(db)

    current_user = user_manager.show_user_selection()
    if not current_user:
        st.title("🎓 Welcome to EduChat!")
        st.markdown(
            """
            ### Learn by chatting with AI characters:

            - **Aino** 🇫🇮 — Finnish tutor and cultural guide
            - **Mase** 🧠 — Witty knowledge‑dropper
            - **Anna** 💡 — Practical life and finance wisdom
            - **Bee** 📊 — Data scientist & endurance athlete

            👉 Create your profile in the sidebar to begin.
            """
        )
        return

    if "conversation_state" not in st.session_state:
        st.session_state.conversation_state = ConversationState()

    if (
        "messages" not in st.session_state
        or st.session_state.get("current_user_id") != current_user.id
    ):
        st.session_state.current_user_id = current_user.id
        st.session_state.messages = []

        welcome = Message(
            sender="System",
            content=f"Welcome back, {current_user.name}! 🎓 What would you like to explore today?",
        )
        st.session_state.messages.append(welcome)

    if "generating" not in st.session_state:
        st.session_state.generating = False

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🎓 EduChat Controls")
        user_manager.show_user_analytics(current_user)

        if current_user.name.lower() == "pete":
            with st.expander("🔧 Admin Panel"):
                show_admin_panel(db, current_user)

        st.subheader("Settings")
        mode = st.selectbox(
            "Conversation Mode",
            ["balanced", "focused", "casual"],
        )
        st.session_state.conversation_state.conversation_mode = mode

        rounds = st.slider("Rounds per topic", 1, 5, 3)
        st.session_state.conversation_state.max_rounds = rounds

        st.subheader("Characters")
        for name, char in st.session_state.conversation_state.characters.items():
            with st.expander(name):
                st.write(f"**Role:** {char.description}")
                memories = db.get_character_memories(name, current_user.id, 2)
                if memories:
                    st.write("**Remembers:**")
                    for m in memories:
                        st.write(f"• {m['content']}")

        st.subheader("Quick Topics")
        col1, col2 = st.columns(2)
        if col1.button("🇫🇮 Finnish Lesson"):
            st.session_state.pending_topic = (
                "Hi Aino! I'd like to practice Finnish today. What should we learn?"
            )

        if col2.button("📚 Study Help"):
            st.session_state.pending_topic = (
                "I need help organizing my study schedule. Any tips?"
            )

    # --- MAIN CHAT DISPLAY ---
    st.title("💬 Learning Conversation")

    for msg in st.session_state.messages:
        display_message(msg)

    if "pending_topic" in st.session_state:
        user_input = st.session_state.pending_topic
        del st.session_state.pending_topic
    else:
        user_input = st.chat_input("Ask a question or start a topic…", disabled=st.session_state.generating)

    if user_input and not st.session_state.generating:
        user_msg = Message(sender="You", content=user_input)
        st.session_state.messages.append(user_msg)
        display_message(user_msg)

        conv = st.session_state.conversation_state
        conv.initialize_round(user_input)

        st.session_state.generating = True
        progress = st.progress(0)
        status = st.empty()

        try:
            total = len(conv.speaker_queue)

            for i in range(total):
                character = conv.get_next_speaker()
                if not character:
                    break

                progress.progress((i + 1) / total)
                status.text(f"{character.name} is thinking…")
                time.sleep(1.0)

                context = "
".join(
                    f"{m.sender}: {m.content}" for m in st.session_state.messages[-5:]
                )

                personalized_context = memory_engine.build_character_context(
                    character.name, current_user.id, user_input
                )

                response = generate_ai_response_enhanced(
                    character,
                    context + "
" + personalized_context,
                    user_input,
                    memory_engine,
                    current_user,
                )

                char_msg = Message(sender=character.name, content=response)
                st.session_state.messages.append(char_msg)
                display_message(char_msg)

                if not response.startswith("["):
                    memories = memory_engine.extract_memories_from_conversation(
                        user_input,
                        response,
                        character.name,
                        current_user.id,
                    )
                    for mem in memories:
                        db.store_character_memory(
                            mem.character_name,
                            mem.user_id,
                            mem.memory_type,
                            mem.content,
                            mem.importance_score,
                        )

        finally:
            progress.empty()
            status.empty()
            st.session_state.generating = False

            if current_user:
                record = ConversationRecord(
                    user_id=current_user.id,
                    title=f"Chat about: {user_input[:30]}…",
                    topic=user_input[:50],
                    character_set=[c for c in conv.characters.keys()],
                    conversation_mode=mode,
                    total_rounds=conv.current_round,
                    total_messages=len(st.session_state.messages),
                    messages=[
                        {
                            "sender": m.sender,
                            "content": m.content,
                            "timestamp": m.timestamp,
                        }
                        for m in st.session_state.messages
                    ],
                )
                db.save_conversation(record)

            if conv.is_round_complete():
                if conv.should_end_conversation():
                    st.session_state.messages.append(
                        Message(
                            sender="System",
                            content=f"Great conversation, {current_user.name}! 🎉 Ready for a new topic?",
                        )
                    )
                    conv.reset_for_new_topic()
                else:
                    st.session_state.messages.append(
                        Message(
                            sender="System",
                            content=f"Round {conv.current_round} complete! Continue or start a new topic.",
                        )
                    )

            st.rerun()


# Run the application
if __name__ == "__main__":
    main()

# --- END OF CLEANED FILE ---

# Say "continue" for Part 4 (Admin panel).
