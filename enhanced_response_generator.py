"""
Enhanced AI Response Generation with Character Personality Framework Integration
Replaces the basic generate_ai_response function with multi-layered context awareness
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
    
    def _call_anthropic_api(self, complete_context: str, user_message: str, 
                           character: EnhancedCharacter) -> str:
        """Call Anthropic API with enhanced context"""
        
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
            
            # Determine max tokens based on response style
            style_token_map = {
                "brief": 100,
                "moderate": 200,
                "detailed": 300,
                "comprehensive": 400
            }
            max_tokens = style_token_map.get(
                character.core_attributes.default_response_style.value, 200
            )
            
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
            base_response = f"*connection glitch* Tech problems... but hey, your question about '{user_message[:30]}' is still worth exploring!"
            if enthusiasm > 0.6:
                base_response += " This is actually pretty interesting stuff even without the AI magic."
        
        elif character_name == "Anna":
            base_response = f"I'm experiencing technical difficulties, but with {patience_desc} patience, I want to give your question the thoughtful response it deserves."
            if formality > 0.4:
                base_response += " Please bear with me while I work through this connection issue."
        
        elif character_name == "Bee":
            base_response = f"System bottleneck detected! While I debug this connection issue, I'm still thinking analytically about your request."
            if character.dynamic_state.adaptation_mode == "challenging":
                base_response += " This is actually a good lesson in system resilience - want to explore that angle?"
        
        else:
            base_response = f"I'm having connection issues, but my enhanced personality ({patience_desc} patience, {formality:.1f} formality) is still here to help!"
        
        if error_reason and "API key" in error_reason:
            base_response += "\n\n*Note: Administrator needs to configure API access for full AI responses*"
        
        return base_response
    
    def _generate_fallback_response(self, character_name: str, user_message: str, 
                                   error_reason: str) -> str:
        """Generate fallback response when AI service fails"""
        
        fallback_responses = {
            "Aino": f"Anteeksi (sorry)! I'm having trouble connecting right now. Let's try again - what would you like to learn about Finnish today?",
            "Mase": f"*connection issues* Hmm, tech problems... but hey, your question about '{user_message[:30]}' is still interesting!",
            "Anna": f"I'm experiencing some technical difficulties, but your question deserves a thoughtful response. Let me try again in a moment.",
            "Bee": f"Looks like we hit a system bottleneck. While I debug this, can you tell me more about what you're trying to solve?"
        }
        
        base_response = fallback_responses.get(character_name, "I'm having connection issues, but I'm still here to help!")
        
        if "API key" in error_reason:
            return f"{base_response} (Note: Administrator needs to configure API access)"
        else:
            return f"{base_response} (Error: {error_reason[:50]}...)"
    
    def _update_character_after_interaction(self, character: EnhancedCharacter, user_id: str,
                                          user_message: str, response_text: str, 
                                          user_emotion: EmotionalState) -> None:
        """Update character state and memory after successful interaction"""
        
        # Update dynamic state
        character.dynamic_state.messages_this_session += 1
        
        # Extract and store new memories
        self._extract_and_store_memories(character, user_id, user_message, user_emotion)
        
        # Update character memory relationships
        self._update_character_relationships(character, user_message, user_emotion)
        
        # Save updated state to database
        self.db.save_character_state(character, user_id)
    
    def _extract_and_store_memories(self, character: EnhancedCharacter, user_id: str,
                                   user_message: str, user_emotion: EmotionalState) -> None:
        """Extract meaningful memories from user interaction"""
        
        message_lower = user_message.lower()
        
        # Preference detection
        if any(word in message_lower for word in ['like', 'love', 'enjoy', 'prefer']):
            memory_content = f"User expressed positive sentiment about: {user_message[:50]}"
            self.db.store_enhanced_memory(
                character.name, user_id, 'preference', memory_content,
                importance=7.0, emotional_context=user_emotion.value
            )
            character.character_memory.preferred_topics.append(user_message[:30])
        
        # Learning struggle detection
        if any(word in message_lower for word in ['difficult', 'hard', 'confused', 'don\'t understand']):
            memory_content = f"User struggled with: {user_message[:50]}"
            self.db.store_enhanced_memory(
                character.name, user_id, 'learning_pattern', memory_content,
                importance=8.0, emotional_context=user_emotion.value
            )
            character.character_memory.known_weaknesses.append(user_message[:30])
        
        # Success detection
        if any(word in message_lower for word in ['got it', 'understand', 'makes sense', 'thanks']):
            memory_content = f"User successfully learned: {user_message[:50]}"
            self.db.store_enhanced_memory(
                character.name, user_id, 'achievement', memory_content,
                importance=6.0, emotional_context=user_emotion.value
            )
            character.character_memory.known_strengths.append(user_message[:30])
        
        # Personal information detection
        if any(word in message_lower for word in ['my', 'i am', 'i have', 'i work', 'i study']):
            memory_content = f"Personal info: {user_message[:50]}"
            self.db.store_enhanced_memory(
                character.name, user_id, 'fact', memory_content,
                importance=5.0, emotional_context=user_emotion.value
            )
    
    def _update_character_relationships(self, character: EnhancedCharacter, 
                                       user_message: str, user_emotion: EmotionalState) -> None:
        """Update relationship metrics based on interaction"""
        
        # Positive emotions increase rapport
        positive_emotions = [EmotionalState.EXCITED, EmotionalState.ENGAGED, EmotionalState.CURIOUS]
        if user_emotion in positive_emotions:
            character.character_memory.rapport_level = min(1.0, 
                character.character_memory.rapport_level + 0.05)
            character.character_memory.trust_level = min(1.0,
                character.character_memory.trust_level + 0.03)
        
        # Frustrated emotions need careful handling
        elif user_emotion == EmotionalState.FRUSTRATED:
            # Small trust decrease unless we adapt well
            character.character_memory.trust_level = max(0.0,
                character.character_memory.trust_level - 0.02)
        
        # Detect learning style patterns
        if any(word in user_message.lower() for word in ['show me', 'example', 'picture']):
            character.character_memory.learning_style_detected = 'visual'
        elif any(word in user_message.lower() for word in ['explain', 'tell me', 'say']):
            character.character_memory.learning_style_detected = 'auditory'
        elif any(word in user_message.lower() for word in ['try', 'practice', 'do']):
            character.character_memory.learning_style_detected = 'kinesthetic'
    
    def _record_interaction_analytics(self, user_id: str, character_name: str, 
                                    user_message: str, response_text: str,
                                    user_emotion: EmotionalState, emotion_confidence: float,
                                    adaptation_mode: str) -> Dict[str, Any]:
        """Record detailed analytics for this interaction"""
        
        # Simple effectiveness heuristics (could be much more sophisticated)
        response_length_score = min(1.0, len(response_text) / 200.0)  # Ideal ~200 chars
        emotion_appropriate_score = emotion_confidence  # How confident we are in emotion detection
        
        # Engagement score based on user message characteristics
        engagement_indicators = ['?', 'how', 'what', 'why', 'cool', 'interesting', 'more']
        engagement_score = min(1.0, sum(1 for word in engagement_indicators 
                                       if word in user_message.lower()) / 3.0)
        
        # Learning progress indicator (very basic)
        progress_indicators = ['understand', 'got it', 'makes sense', 'ah', 'oh']
        progress_score = min(1.0, sum(1 for word in progress_indicators 
                                     if word in user_message.lower()) / 2.0)
        
        # Overall effectiveness
        effectiveness = (response_length_score + emotion_appropriate_score + engagement_score) / 3.0
        
        # Record in database (would need message_id in real implementation)
        message_id = f"temp_{int(time.time())}"  # Temporary ID
        
        self.db.record_learning_interaction(
            user_id, character_name, message_id, user_emotion,
            adaptation_mode, effectiveness, engagement_score, progress_score
        )
        
        return {
            'user_emotion': user_emotion.value,
            'emotion_confidence': emotion_confidence,
            'adaptation_mode': adaptation_mode,
            'effectiveness': effectiveness,
            'engagement_score': engagement_score,
            'progress_score': progress_score,
            'response_length': len(response_text)
        }
    
    def get_character_for_streamlit(self, character_name: str) -> Dict[str, Any]:
        """Get character data formatted for Streamlit display"""
        if character_name not in self.characters:
            return {}
        
        character = self.characters[character_name]
        
        return {
            'name': character.name,
            'archetype': character.archetype,
            'description': f"{character.core_attributes.occupation}, age {character.core_attributes.age}",
            'color': character.color,
            'knowledge_domains': character.knowledge_domains,
            'teaching_specialties': character.teaching_specialties,
            'patience_level': character.core_attributes.patience_level.name,
            'formality_level': character.core_attributes.formality_level,
            'enthusiasm_level': character.core_attributes.enthusiasm_level,
            'default_response_style': character.core_attributes.default_response_style.value
        }
    
    def run_ab_test_for_user(self, user_id: str, character_name: str, 
                           experiment_name: str = "patience_level_test") -> str:
        """Run A/B test for character personality variants"""
        
        # Check if user is already in experiment
        variant = self.db.get_user_experiment_variant(user_id, experiment_name)
        
        if variant is None:
            # Create experiment if it doesn't exist
            variants = {
                "high_patience": {
                    "core_attributes": {
                        "patience_level": "VERY_HIGH",
                        "encouragement_frequency": 0.9
                    }
                },
                "moderate_patience": {
                    "core_attributes": {
                        "patience_level": "MODERATE", 
                        "encouragement_frequency": 0.5
                    }
                }
            }
            
            try:
                self.db.create_ab_test_experiment(experiment_name, character_name, variants)
                variant = self.db.assign_user_to_experiment(user_id, experiment_name)
            except:
                variant = "control"
        
        return variant

# Integration function for existing Streamlit app
def generate_enhanced_ai_response(character_name: str, user_id: str, user_message: str, 
                                conversation_history: List[Dict], 
                                db: EnhancedEduChatDatabase) -> str:
    """
    Drop-in replacement for the existing generate_ai_response function
    
    This function maintains compatibility with the existing Streamlit app
    while providing enhanced personality framework capabilities.
    """
    
    # Initialize enhanced response generator
    if 'enhanced_generator' not in st.session_state:
        st.session_state.enhanced_generator = EnhancedResponseGenerator(db)
    
    generator = st.session_state.enhanced_generator
    
    # Generate enhanced response
    response_text, metadata = generator.generate_enhanced_response(
        character_name, user_id, user_message, conversation_history
    )
    
    # Display debug info in sidebar if enabled
    if st.sidebar.checkbox("Show Enhanced Character Debug", value=False, key=f"debug_{character_name}_{user_id}"):
        with st.sidebar.expander(f"Debug: {character_name} Response"):
            st.json(metadata)
            
            character_info = generator.get_character_for_streamlit(character_name)
            st.write("**Character State:**")
            st.write(f"Patience: {character_info.get('patience_level', 'Unknown')}")
            st.write(f"Formality: {character_info.get('formality_level', 0):.2f}")
            st.write(f"Enthusiasm: {character_info.get('enthusiasm_level', 0):.2f}")
    
    return response_text

if __name__ == "__main__":
    # Test the enhanced response generator
    from enhanced_database_models import EnhancedEduChatDatabase
    
    db = EnhancedEduChatDatabase("test_enhanced.db")
    generator = EnhancedResponseGenerator(db)
    
    # Test response generation
    test_message = "I'm really confused about Finnish grammar"
    test_history = [
        {"sender": "You", "content": "Hi Aino!", "timestamp": datetime.now()},
        {"sender": "Aino", "content": "Hei! Nice to meet you!", "timestamp": datetime.now()}
    ]
    
    response, metadata = generator.generate_enhanced_response(
        "Aino", "test_user", test_message, test_history
    )
    
    print(f"Response: {response}")
    print(f"Metadata: {metadata}")
    
    print("\nEnhanced response generation system ready!")
