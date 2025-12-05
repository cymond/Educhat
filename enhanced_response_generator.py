"""
Enhanced AI Response Generation with Character Personality Framework Integration
Replaces the basic generate_ai_response function with multi-layered context awareness
NOW WITH DYNAMIC TOKEN CALCULATION - prevents API truncation
"""

import streamlit as st
import json
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from character_personality_framework import (
    EnhancedCharacter, EmotionalAdapter, ContextBuilder, 
    EmotionalState, CharacterFactory, get_enhanced_character_set
)
from enhanced_database_models import EnhancedEduChatDatabase

class EnhancedResponseGenerator:
    """Advanced AI response generation with personality framework integration"""
    
    def __init__(self, db: EnhancedEduChatDatabase):
        self.db = db
        self.characters = self._initialize_enhanced_characters()
        self.conversation_context_limit = 8  # Number of recent messages to include
        self._last_db_memories = []  # Store memories for dynamic token calculation
    
    def _initialize_enhanced_characters(self) -> Dict[str, EnhancedCharacter]:
        """Initialize enhanced characters from database or create defaults"""
        characters = {}
        
        # Try to load from database first
        default_names = ["Aino", "Mase", "Anna", "Bee"]
        
        for name in default_names:
            character = self.db.load_character_personality(name)
            if character is None:
                # Create default and save to database
                character = self._create_default_character(name)
                self.db.save_character_personality(character)
            characters[name] = character
        
        return characters
    
    def _create_default_character(self, name: str) -> EnhancedCharacter:
        """Create default enhanced character"""
        factory_map = {
            "Aino": CharacterFactory.create_aino_enhanced,
            "Mase": CharacterFactory.create_mase_enhanced, 
            "Anna": CharacterFactory.create_anna_enhanced,
            "Bee": CharacterFactory.create_bee_enhanced
        }
        
        if name in factory_map:
            return factory_map[name]()
        else:
            # Generic character as fallback
            return CharacterFactory.create_aino_enhanced()  # Use Aino as template
    
    def load_character_for_user(self, character_name: str, user_id: str) -> EnhancedCharacter:
        """Load character with user-specific state and memory"""
        if character_name not in self.characters:
            return self._create_default_character(character_name)
        
        # Get base character
        character = self.characters[character_name]
        
        # Load user-specific state and memory
        dynamic_state, character_memory = self.db.load_character_state(character_name, user_id)
        
        if dynamic_state:
            character.dynamic_state = dynamic_state
        if character_memory:
            character.character_memory = character_memory
        
        return character
    
    def generate_enhanced_response(self, character_name: str, user_id: str, 
                                 user_message: str, conversation_history: List[Dict],
                                 detect_emotion: bool = True) -> Tuple[str, Dict[str, Any]]:
        """
        Generate AI response using enhanced character personality framework
        
        Returns: (response_text, interaction_metadata)
        """
        
        # Load character with user-specific context
        character = self.load_character_for_user(character_name, user_id)
        
        # Step 1: Detect user emotion
        user_emotion = EmotionalState.ENGAGED  # Default
        emotion_confidence = 0.3
        
        if detect_emotion:
            user_emotion, emotion_confidence = EmotionalAdapter.detect_user_emotion(
                user_message, conversation_history
            )
        
        # Step 2: Adapt character state based on detected emotion
        EmotionalAdapter.adapt_character_state(character, user_emotion, conversation_history)
        
        # Step 3: Get database memories for knowledge context
        db_memories = self.db.get_enhanced_memories(character_name, user_id, limit=5)
        
        # Store memories for dynamic token calculation
        self._last_db_memories = db_memories
        
        # Step 4: Build complete multi-layer context
        complete_context = ContextBuilder.build_complete_context(
            character, user_message, conversation_history, db_memories, user_id
        )
        
        # Step 5: Generate AI response
        try:
            response_text = self._call_anthropic_api(complete_context, user_message, character)
            
            # Step 6: Update character state and memory
            self._update_character_after_interaction(
                character, user_id, user_message, response_text, user_emotion
            )
            
            # Step 7: Store interaction analytics
            interaction_metadata = self._record_interaction_analytics(
                user_id, character_name, user_message, response_text, 
                user_emotion, emotion_confidence, character.dynamic_state.adaptation_mode
            )
            
            return response_text, interaction_metadata
            
        except Exception as e:
            # Graceful fallback
            error_response = self._generate_fallback_response(character_name, user_message, str(e))
            return error_response, {"error": str(e), "fallback": True}

    def calculate_dynamic_response_tokens(self, character, user_message: str, 
                                        complete_context: str, db_memories: list) -> int:
        """
        Calculate exact tokens needed - prevents API truncation by giving exactly the right space
        """
        
        # Character-specific base needs
        character_base_needs = {
            "Aino": 180,   # Finnish explanations with cultural context
            "Mase": 120,   # Concise but complete knowledge drops
            "Anna": 160,   # Practical wisdom with examples
            "Bee": 170     # Technical precision with clarity
        }
        
        base_tokens = character_base_needs.get(character.name, 150)
        
        # Analyze message complexity
        word_count = len(user_message.split())
        complexity_multiplier = 1.0
        
        if word_count > 25:
            complexity_multiplier = 1.6    # Very complex question
        elif word_count > 15:
            complexity_multiplier = 1.3    # Moderately complex
        elif word_count > 8:
            complexity_multiplier = 1.1    # Simple question
        
        # Detect educational content that needs detailed response
        educational_indicators = [
            'explain', 'how', 'why', 'what', 'teach', 'learn', 'show me',
            'help me understand', 'tell me about', 'describe', 'clarify',
            'difference between', 'compare', 'example', 'step by step'
        ]
        educational_score = sum(1 for phrase in educational_indicators 
                               if phrase in user_message.lower())
        educational_multiplier = 1.0 + (educational_score * 0.25)
        
        # Integrate with your Character Personality Framework
        personality_multiplier = 1.0
        
        try:
            # Use patience level from your CPF
            patience_level = character.core_attributes.patience_level.value
            patience_adjustments = {
                1: 0.85,  # Very low patience = more concise
                2: 0.95,  # Low patience
                3: 1.0,   # Moderate patience = baseline
                4: 1.15,  # High patience = more detailed
                5: 1.3    # Very high patience = comprehensive
            }
            patience_multiplier = patience_adjustments.get(patience_level, 1.0)
            
            # Use formality and enthusiasm from your CPF
            formality = getattr(character.core_attributes, 'formality_level', 3)
            enthusiasm = getattr(character.core_attributes, 'enthusiasm_level', 0.5)
            
            formality_multiplier = 1.0 + (formality - 3) * 0.05  # More formal = slightly more detailed
            enthusiasm_multiplier = 1.0 + enthusiasm * 0.1       # More enthusiastic = slightly longer
            
            personality_multiplier = patience_multiplier * formality_multiplier * enthusiasm_multiplier
            
        except (AttributeError, TypeError):
            # Graceful fallback if CPF structure differs
            personality_multiplier = 1.0
        
        # Memory integration - more memories = more context to weave in
        memory_tokens = min(len(db_memories) * 25, 80) if db_memories else 0
        
        # Question type specific adjustments
        question_multiplier = 1.0
        if '?' in user_message:
            if any(phrase in user_message.lower() for phrase in ['how to', 'step by step']):
                question_multiplier = 1.3  # Process questions need structure
            elif user_message.count('?') > 1:
                question_multiplier = 1.4  # Multiple questions need comprehensive answers
        
        # Calculate final optimal tokens
        calculated_tokens = int(
            base_tokens * 
            complexity_multiplier * 
            educational_multiplier * 
            personality_multiplier * 
            question_multiplier +
            memory_tokens
        )
        
        # Reasonable bounds - generous enough to prevent truncation
        return max(200, min(calculated_tokens, 700))
    
    def _call_anthropic_api(self, complete_context: str, user_message: str, 
                           character: EnhancedCharacter) -> str:
        """Call Anthropic API with enhanced context and dynamic token calculation"""
        
        # Get API configuration
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
            model = st.secrets.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        except:
            try:
                api_key = os.getenv('ANTHROPIC_API_KEY')
                model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
            except:
                api_key = None
                model = "claude-3-5-sonnet-20241022"
        
        if not api_key or api_key == 'your_anthropic_api_key_here':
            return self._generate_enhanced_fallback_response(character.name, user_message, character)
        
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            
            # Calculate exact tokens needed for this specific response
            max_tokens = self.calculate_dynamic_response_tokens(
                character=character,
                user_message=user_message, 
                complete_context=complete_context,
                db_memories=self._last_db_memories
            )
            
            # Optional: Add debug info to see token calculation in action
            # print(f"Dynamic tokens for {character.name}: {max_tokens}")
            
            # Adjust temperature based on character traits
            base_temperature = 0.7
            humor_boost = character.core_attributes.humor_tendency * 0.2
            formality_reduction = (1.0 - character.core_attributes.formality_level) * 0.1
            temperature = min(1.0, base_temperature + humor_boost + formality_reduction)
            
            # Call API
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=complete_context,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            return self._generate_enhanced_fallback_response(character.name, user_message, character, str(e))
    
    def _generate_enhanced_fallback_response(self, character_name: str, user_message: str, 
                                           character: EnhancedCharacter, error_reason: str = None) -> str:
        """Generate enhanced fallback response that demonstrates personality framework"""
        
        # Use character personality to generate fallback
        patience_desc = character.core_attributes.patience_level.name.lower().replace('_', ' ')
        formality = character.core_attributes.formality_level
        enthusiasm = character.core_attributes.enthusiasm_level
        
        if character_name == "Aino":
            base_response = f"Anteeksi (sorry)! I'm having connection issues, but I'm still here with {patience_desc} patience to help you learn Finnish!"
            if character.dynamic_state.adaptation_mode == "supportive":
                base_response += " I noticed you might be feeling frustrated - let's take this step by step when I'm back online."
        
        elif character_name == "Mase":
            base_response = f"Yo, tech hiccup on my end! But hey, that's what happens when you're running on {enthusiasm:.1f} enthusiasm and {patience_desc} patience, right?"
            if character.dynamic_state.adaptation_mode == "energetic":
                base_response += " I was totally ready to drop some knowledge on you too!"
        
        elif character_name == "Anna":
            base_response = f"My apologies - I'm experiencing some technical difficulties. But as someone with {patience_desc} patience, I'm not going anywhere."
            if formality >= 4:
                base_response += " I shall return momentarily to provide the guidance you seek."
            else:
                base_response += " I'll be back to share some wisdom soon!"
        
        elif character_name == "Bee":
            base_response = f"Error in API connection - debugging in progress. My {patience_desc} patience levels are handling this gracefully."
            if character.dynamic_state.adaptation_mode == "analytical":
                base_response += " Analyzing optimal response patterns for when connectivity resumes."
        
        else:
            base_response = f"I'm experiencing connection issues but my {patience_desc} patience keeps me optimistic!"
        
        if error_reason:
            base_response += f" (Technical note: {error_reason[:50]}...)"
        
        return base_response
    
    def _generate_fallback_response(self, character_name: str, user_message: str, error_reason: str) -> str:
        """Simple fallback when character object is not available"""
        fallbacks = {
            "Aino": f"Anteeksi! Technical issues, but I'll help you learn Finnish soon!",
            "Mase": f"Tech troubles! But I've got knowledge to drop when I'm back online.",
            "Anna": f"Having connection issues, but I'll return with practical wisdom shortly.",
            "Bee": f"Connection error detected - will resume analytical responses momentarily."
        }
        
        base = fallbacks.get(character_name, "Connection issues - back soon!")
        return f"{base} (Error: {error_reason[:30]}...)"
    
    def _update_character_after_interaction(self, character: EnhancedCharacter, user_id: str, 
                                           user_message: str, response_text: str, user_emotion: EmotionalState):
        """Update character state and memory after interaction"""
        
        # Update character memory with new interaction
        memory_content = f"User said: '{user_message[:100]}...' Response given about: {response_text[:50]}..."
        character.character_memory.store_memory(
            memory_type="interaction",
            content=memory_content,
            importance=self._calculate_memory_importance(user_emotion, user_message),
            emotional_context=user_emotion.value
        )
        
        # Update dynamic state
        character.dynamic_state.last_interaction = datetime.now()
        character.dynamic_state.interaction_count += 1
        
        # Save updated character state to database
        self.db.save_character_state(character.name, user_id, character.dynamic_state, character.character_memory)
    
    def _calculate_memory_importance(self, user_emotion: EmotionalState, user_message: str) -> int:
        """Calculate importance score for memory storage"""
        base_importance = 5
        
        # Emotional context affects importance
        emotion_modifiers = {
            EmotionalState.FRUSTRATED: 2,  # Remember frustrating interactions
            EmotionalState.EXCITED: 1,     # Remember exciting moments
            EmotionalState.CONFUSED: 2,    # Remember confusion to avoid repeating
            EmotionalState.OVERWHELMED: 3  # Very important to remember overwhelm triggers
        }
        
        base_importance += emotion_modifiers.get(user_emotion, 0)
        
        # Learning-related interactions are more important
        learning_keywords = ["learn", "teach", "explain", "help", "understand", "practice"]
        if any(keyword in user_message.lower() for keyword in learning_keywords):
            base_importance += 2
        
        return min(base_importance, 10)  # Cap at 10
    
    def _record_interaction_analytics(self, user_id: str, character_name: str, user_message: str, 
                                    response_text: str, user_emotion: EmotionalState, 
                                    emotion_confidence: float, adaptation_mode: str) -> Dict[str, Any]:
        """Record detailed analytics for this interaction"""
        
        analytics = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "character_name": character_name,
            "user_message_length": len(user_message.split()),
            "response_length": len(response_text.split()),
            "user_emotion": user_emotion.value,
            "emotion_confidence": emotion_confidence,
            "adaptation_mode": adaptation_mode,
            "interaction_type": self._classify_interaction_type(user_message),
            "educational_content": self._detect_educational_content(user_message),
            "response_generation_success": not response_text.startswith("[Error"),
        }
        
        # Store analytics in database
        try:
            self.db.record_interaction_analytics(analytics)
        except Exception as e:
            # Don't let analytics failures break the conversation
            analytics["analytics_storage_error"] = str(e)
        
        return analytics
    
    def _classify_interaction_type(self, user_message: str) -> str:
        """Classify the type of interaction for analytics"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good evening']):
            return "greeting"
        elif '?' in user_message:
            if any(word in message_lower for word in ['how', 'what', 'why', 'when', 'where']):
                return "question_educational"
            else:
                return "question_general"
        elif any(word in message_lower for word in ['thank', 'thanks', 'appreciate']):
            return "gratitude"
        elif any(word in message_lower for word in ['learn', 'teach', 'practice', 'study']):
            return "learning_request"
        else:
            return "conversation"
    
    def _detect_educational_content(self, user_message: str) -> bool:
        """Detect if the message contains educational content requests"""
        educational_indicators = [
            'explain', 'how', 'why', 'what', 'teach', 'learn', 'show', 'help',
            'understand', 'clarify', 'describe', 'tell me about'
        ]
        return any(indicator in user_message.lower() for indicator in educational_indicators)

    def get_character_analytics(self, character_name: str, user_id: str) -> Dict[str, Any]:
        """Get analytics for a specific character-user combination"""
        try:
            return self.db.get_character_analytics(character_name, user_id)
        except Exception as e:
            return {"error": f"Could not retrieve analytics: {str(e)}"}

    def get_character_for_streamlit(self, character_name: str) -> Dict[str, Any]:
        """Get character information for Streamlit UI display"""
        try:
            if character_name in self.characters:
                character = self.characters[character_name]
                
                # Extract character info for UI display
                character_info = {
                    'name': character.name,
                    'archetype': getattr(character, 'archetype', character_name),
                    'description': getattr(character.core_attributes, 'occupation', f'{character_name} - AI Learning Companion'),
                    'patience_level': character.core_attributes.patience_level.name.lower().replace('_', ' '),
                    'formality_level': getattr(character.core_attributes, 'formality_level', 3),
                    'enthusiasm_level': getattr(character.core_attributes, 'enthusiasm_level', 0.5),
                    'humor_tendency': getattr(character.core_attributes, 'humor_tendency', 0.3),
                    'default_response_style': character.core_attributes.default_response_style.value,
                    'personality_traits': getattr(character, 'personality_summary', f'{character_name} personality'),
                    'knowledge_domains': getattr(character, 'knowledge_areas', [f'{character_name} expertise'])
                }
                
                return character_info
                
            else:
                # Fallback character info
                fallback_info = {
                    'Aino': {
                        'name': 'Aino',
                        'archetype': 'Cultural Teacher',
                        'description': 'Native Finnish speaker and cultural guide',
                        'patience_level': 'very high',
                        'formality_level': 4,
                        'enthusiasm_level': 0.8,
                        'humor_tendency': 0.3,
                        'default_response_style': 'detailed',
                        'personality_traits': 'Patient, encouraging, culturally insightful',
                        'knowledge_domains': ['Finnish language', 'Nordic culture', 'pronunciation']
                    },
                    'Mase': {
                        'name': 'Mase',
                        'archetype': 'Peer Educator',
                        'description': 'Young knowledge enthusiast with casual wisdom',
                        'patience_level': 'moderate',
                        'formality_level': 2,
                        'enthusiasm_level': 0.6,
                        'humor_tendency': 0.8,
                        'default_response_style': 'brief',
                        'personality_traits': 'Witty, casual, surprisingly knowledgeable',
                        'knowledge_domains': ['Science', 'Technology', 'Pop culture', 'Trivia']
                    },
                    'Anna': {
                        'name': 'Anna',
                        'archetype': 'Wise Mentor',
                        'description': 'Experienced advisor with practical wisdom',
                        'patience_level': 'very high',
                        'formality_level': 4,
                        'enthusiasm_level': 0.5,
                        'humor_tendency': 0.2,
                        'default_response_style': 'moderate',
                        'personality_traits': 'Wise, practical, calm, supportive',
                        'knowledge_domains': ['Life advice', 'Finance', 'Health', 'Parenting']
                    },
                    'Bee': {
                        'name': 'Bee',
                        'archetype': 'Technical Expert',
                        'description': 'Data scientist and analytical thinker',
                        'patience_level': 'moderate',
                        'formality_level': 3,
                        'enthusiasm_level': 0.7,
                        'humor_tendency': 0.4,
                        'default_response_style': 'detailed',
                        'personality_traits': 'Technical, athletic, analytical, precise',
                        'knowledge_domains': ['Data science', 'Programming', 'Analytics', 'Sports']
                    }
                }
                
                return fallback_info.get(character_name, {
                    'name': character_name,
                    'archetype': 'AI Companion',
                    'description': 'Helpful learning companion',
                    'patience_level': 'moderate',
                    'formality_level': 3,
                    'enthusiasm_level': 0.5,
                    'humor_tendency': 0.3,
                    'default_response_style': 'moderate',
                    'personality_traits': 'Helpful and adaptive',
                    'knowledge_domains': ['General knowledge']
                })
                
        except Exception as e:
            # Ultra-safe fallback
            return {
                'name': character_name,
                'archetype': 'AI Companion',
                'description': 'Helpful learning companion',
                'patience_level': 'moderate',
                'formality_level': 3,
                'enthusiasm_level': 0.5,
                'humor_tendency': 0.3,
                'default_response_style': 'moderate',
                'personality_traits': 'Helpful and adaptive',
                'knowledge_domains': ['General knowledge'],
                'error': str(e)
            }


# Standalone function for backward compatibility
def generate_enhanced_ai_response(character_name: str, user_id: str, user_message: str, 
                                conversation_history: List[Dict], db: EnhancedEduChatDatabase) -> Tuple[str, Dict]:
    """
    Standalone function for backward compatibility with existing code
    """
    generator = EnhancedResponseGenerator(db)
    return generator.generate_enhanced_response(character_name, user_id, user_message, conversation_history)
