"""
Character Personality Framework Testing & Validation Suite
Comprehensive testing system for family feedback and A/B testing
"""

import json
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from dataclasses import dataclass

from enhanced_database_models import EnhancedEduChatDatabase
from character_personality_framework import (
    EnhancedCharacter, EmotionalState, CharacterFactory, 
    EmotionalAdapter, ContextBuilder
)
from enhanced_response_generator import EnhancedResponseGenerator

@dataclass
class TestScenario:
    """Test scenario for character personality validation"""
    name: str
    description: str
    user_message: str
    expected_emotion: EmotionalState
    context_setup: List[Dict]
    success_criteria: Dict[str, Any]
    character_focus: Optional[str] = None

class CharacterPersonalityTester:
    """Comprehensive testing framework for character personalities"""
    
    def __init__(self, db: EnhancedEduChatDatabase):
        self.db = db
        self.response_generator = EnhancedResponseGenerator(db)
        self.test_scenarios = self._create_test_scenarios()
    
    def _create_test_scenarios(self) -> List[TestScenario]:
        """Create comprehensive test scenarios for character validation"""
        return [
            # Frustration Handling Tests
            TestScenario(
                name="Frustration Adaptation - Aino",
                description="Test how Aino adapts to frustrated Finnish learner",
                user_message="I don't understand Finnish grammar at all! It's so confusing and difficult!",
                expected_emotion=EmotionalState.FRUSTRATED,
                context_setup=[
                    {"sender": "You", "content": "Hi Aino, can you teach me Finnish?"},
                    {"sender": "Aino", "content": "Hei! I'd love to help you learn Finnish!"},
                    {"sender": "You", "content": "I tried studying cases but I'm lost..."}
                ],
                success_criteria={
                    "increased_patience": True,
                    "simplified_language": True,
                    "encouragement_present": True,
                    "response_length": "brief"
                },
                character_focus="Aino"
            ),
            
            TestScenario(
                name="Excitement Amplification - Mase", 
                description="Test how Mase responds to excited learner",
                user_message="That's so cool! I love learning about quantum physics! Tell me more!",
                expected_emotion=EmotionalState.EXCITED,
                context_setup=[
                    {"sender": "You", "content": "What's interesting in science lately?"},
                    {"sender": "Mase", "content": "*drops knowledge* Quantum computers are getting wild..."}
                ],
                success_criteria={
                    "energy_match": True,
                    "advanced_content": True,
                    "enthusiasm_present": True,
                    "deeper_explanations": True
                },
                character_focus="Mase"
            ),
            
            TestScenario(
                name="Confusion Support - Anna",
                description="Test how Anna helps confused learner",
                user_message="I'm confused about investment strategies. There's so much information...",
                expected_emotion=EmotionalState.CONFUSED,
                context_setup=[
                    {"sender": "You", "content": "Anna, I want to start investing but don't know where to begin"},
                    {"sender": "Anna", "content": "Smart question. Let's start with the fundamentals..."}
                ],
                success_criteria={
                    "step_by_step_approach": True,
                    "analogies_used": True,
                    "reassuring_tone": True,
                    "practical_examples": True
                },
                character_focus="Anna"
            ),
            
            TestScenario(
                name="Technical Deep Dive - Bee",
                description="Test Bee's technical adaptation to engaged learner", 
                user_message="I want to understand machine learning algorithms from a mathematical perspective",
                expected_emotion=EmotionalState.ENGAGED,
                context_setup=[
                    {"sender": "You", "content": "Bee, can you explain data science concepts?"},
                    {"sender": "Bee", "content": "Let's analyze this systematically..."}
                ],
                success_criteria={
                    "technical_depth": True,
                    "mathematical_concepts": True,
                    "analytical_approach": True,
                    "performance_focus": True
                },
                character_focus="Bee"
            ),
            
            # Memory Integration Tests
            TestScenario(
                name="Memory Recall Test",
                description="Test character memory integration in responses",
                user_message="Can you help me with another Finnish lesson?",
                expected_emotion=EmotionalState.ENGAGED,
                context_setup=[
                    # This assumes previous memory about user's Finnish interest
                ],
                success_criteria={
                    "memory_referenced": True,
                    "personalized_approach": True,
                    "continuity_maintained": True
                },
                character_focus="Aino"
            )
        ]
    
    def run_single_test(self, scenario: TestScenario, user_id: str = "test_user") -> Dict[str, Any]:
        """Run a single test scenario and return results"""
        
        print(f"🧪 Running test: {scenario.name}")
        
        # Generate response using the scenario
        response_text, metadata = self.response_generator.generate_enhanced_response(
            scenario.character_focus or "Aino",
            user_id,
            scenario.user_message,
            scenario.context_setup
        )
        
        # Analyze response against success criteria
        results = self._analyze_response(response_text, metadata, scenario.success_criteria)
        
        return {
            'scenario_name': scenario.name,
            'description': scenario.description,
            'user_message': scenario.user_message,
            'expected_emotion': scenario.expected_emotion.value,
            'detected_emotion': metadata.get('user_emotion', 'unknown'),
            'response_text': response_text,
            'response_metadata': metadata,
            'success_criteria_met': results,
            'overall_score': results['overall_score'],
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_response(self, response_text: str, metadata: Dict, 
                         criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze response against success criteria"""
        
        results = {}
        score = 0
        total_criteria = len(criteria)
        
        response_lower = response_text.lower()
        
        # Check each criterion
        if 'increased_patience' in criteria and criteria['increased_patience']:
            # Look for patient language indicators
            patient_words = ['don\'t worry', 'let\'s take', 'step by step', 'slowly', 'no rush']
            results['increased_patience'] = any(word in response_lower for word in patient_words)
            if results['increased_patience']:
                score += 1
        
        if 'simplified_language' in criteria and criteria['simplified_language']:
            # Check for simpler sentence structure (basic heuristic)
            avg_sentence_length = len(response_text.split()) / max(1, response_text.count('.') + response_text.count('!') + response_text.count('?'))
            results['simplified_language'] = avg_sentence_length < 15
            if results['simplified_language']:
                score += 1
        
        if 'encouragement_present' in criteria and criteria['encouragement_present']:
            encouraging_words = ['you can', 'great', 'good', 'excellent', 'keep going', 'well done']
            results['encouragement_present'] = any(word in response_lower for word in encouraging_words)
            if results['encouragement_present']:
                score += 1
        
        if 'response_length' in criteria:
            expected_length = criteria['response_length']
            actual_length = len(response_text.split())
            
            if expected_length == 'brief':
                results['response_length'] = actual_length < 50
            elif expected_length == 'detailed':
                results['response_length'] = actual_length > 100
            else:
                results['response_length'] = 50 <= actual_length <= 100
            
            if results['response_length']:
                score += 1
        
        if 'energy_match' in criteria and criteria['energy_match']:
            energetic_indicators = ['!', 'awesome', 'amazing', 'cool', 'wild', 'incredible']
            results['energy_match'] = any(word in response_lower for word in energetic_indicators)
            if results['energy_match']:
                score += 1
        
        if 'technical_depth' in criteria and criteria['technical_depth']:
            technical_words = ['algorithm', 'mathematical', 'function', 'optimization', 'analysis']
            results['technical_depth'] = any(word in response_lower for word in technical_words)
            if results['technical_depth']:
                score += 1
        
        if 'analogies_used' in criteria and criteria['analogies_used']:
            analogy_indicators = ['like', 'similar to', 'imagine', 'think of it as', 'it\'s like']
            results['analogies_used'] = any(phrase in response_lower for phrase in analogy_indicators)
            if results['analogies_used']:
                score += 1
        
        if 'memory_referenced' in criteria and criteria['memory_referenced']:
            # Check if response shows awareness of past interactions
            memory_indicators = ['remember', 'last time', 'you mentioned', 'as we discussed']
            results['memory_referenced'] = any(phrase in response_lower for phrase in memory_indicators)
            if results['memory_referenced']:
                score += 1
        
        # Calculate overall score
        results['overall_score'] = score / max(1, total_criteria)
        results['criteria_met'] = score
        results['total_criteria'] = total_criteria
        
        return results
    
    def run_full_test_suite(self, user_id: str = "test_user") -> List[Dict[str, Any]]:
        """Run all test scenarios and return comprehensive results"""
        
        results = []
        
        for scenario in self.test_scenarios:
            try:
                result = self.run_single_test(scenario, user_id)
                results.append(result)
                print(f"✅ {scenario.name}: Score {result['overall_score']:.2f}")
            except Exception as e:
                print(f"❌ {scenario.name}: Failed - {str(e)}")
                results.append({
                    'scenario_name': scenario.name,
                    'error': str(e),
                    'overall_score': 0.0,
                    'timestamp': datetime.now().isoformat()
                })
        
        return results

class FamilyTestingInterface:
    """Streamlit interface for family testing and feedback"""
    
    def __init__(self, db: EnhancedEduChatDatabase):
        self.db = db
        self.tester = CharacterPersonalityTester(db)
    
    def show_testing_interface(self, current_user):
        """Show the family testing interface in Streamlit"""
        
        st.title("🧪 Character Personality Testing Lab")
        st.markdown("*Help us improve the AI learning companions by testing their personalities!*")
        
        # Testing modes
        test_mode = st.selectbox(
            "Choose Testing Mode:",
            ["Family Feedback", "Automated Testing", "A/B Comparison", "Character Deep Dive"]
        )
        
        if test_mode == "Family Feedback":
            self._show_family_feedback_interface(current_user)
        elif test_mode == "Automated Testing":
            self._show_automated_testing_interface(current_user)
        elif test_mode == "A/B Comparison":
            self._show_ab_comparison_interface(current_user)
        elif test_mode == "Character Deep Dive":
            self._show_character_deep_dive_interface(current_user)
    
    def _show_family_feedback_interface(self, current_user):
        """Show interface for family members to provide feedback"""
        
        st.subheader("👨‍👩‍👧‍👦 Family Feedback Collection")
        
        # Character evaluation
        character_to_evaluate = st.selectbox("Which character would you like to evaluate?", 
                                           ["Aino", "Mase", "Anna", "Bee"])
        
        # Recent conversation recall
        st.write("Think about your recent conversation with this character...")
        
        # Feedback dimensions
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Personality Ratings:**")
            helpfulness = st.slider(f"How helpful was {character_to_evaluate}?", 1, 10, 7)
            patience = st.slider(f"How patient was {character_to_evaluate}?", 1, 10, 7)
            naturalness = st.slider(f"How natural did {character_to_evaluate} feel?", 1, 10, 7)
            engagement = st.slider(f"How engaging was {character_to_evaluate}?", 1, 10, 7)
        
        with col2:
            st.write("**Learning Impact:**")
            understanding = st.slider("Did you learn something new?", 1, 10, 7)
            motivation = st.slider("Did it motivate you to learn more?", 1, 10, 7)
            appropriate_level = st.slider("Was the difficulty level right?", 1, 10, 7)
            memorable = st.slider("Will you remember this conversation?", 1, 10, 7)
        
        # Open feedback
        st.write("**Tell us more:**")
        what_worked = st.text_area("What worked well about this character?")
        what_could_improve = st.text_area("What could be better?")
        emotional_reaction = st.selectbox(
            "How did the character make you feel?",
            ["Excited to learn", "Comfortable and supported", "Challenged appropriately", 
             "Confused", "Frustrated", "Bored", "Other"]
        )
        
        would_recommend = st.radio("Would you recommend this character to a friend?", 
                                 ["Definitely yes", "Probably yes", "Maybe", "Probably no", "Definitely no"])
        
        if st.button("Submit Feedback"):
            # Store feedback in database
            feedback_data = {
                'character_name': character_to_evaluate,
                'user_id': current_user.id,
                'ratings': {
                    'helpfulness': helpfulness,
                    'patience': patience,
                    'naturalness': naturalness,
                    'engagement': engagement,
                    'understanding': understanding,
                    'motivation': motivation,
                    'appropriate_level': appropriate_level,
                    'memorable': memorable
                },
                'open_feedback': {
                    'what_worked': what_worked,
                    'what_could_improve': what_could_improve,
                    'emotional_reaction': emotional_reaction,
                    'would_recommend': would_recommend
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in database (would need a feedback table)
            self._store_family_feedback(feedback_data)
            
            st.success(f"Thank you for your feedback about {character_to_evaluate}! This helps us improve the AI personalities.")
    
    def _show_automated_testing_interface(self, current_user):
        """Show automated testing interface"""
        
        st.subheader("🤖 Automated Personality Testing")
        
        if st.button("Run Full Test Suite", type="primary"):
            with st.spinner("Running comprehensive personality tests..."):
                results = self.tester.run_full_test_suite(current_user.id)
            
            # Display results
            st.write("## Test Results")
            
            # Overall summary
            overall_scores = [r['overall_score'] for r in results if 'overall_score' in r]
            avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Average Score", f"{avg_score:.2f}")
            with col2:
                st.metric("Tests Passed", f"{sum(1 for s in overall_scores if s >= 0.7)}/{len(overall_scores)}")
            with col3:
                st.metric("Total Tests", len(results))
            
            # Detailed results
            for result in results:
                if 'error' not in result:
                    score = result['overall_score']
                    color = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"
                    
                    with st.expander(f"{color} {result['scenario_name']} - Score: {score:.2f}"):
                        st.write(f"**Description:** {result['description']}")
                        st.write(f"**User Message:** {result['user_message']}")
                        st.write(f"**Expected Emotion:** {result['expected_emotion']}")
                        st.write(f"**Detected Emotion:** {result['detected_emotion']}")
                        st.write(f"**Response:** {result['response_text']}")
                        
                        # Success criteria breakdown
                        criteria_met = result['success_criteria_met']
                        st.write("**Criteria Analysis:**")
                        for criterion, met in criteria_met.items():
                            if criterion not in ['overall_score', 'criteria_met', 'total_criteria']:
                                status = "✅" if met else "❌"
                                st.write(f"{status} {criterion.replace('_', ' ').title()}")
    
    def _show_ab_comparison_interface(self, current_user):
        """Show A/B testing comparison interface"""
        
        st.subheader("⚖️ A/B Character Comparison")
        
        # Set up A/B test
        character_to_test = st.selectbox("Choose character to test:", ["Aino", "Mase", "Anna", "Bee"])
        
        st.write("We'll show you two versions of the same character responding to the same question.")
        
        test_message = st.text_input("Enter your test message:", 
                                   "I'm feeling frustrated with learning today...")
        
        if st.button("Generate A/B Comparison") and test_message:
            with st.spinner("Generating two personality variants..."):
                # Generate two responses with different personality parameters
                original_response, original_meta = self.tester.response_generator.generate_enhanced_response(
                    character_to_test, current_user.id, test_message, []
                )
                
                # Create a variant with modified personality (simulate A/B test)
                # This would integrate with the A/B testing system
                variant_response, variant_meta = self.tester.response_generator.generate_enhanced_response(
                    character_to_test, current_user.id, test_message, []
                )
            
            # Show comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Version A (Original)**")
                st.info(original_response)
                st.json({"emotion_detected": original_meta.get('user_emotion'),
                        "adaptation_mode": original_meta.get('adaptation_mode')})
            
            with col2:
                st.write("**Version B (Variant)**")
                st.info(variant_response)
                st.json({"emotion_detected": variant_meta.get('user_emotion'),
                        "adaptation_mode": variant_meta.get('adaptation_mode')})
            
            # Voting interface
            st.write("**Which version do you prefer?**")
            preference = st.radio("Choose:", ["Version A", "Version B", "No preference"], 
                                horizontal=True)
            
            if preference != "No preference":
                feedback_reason = st.text_area("Why did you prefer this version?")
                
                if st.button("Submit Preference"):
                    # Record A/B test result
                    self._record_ab_test_preference(current_user.id, character_to_test, 
                                                  preference, feedback_reason)
                    st.success("Thank you! Your preference helps improve the AI personalities.")
    
    def _show_character_deep_dive_interface(self, current_user):
        """Show detailed character analysis interface"""
        
        st.subheader("🔬 Character Deep Dive Analysis")
        
        character_name = st.selectbox("Select character for deep analysis:", 
                                    ["Aino", "Mase", "Anna", "Bee"])
        
        # Get character information
        character_info = self.tester.response_generator.get_character_for_streamlit(character_name)
        
        # Display current personality parameters
        st.write("## Current Personality Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Patience Level", character_info.get('patience_level', 'Unknown'))
            st.metric("Formality", f"{character_info.get('formality_level', 0.5):.2f}")
        
        with col2:
            st.metric("Enthusiasm", f"{character_info.get('enthusiasm_level', 0.5):.2f}")
            st.metric("Response Style", character_info.get('default_response_style', 'moderate').title())
        
        with col3:
            st.write("**Knowledge Areas:**")
            for domain in character_info.get('knowledge_domains', []):
                st.write(f"• {domain}")
        
        # Memory analysis for current user
        memories = self.db.get_enhanced_memories(character_name, current_user.id, limit=10)
        
        if memories:
            st.write("## Character Memory Analysis")
            
            # Memory distribution
            memory_types = {}
            importance_scores = []
            
            for memory in memories:
                mem_type = memory['type']
                memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
                importance_scores.append(memory['importance'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Memory Types:**")
                for mem_type, count in memory_types.items():
                    st.write(f"• {mem_type}: {count}")
            
            with col2:
                avg_importance = sum(importance_scores) / len(importance_scores)
                st.metric("Average Memory Importance", f"{avg_importance:.1f}/10")
                st.metric("Total Memories", len(memories))
            
            # Recent memories
            st.write("**Recent Memories:**")
            for memory in memories[:5]:
                importance_color = "🟢" if memory['importance'] > 7 else "🟡" if memory['importance'] > 5 else "⚪"
                st.write(f"{importance_color} {memory['content']} *({memory['type']})*")
    
    def _store_family_feedback(self, feedback_data: Dict):
        """Store family feedback in database"""
        # This would create a feedback table and store the data
        # For now, we'll use the enhanced memory system
        self.db.store_enhanced_memory(
            feedback_data['character_name'],
            feedback_data['user_id'],
            'feedback',
            f"Family feedback: {json.dumps(feedback_data['ratings'])}",
            importance=8.0,
            emotional_context="feedback_session"
        )
    
    def _record_ab_test_preference(self, user_id: str, character_name: str, 
                                  preference: str, reason: str):
        """Record A/B test preference"""
        self.db.store_enhanced_memory(
            character_name,
            user_id,
            'ab_test_preference',
            f"Preferred {preference}: {reason}",
            importance=9.0,
            emotional_context="ab_testing"
        )

# Integration with main app
def show_personality_testing_lab(db: EnhancedEduChatDatabase, current_user):
    """Show the personality testing lab in the main app"""
    
    family_tester = FamilyTestingInterface(db)
    family_tester.show_testing_interface(current_user)

if __name__ == "__main__":
    # Standalone testing
    from enhanced_database_models import EnhancedEduChatDatabase
    
    db = EnhancedEduChatDatabase("test_personality.db")
    tester = CharacterPersonalityTester(db)
    
    print("🧪 Running Character Personality Framework Tests")
    print("=" * 50)
    
    # Run full test suite
    results = tester.run_full_test_suite()
    
    # Summary
    overall_scores = [r['overall_score'] for r in results if 'overall_score' in r]
    avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
    
    print(f"\n📊 Test Summary:")
    print(f"   Average Score: {avg_score:.2f}/1.0")
    print(f"   Tests Passed (≥0.7): {sum(1 for s in overall_scores if s >= 0.7)}/{len(overall_scores)}")
    print(f"   Total Tests: {len(results)}")
    
    # Save results
    with open("personality_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Testing complete! Results saved to personality_test_results.json")
