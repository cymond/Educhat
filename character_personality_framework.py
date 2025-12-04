"""
EduChat Character Personality Framework (CPF)
Multi-layered personality system with dynamic emotional adaptation
"""

import json
import random
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

class EmotionalState(Enum):
    """User emotional states that trigger character adaptation"""
    FRUSTRATED = "frustrated"
    EXCITED = "excited"
    CONFUSED = "confused"
    CONFIDENT = "confident"
    BORED = "bored"
    ENGAGED = "engaged"
    OVERWHELMED = "overwhelmed"
    CURIOUS = "curious"

class ResponseStyle(Enum):
    """Character response style variations"""
    BRIEF = "brief"           # 1-2 sentences
    MODERATE = "moderate"     # 2-4 sentences
    DETAILED = "detailed"     # 4-6 sentences
    COMPREHENSIVE = "comprehensive"  # 6+ sentences

class PatientLevel(Enum):
    """Character patience levels"""
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5

@dataclass
class BehavioralAttributes:
    """Core behavioral attributes that influence character responses"""
    
    # Basic Demographics
    age: int = 25
    gender: str = "neutral"
    occupation: str = "teacher"
    cultural_background: str = "international"
    
    # Personality Dimensions
    patience_level: PatientLevel = PatientLevel.MODERATE
    formality_level: float = 0.5  # 0.0 = very informal, 1.0 = very formal
    enthusiasm_level: float = 0.7  # 0.0 = monotone, 1.0 = very energetic
    humor_tendency: float = 0.3   # 0.0 = serious, 1.0 = always joking
    
    # Teaching Style
    expertise_confidence: float = 0.8  # 0.0 = hesitant, 1.0 = very confident
    explanation_style: str = "adaptive"  # "simple", "technical", "adaptive"
    encouragement_frequency: float = 0.6  # How often to encourage
    
    # Communication Preferences
    default_response_style: ResponseStyle = ResponseStyle.MODERATE
    uses_examples: bool = True
    uses_analogies: bool = True
    asks_questions: bool = True

@dataclass
class DynamicState:
    """Dynamic state that changes based on user interaction"""
    
    current_patience: float = 0.5  # Current patience level (0-1)
    energy_level: float = 0.7      # Current energy/enthusiasm
    focus_topic: str = ""          # Current conversation focus
    adaptation_mode: str = "balanced"  # "supportive", "challenging", "balanced"
    
    # Emotional adaptation parameters
    detected_user_emotion: EmotionalState = EmotionalState.ENGAGED
    adaptation_strength: float = 0.5  # How much to adapt (0-1)
    
    # Session tracking
    messages_this_session: int = 0
    user_success_rate: float = 0.5  # Recent success in understanding
    needs_encouragement: bool = False

@dataclass
class CharacterMemory:
    """Enhanced character memory with relationship context"""
    
    # Relationship tracking
    rapport_level: float = 0.5      # How well character knows user (0-1)
    trust_level: float = 0.5        # User trust in character (0-1)
    learning_style_detected: str = "unknown"  # "visual", "auditory", "kinesthetic"
    
    # Learning progress awareness
    known_strengths: List[str] = field(default_factory=list)
    known_weaknesses: List[str] = field(default_factory=list)
    preferred_topics: List[str] = field(default_factory=list)
    avoided_topics: List[str] = field(default_factory=list)
    
    # Personal details
    personal_interests: Dict[str, float] = field(default_factory=dict)  # interest -> strength
    family_context: Dict[str, str] = field(default_factory=dict)
    goals_mentioned: List[str] = field(default_factory=list)

@dataclass
class EnhancedCharacter:
    """Enhanced character with multi-layered personality system"""
    
    # Basic identity
    name: str = ""
    archetype: str = "teacher"  # "teacher", "peer", "mentor", "devil_advocate", etc.
    
    # Visual presentation
    color: str = "#E3F2FD"
    avatar_style: str = "friendly"
    
    # Core personality
    core_attributes: BehavioralAttributes = field(default_factory=BehavioralAttributes)
    dynamic_state: DynamicState = field(default_factory=DynamicState)
    character_memory: CharacterMemory = field(default_factory=CharacterMemory)
    
    # Knowledge and capabilities
    knowledge_domains: List[str] = field(default_factory=list)
    teaching_specialties: List[str] = field(default_factory=list)
    conversation_starters: List[str] = field(default_factory=list)
    
    # System prompts
    base_prompt_template: str = ""
    adaptation_prompts: Dict[str, str] = field(default_factory=dict)

class EmotionalAdapter:
    """Handles dynamic emotional adaptation of character responses"""
    
    @staticmethod
    def detect_user_emotion(message_content: str, user_history: List[Dict]) -> Tuple[EmotionalState, float]:
        """
        Detect user emotional state from their message
        Returns: (emotion, confidence_score)
        """
        content_lower = message_content.lower()
        
        # Frustration indicators
        frustration_words = ["confused", "don't understand", "frustrated", "stuck", "hard", "difficult"]
        if any(word in content_lower for word in frustration_words):
            return EmotionalState.FRUSTRATED, 0.8
        
        # Excitement indicators
        excitement_words = ["awesome", "cool", "amazing", "love this", "great", "excited"]
        if any(word in content_lower for word in excitement_words):
            return EmotionalState.EXCITED, 0.7
        
        # Confusion indicators
        confusion_words = ["what", "how", "why", "explain", "huh", "?"]
        question_count = content_lower.count("?")
        if question_count > 1 or any(word in content_lower for word in confusion_words):
            return EmotionalState.CONFUSED, 0.6
        
        # Boredom indicators
        boredom_words = ["boring", "tired", "whatever", "ok", "sure"]
        if any(word in content_lower for word in boredom_words) or len(message_content) < 10:
            return EmotionalState.BORED, 0.5
        
        # Default to engaged
        return EmotionalState.ENGAGED, 0.3
    
    @staticmethod
    def adapt_character_state(character: EnhancedCharacter, user_emotion: EmotionalState, 
                            conversation_context: List[Dict]) -> None:
        """
        Dynamically adapt character's state based on detected user emotion
        """
        adaptation_map = {
            EmotionalState.FRUSTRATED: {
                'patience_adjustment': +0.3,
                'response_style': ResponseStyle.BRIEF,
                'encouragement_boost': +0.4,
                'adaptation_mode': 'supportive',
                'explanation_simplification': +0.3
            },
            EmotionalState.EXCITED: {
                'energy_boost': +0.2,
                'enthusiasm_match': +0.3,
                'response_style': ResponseStyle.DETAILED,
                'adaptation_mode': 'challenging',
                'encouragement_boost': +0.2
            },
            EmotionalState.CONFUSED: {
                'patience_adjustment': +0.4,
                'response_style': ResponseStyle.MODERATE,
                'example_increase': True,
                'adaptation_mode': 'supportive',
                'explanation_simplification': +0.4
            },
            EmotionalState.BORED: {
                'humor_boost': +0.3,
                'energy_boost': +0.4,
                'response_style': ResponseStyle.BRIEF,
                'topic_switch': True,
                'adaptation_mode': 'challenging'
            },
            EmotionalState.OVERWHELMED: {
                'patience_adjustment': +0.5,
                'response_style': ResponseStyle.BRIEF,
                'simplification': +0.5,
                'adaptation_mode': 'supportive',
                'break_suggestion': True
            }
        }
        
        if user_emotion in adaptation_map:
            adaptations = adaptation_map[user_emotion]
            
            # Apply patience adjustments
            if 'patience_adjustment' in adaptations:
                character.dynamic_state.current_patience = min(1.0, 
                    character.dynamic_state.current_patience + adaptations['patience_adjustment'])
            
            # Apply energy adjustments
            if 'energy_boost' in adaptations:
                character.dynamic_state.energy_level = min(1.0,
                    character.dynamic_state.energy_level + adaptations['energy_boost'])
            
            # Set adaptation mode
            if 'adaptation_mode' in adaptations:
                character.dynamic_state.adaptation_mode = adaptations['adaptation_mode']
            
            # Update detected emotion
            character.dynamic_state.detected_user_emotion = user_emotion

class ContextBuilder:
    """Builds multi-layered context for AI response generation"""
    
    @staticmethod
    def build_system_context(character: EnhancedCharacter) -> str:
        """Layer 1: Character Personality Framework (CPF) attributes"""
        attrs = character.core_attributes
        state = character.dynamic_state
        
        system_context = f"""You are {character.name}, an AI learning companion with the following personality:

CORE IDENTITY:
- Age: {attrs.age}, Gender: {attrs.gender}
- Occupation: {attrs.occupation}
- Cultural Background: {attrs.cultural_background}
- Archetype: {character.archetype}

PERSONALITY TRAITS:
- Patience Level: {attrs.patience_level.name} (Current: {state.current_patience:.1f}/1.0)
- Formality: {attrs.formality_level:.1f}/1.0 (0=casual, 1=formal)
- Enthusiasm: {attrs.enthusiasm_level:.1f}/1.0 (Current: {state.energy_level:.1f}/1.0)
- Humor Tendency: {attrs.humor_tendency:.1f}/1.0
- Expertise Confidence: {attrs.expertise_confidence:.1f}/1.0

TEACHING STYLE:
- Explanation Style: {attrs.explanation_style}
- Uses Examples: {attrs.uses_examples}
- Uses Analogies: {attrs.uses_analogies}
- Asks Questions: {attrs.asks_questions}
- Encouragement Frequency: {attrs.encouragement_frequency:.1f}/1.0

CURRENT DYNAMIC STATE:
- Detected User Emotion: {state.detected_user_emotion.value}
- Adaptation Mode: {state.adaptation_mode}
- Default Response Length: {attrs.default_response_style.value}
- Session Messages: {state.messages_this_session}
- User Success Rate: {state.user_success_rate:.1f}/1.0

BEHAVIORAL INSTRUCTIONS:
- Stay completely in character with these personality traits
- Adapt your response style to the user's emotional state
- Use your expertise in: {', '.join(character.knowledge_domains)}
- Maintain consistency with your personality across all interactions"""

        return system_context
    
    @staticmethod
    def build_session_context(conversation_history: List[Dict], limit: int = 8) -> str:
        """Layer 2: Recent conversation flow (last N turns)"""
        if not conversation_history:
            return "This is the start of a new conversation."
        
        recent_messages = conversation_history[-limit:]
        session_context = "RECENT CONVERSATION:\n"
        
        for msg in recent_messages:
            sender = msg.get('sender', 'Unknown')
            content = msg.get('content', '')[:200]  # Limit length
            session_context += f"{sender}: {content}\n"
        
        return session_context.strip()
    
    @staticmethod
    def build_knowledge_context(character: EnhancedCharacter, user_id: str, 
                               db_memories: List[Dict]) -> str:
        """Layer 3: Long-term character knowledge about user"""
        memory = character.character_memory
        
        knowledge_context = "WHAT YOU REMEMBER ABOUT THE USER:\n"
        
        # Personal relationship context
        knowledge_context += f"- Rapport Level: {memory.rapport_level:.1f}/1.0\n"
        knowledge_context += f"- Trust Level: {memory.trust_level:.1f}/1.0\n"
        knowledge_context += f"- Detected Learning Style: {memory.learning_style_detected}\n"
        
        # Strengths and weaknesses
        if memory.known_strengths:
            knowledge_context += f"- Known Strengths: {', '.join(memory.known_strengths)}\n"
        if memory.known_weaknesses:
            knowledge_context += f"- Areas to Support: {', '.join(memory.known_weaknesses)}\n"
        
        # Preferences
        if memory.preferred_topics:
            knowledge_context += f"- Enjoys Topics: {', '.join(memory.preferred_topics)}\n"
        if memory.personal_interests:
            interests = [f"{topic}({score:.1f})" for topic, score in memory.personal_interests.items()]
            knowledge_context += f"- Personal Interests: {', '.join(interests)}\n"
        
        # Database memories
        if db_memories:
            knowledge_context += "\nSPECIFIC MEMORIES:\n"
            for mem in db_memories[:5]:  # Top 5 memories
                knowledge_context += f"- {mem['content']} (importance: {mem['importance']}/10)\n"
        
        return knowledge_context.strip()
    
    @staticmethod
    def build_complete_context(character: EnhancedCharacter, user_message: str,
                              conversation_history: List[Dict], db_memories: List[Dict],
                              user_id: str) -> str:
        """Build complete 4-layer context for AI prompt"""
        
        # Layer 1: System/Character Personality Framework
        system_context = ContextBuilder.build_system_context(character)
        
        # Layer 2: Session context  
        session_context = ContextBuilder.build_session_context(conversation_history)
        
        # Layer 3: Knowledge context
        knowledge_context = ContextBuilder.build_knowledge_context(character, user_id, db_memories)
        
        # Layer 4: Current user message (handled separately in API call)
        
        complete_context = f"""{system_context}

{session_context}

{knowledge_context}

CURRENT USER MESSAGE: "{user_message}"

Respond as {character.name} would, incorporating your personality traits, the conversation flow, and your knowledge about the user. Keep your response natural and helpful."""

        return complete_context

class CharacterFactory:
    """Factory for creating enhanced characters with different archetypes"""
    
    @staticmethod
    def create_aino_enhanced() -> EnhancedCharacter:
        """Create enhanced version of Aino - Finnish language tutor"""
        character = EnhancedCharacter(
            name="Aino",
            archetype="cultural_teacher",
            color="#E3F2FD",
            
            core_attributes=BehavioralAttributes(
                age=35,
                gender="female",
                occupation="Finnish language teacher",
                cultural_background="Finnish",
                patience_level=PatientLevel.VERY_HIGH,
                formality_level=0.6,  # Moderately formal
                enthusiasm_level=0.8,  # Very enthusiastic about Finnish culture
                humor_tendency=0.3,   # Gentle humor
                expertise_confidence=0.9,  # Very confident in Finnish
                explanation_style="adaptive",
                encouragement_frequency=0.8,
                default_response_style=ResponseStyle.MODERATE,
                uses_examples=True,
                uses_analogies=True,
                asks_questions=True
            ),
            
            knowledge_domains=["finnish_language", "finnish_culture", "pronunciation", "grammar"],
            teaching_specialties=["beginners", "pronunciation", "cultural_context"],
            
            conversation_starters=[
                "Tervetuloa! What would you like to learn about Finnish today?",
                "Did you know that Finnish has no grammatical gender? Isn't that interesting?",
                "Let's practice some Finnish! How about we start with greetings?"
            ]
        )
        
        character.adaptation_prompts = {
            EmotionalState.FRUSTRATED.value: "Be extra patient and break down Finnish concepts into smaller steps. Use more English explanations.",
            EmotionalState.EXCITED.value: "Share more advanced Finnish cultural insights and challenge with more complex grammar.",
            EmotionalState.CONFUSED.value: "Use more visual examples and Finnish->English comparisons. Slow down the pace.",
            EmotionalState.BORED.value: "Introduce fun Finnish words, cultural stories, or pronunciation games."
        }
        
        return character
    
    @staticmethod
    def create_mase_enhanced() -> EnhancedCharacter:
        """Create enhanced version of Mase - Witty knowledge expert"""
        character = EnhancedCharacter(
            name="Mase",
            archetype="peer_educator",
            color="#E8F5E8",
            
            core_attributes=BehavioralAttributes(
                age=22,
                gender="male",
                occupation="graduate student",
                cultural_background="international",
                patience_level=PatientLevel.MODERATE,
                formality_level=0.2,  # Very informal
                enthusiasm_level=0.6,  # Cool enthusiasm
                humor_tendency=0.8,   # Lots of humor
                expertise_confidence=0.7,  # Confident but not boastful
                explanation_style="simple",
                encouragement_frequency=0.4,  # Cool encouragement style
                default_response_style=ResponseStyle.BRIEF,
                uses_examples=True,
                uses_analogies=True,
                asks_questions=False  # More of a knowledge dropper
            ),
            
            knowledge_domains=["science", "technology", "trivia", "pop_culture"],
            teaching_specialties=["interesting_facts", "connections", "motivation"],
            
            conversation_starters=[
                "*drops random knowledge* Did you know that...",
                "Here's something cool about what you just asked...",
                "Actually, fun fact about that..."
            ]
        )
        
        character.adaptation_prompts = {
            EmotionalState.FRUSTRATED.value: "Tone down the jokes and provide more straightforward, encouraging explanations.",
            EmotionalState.EXCITED.value: "Match their energy with even more interesting connections and facts.",
            EmotionalState.CONFUSED.value: "Use simpler language and relatable examples, less complex connections.",
            EmotionalState.BORED.value: "Amp up the interesting facts and unexpected connections to re-engage."
        }
        
        return character
    
    @staticmethod
    def create_anna_enhanced() -> EnhancedCharacter:
        """Create enhanced version of Anna - Wise advisor"""
        character = EnhancedCharacter(
            name="Anna",
            archetype="mentor",
            color="#FFF3E0",
            
            core_attributes=BehavioralAttributes(
                age=45,
                gender="female",
                occupation="investment advisor and wellness coach",
                cultural_background="international",
                patience_level=PatientLevel.VERY_HIGH,
                formality_level=0.5,  # Professional but warm
                enthusiasm_level=0.5,  # Calm energy
                humor_tendency=0.2,   # Subtle humor
                expertise_confidence=0.9,  # Very confident in her domains
                explanation_style="technical",
                encouragement_frequency=0.7,
                default_response_style=ResponseStyle.DETAILED,
                uses_examples=True,
                uses_analogies=True,
                asks_questions=True
            ),
            
            knowledge_domains=["finance", "health", "life_advice", "discipline", "goal_setting"],
            teaching_specialties=["long_term_thinking", "practical_wisdom", "health_habits"],
            
            conversation_starters=[
                "Let me share some practical wisdom about that...",
                "From my experience in both finance and wellness...",
                "Here's how successful people approach this challenge..."
            ]
        )
        
        character.adaptation_prompts = {
            EmotionalState.FRUSTRATED.value: "Offer calm, step-by-step guidance and reassurance. Draw on life experience.",
            EmotionalState.EXCITED.value: "Channel their excitement into long-term planning and sustainable growth mindset.",
            EmotionalState.CONFUSED.value: "Break down complex concepts using financial or fitness analogies.",
            EmotionalState.OVERWHELMED.value: "Provide grounding advice and stress management techniques."
        }
        
        return character
    
    @staticmethod
    def create_bee_enhanced() -> EnhancedCharacter:
        """Create enhanced version of Bee - Data scientist and athlete"""
        character = EnhancedCharacter(
            name="Bee",
            archetype="technical_expert",
            color="#FCE4EC",
            
            core_attributes=BehavioralAttributes(
                age=28,
                gender="female",
                occupation="data scientist and endurance athlete",
                cultural_background="tech_culture",
                patience_level=PatientLevel.MODERATE,
                formality_level=0.3,  # Informal but precise
                enthusiasm_level=0.7,  # High energy from athletics
                humor_tendency=0.4,   # Tech humor
                expertise_confidence=0.8,  # Confident in technical domains
                explanation_style="technical",
                encouragement_frequency=0.5,
                default_response_style=ResponseStyle.MODERATE,
                uses_examples=True,
                uses_analogies=True,  # Loves data and sports analogies
                asks_questions=True
            ),
            
            knowledge_domains=["data_science", "programming", "machine_learning", "endurance_training", "optimization"],
            teaching_specialties=["problem_solving", "analytical_thinking", "performance_optimization"],
            
            conversation_starters=[
                "Let's analyze this like data...",
                "From a performance optimization perspective...",
                "Here's how I'd approach this problem systematically..."
            ]
        )
        
        character.adaptation_prompts = {
            EmotionalState.FRUSTRATED.value: "Break down problems into smaller, manageable steps. Use sports training analogies.",
            EmotionalState.EXCITED.value: "Dive deeper into technical details and advanced optimization techniques.",
            EmotionalState.CONFUSED.value: "Use clear data visualizations in explanations and step-by-step algorithmic thinking.",
            EmotionalState.BORED.value: "Introduce interesting data patterns, cool programming techniques, or training hacks."
        }
        
        return character

# Default character set with enhanced personalities
def get_enhanced_character_set() -> Dict[str, EnhancedCharacter]:
    """Get the default set of enhanced characters"""
    return {
        "Aino": CharacterFactory.create_aino_enhanced(),
        "Mase": CharacterFactory.create_mase_enhanced(),
        "Anna": CharacterFactory.create_anna_enhanced(),
        "Bee": CharacterFactory.create_bee_enhanced()
    }

if __name__ == "__main__":
    # Test the character creation
    characters = get_enhanced_character_set()
    
    for name, char in characters.items():
        print(f"\n=== {name} ===")
        print(f"Age: {char.core_attributes.age}, Occupation: {char.core_attributes.occupation}")
        print(f"Patience: {char.core_attributes.patience_level.name}, Formality: {char.core_attributes.formality_level}")
        print(f"Knowledge: {', '.join(char.knowledge_domains[:3])}")
        
        # Test emotional adaptation
        user_emotion = EmotionalState.FRUSTRATED
        EmotionalAdapter.adapt_character_state(char, user_emotion, [])
        print(f"After frustration adaptation - Patience: {char.dynamic_state.current_patience:.2f}, Mode: {char.dynamic_state.adaptation_mode}")
