"""
Enhanced Character Memory System for EduChat
Compatible with your existing database and character structure
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import uuid

@dataclass
class MemoryItem:
    """Enhanced memory item with metadata"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    character_name: str = ""
    user_id: str = ""
    memory_type: str = ""  # 'preference', 'fact', 'achievement', 'learning_style', 'correction'
    content: str = ""
    importance_score: int = 5  # 1-10
    emotional_context: str = ""  # 'positive', 'neutral', 'frustration', 'excitement'
    topics: List[str] = field(default_factory=list)  # Associated topics
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    decay_rate: float = 0.95  # How quickly importance fades

class AdvancedMemoryEngine:
    """Advanced character memory system compatible with your existing EduChat structure"""
    
    def __init__(self, db):
        self.db = db
        self.memory_extractors = self._setup_memory_extractors()
        self.topic_keywords = self._setup_topic_keywords()
    
    def _setup_memory_extractors(self) -> Dict[str, Any]:
        """Setup patterns for extracting different types of memories"""
        return {
            'preferences': [
                r"I (like|love|enjoy|prefer) (.+)",
                r"I (don't like|hate|dislike) (.+)",
                r"I usually (.+)",
                r"I always (.+)",
                r"My favorite (.+) is (.+)"
            ],
            'learning_style': [
                r"I learn best when (.+)",
                r"I understand better if (.+)",
                r"Can you explain (.+) more simply",
                r"I'm confused about (.+)",
                r"That makes sense now",
                r"I need more practice with (.+)"
            ],
            'facts': [
                r"I am (.+)",
                r"I work as (.+)",
                r"I live in (.+)",
                r"My (.+) is (.+)",
                r"I have (.+)",
                r"I study (.+)",
                r"I'm learning (.+)"
            ],
            'goals': [
                r"I want to (.+)",
                r"I'm trying to (.+)",
                r"My goal is (.+)",
                r"I hope to (.+)",
                r"I need to (.+)"
            ],
            'emotional_context': [
                r"I'm (excited|frustrated|confused|happy|sad|worried) (.+)",
                r"That's (amazing|terrible|confusing|helpful|difficult) (.+)",
                r"I feel (.+) about (.+)"
            ]
        }
    
    def _setup_topic_keywords(self) -> Dict[str, List[str]]:
        """Setup topic classification keywords for Finnish learning focus"""
        return {
            'finnish_language': [
                'finnish', 'suomi', 'pronunciation', 'grammar', 'vocabulary',
                'tervetuloa', 'kiitos', 'hei', 'moi', 'sisu', 'sauna'
            ],
            'learning_methods': [
                'study', 'practice', 'learn', 'understand', 'remember',
                'flashcards', 'exercises', 'homework', 'repeat'
            ],
            'technology': [
                'computer', 'programming', 'data', 'python', 'code',
                'software', 'app', 'website', 'ai', 'algorithm'
            ],
            'health_fitness': [
                'exercise', 'running', 'gym', 'nutrition', 'diet',
                'training', 'workout', 'health', 'fitness'
            ],
            'family_personal': [
                'family', 'mother', 'father', 'child', 'home', 'personal',
                'private', 'relationship', 'friend', 'brother', 'sister'
            ],
            'school_work': [
                'school', 'work', 'job', 'teacher', 'homework', 'class',
                'meeting', 'project', 'assignment'
            ]
        }
    
    def extract_memories_from_conversation(self, user_message: str, character_response: str, 
                                         character_name: str, user_id: str) -> List[MemoryItem]:
        """Extract memories from a conversation turn"""
        memories = []
        
        # Extract from user message
        for memory_type, patterns in self.memory_extractors.items():
            for pattern in patterns:
                matches = re.finditer(pattern, user_message, re.IGNORECASE)
                for match in matches:
                    memory_content = self._clean_memory_content(match.group(0))
                    importance = self._calculate_importance(memory_type, memory_content, user_message)
                    topics = self._extract_topics(user_message)
                    emotional_context = self._detect_emotional_context(user_message)
                    
                    memory = MemoryItem(
                        character_name=character_name,
                        user_id=user_id,
                        memory_type=memory_type,
                        content=memory_content,
                        importance_score=importance,
                        topics=topics,
                        emotional_context=emotional_context
                    )
                    memories.append(memory)
        
        # Extract corrections and learning moments from character responses
        if "actually" in character_response.lower() or "correct" in character_response.lower():
            correction_memory = MemoryItem(
                character_name=character_name,
                user_id=user_id,
                memory_type="correction",
                content=f"Corrected user about: {user_message[:50]}...",
                importance_score=8,
                topics=self._extract_topics(user_message),
                emotional_context="learning"
            )
            memories.append(correction_memory)
        
        # Detect when user shows understanding
        if any(phrase in user_message.lower() for phrase in ['i understand', 'makes sense', 'i see', 'thank you']):
            understanding_memory = MemoryItem(
                character_name=character_name,
                user_id=user_id,
                memory_type="achievement", 
                content=f"User understood: {character_response[:50]}...",
                importance_score=7,
                topics=self._extract_topics(character_response),
                emotional_context="positive"
            )
            memories.append(understanding_memory)
        
        return memories
    
    def _clean_memory_content(self, content: str) -> str:
        """Clean and normalize memory content"""
        # Remove extra whitespace
        content = ' '.join(content.split())
        # Limit length
        if len(content) > 200:
            content = content[:200] + "..."
        return content
    
    def _calculate_importance(self, memory_type: str, content: str, context: str) -> int:
        """Calculate importance score for a memory"""
        base_scores = {
            'preferences': 6,
            'learning_style': 8,
            'facts': 7,
            'goals': 9,
            'emotional_context': 5,
            'correction': 9,
            'achievement': 8
        }
        
        score = base_scores.get(memory_type, 5)
        
        # Boost score for certain keywords
        high_value_keywords = ['goal', 'important', 'always', 'never', 'love', 'hate', 'struggling', 'confused']
        for keyword in high_value_keywords:
            if keyword in content.lower():
                score += 1
        
        # Boost for Finnish language learning context (your main focus)
        if any(word in content.lower() for word in ['finnish', 'suomi', 'language']):
            score += 1
        
        # Boost for family learning context
        if any(word in content.lower() for word in ['family', 'together', 'help']):
            score += 1
        
        # Reduce for very common phrases
        common_phrases = ['i think', 'maybe', 'probably', 'sometimes']
        for phrase in common_phrases:
            if phrase in content.lower():
                score -= 1
        
        return max(1, min(10, score))
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topic tags from text"""
        topics = []
        text_lower = text.lower()
        
        for topic, keywords in self.topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _detect_emotional_context(self, text: str) -> str:
        """Detect emotional context from text"""
        emotions = {
            'positive': ['happy', 'excited', 'love', 'great', 'amazing', 'wonderful', 'easy', 'fun'],
            'negative': ['sad', 'frustrated', 'hate', 'terrible', 'awful'],
            'difficulty': ['difficult', 'hard', 'confused', 'struggle', 'can\'t'],
            'learning': ['understand', 'learn', 'practice', 'study', 'remember'],
            'neutral': []
        }
        
        text_lower = text.lower()
        for emotion, keywords in emotions.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion
        
        return 'neutral'
    
    def build_character_context(self, character_name: str, user_id: str, 
                               current_topic: str = "") -> str:
        """Build comprehensive context from character memories"""
        memories = self.db.get_character_memories_optimized(character_name, user_id, 10)
        
        if not memories:
            return ""
        
        # Group memories by type
        memory_groups = defaultdict(list)
        for memory in memories:
            memory_groups[memory['type']].append(memory)
        
        context_parts = []
        
        # Build context based on memory types
        if memory_groups['facts']:
            facts = [m['content'] for m in memory_groups['facts'][:3]]
            context_parts.append(f"What I know about this user: {'; '.join(facts)}")
        
        if memory_groups['preferences']:
            prefs = [m['content'] for m in memory_groups['preferences'][:3]]
            context_parts.append(f"Their preferences: {'; '.join(prefs)}")
        
        if memory_groups['learning_style']:
            learning = [m['content'] for m in memory_groups['learning_style'][:2]]
            context_parts.append(f"Their learning style: {'; '.join(learning)}")
        
        if memory_groups['goals']:
            goals = [m['content'] for m in memory_groups['goals'][:2]]
            context_parts.append(f"Their goals: {'; '.join(goals)}")
        
        # Add topic-relevant memories if current topic is specified
        if current_topic:
            relevant_memories = [
                m for m in memories 
                if current_topic.lower() in m['content'].lower()
            ][:2]
            if relevant_memories:
                relevant_content = [m['content'] for m in relevant_memories]
                context_parts.append(f"Previous discussions about {current_topic}: {'; '.join(relevant_content)}")
        
        # Add recent corrections or difficulties
        if memory_groups['correction']:
            recent_corrections = [m['content'] for m in memory_groups['correction'][:2]]
            context_parts.append(f"Recent corrections: {'; '.join(recent_corrections)}")
        
        return "\n".join(context_parts)
    
    def get_personalized_prompt_additions(self, character_name: str, user_id: str, 
                                        current_topic: str = "") -> Dict[str, str]:
        """Get personalized additions to character prompts"""
        context = self.build_character_context(character_name, user_id, current_topic)
        
        # Character-specific personalizations for your characters
        personalizations = {
            'Aino': self._get_aino_personalization(context),
            'Mase': self._get_mase_personalization(context),
            'Anna': self._get_anna_personalization(context),
            'Bee': self._get_bee_personalization(context)
        }
        
        return personalizations.get(character_name, {'context': context})
    
    def _get_aino_personalization(self, context: str) -> Dict[str, str]:
        """Aino-specific personalization for Finnish learning"""
        additions = {
            'context': context,
            'style_note': "Remember their Finnish learning progress and adapt difficulty accordingly.",
            'cultural_note': "Reference previous cultural topics they found interesting.",
            'encouragement': "Use their name and encourage based on their learning goals."
        }
        return additions
    
    def _get_mase_personalization(self, context: str) -> Dict[str, str]:
        """Mase-specific personalization"""
        return {
            'context': context,
            'joke_style': "Reference their interests when making jokes.",
            'knowledge_level': "Adjust knowledge drops to their background and interests.",
            'brevity': "Keep it short but reference their previous questions."
        }
    
    def _get_anna_personalization(self, context: str) -> Dict[str, str]:
        """Anna-specific personalization"""
        return {
            'context': context,
            'advice_style': "Give advice relevant to their stated goals and family situation.",
            'wisdom_focus': "Draw on their expressed challenges and learning style.",
            'practical': "Reference their real-world applications for learning."
        }
    
    def _get_bee_personalization(self, context: str) -> Dict[str, str]:
        """Bee-specific personalization"""
        return {
            'context': context,
            'technical_level': "Match their technical background and interests.",
            'analytical_approach': "Use examples from domains they care about.",
            'data_focus': "Reference their learning patterns and progress data."
        }
    
    def generate_memory_summary(self, character_name: str, user_id: str) -> Dict[str, Any]:
        """Generate a summary of character memories about a user"""
        memories = self.db.get_character_memories_optimized(character_name, user_id, 50)
        
        if not memories:
            return {'total_memories': 0, 'summary': 'No memories yet'}
        
        # Analyze memory patterns
        memory_types = defaultdict(int)
        topics = defaultdict(int)
        emotional_patterns = defaultdict(int)
        
        for memory in memories:
            memory_types[memory['type']] += 1
            
            # Simple topic extraction for summary
            content = memory['content'].lower()
            if 'finnish' in content:
                topics['Finnish Learning'] += 1
            if 'family' in content:
                topics['Family'] += 1
            if 'goal' in content:
                topics['Goals'] += 1
            if 'difficult' in content or 'confused' in content:
                emotional_patterns['difficulty'] += 1
            if 'enjoy' in content or 'love' in content:
                emotional_patterns['positive'] += 1
        
        return {
            'total_memories': len(memories),
            'memory_types': dict(memory_types),
            'common_topics': dict(topics),
            'emotional_patterns': dict(emotional_patterns),
            'relationship_strength': min(len(memories) // 5, 10),  # 1-10 scale
            'personality_understanding': self._calculate_personality_understanding(memories),
            'learning_focus': self._identify_learning_focus(memories)
        }
    
    def _calculate_personality_understanding(self, memories: List[Dict]) -> int:
        """Calculate how well the character understands the user's personality"""
        unique_types = set(m['type'] for m in memories)
        high_importance_memories = [m for m in memories if m['importance'] >= 8]
        
        score = len(unique_types) * 2 + len(high_importance_memories)
        return min(score, 10)
    
    def _identify_learning_focus(self, memories: List[Dict]) -> str:
        """Identify the user's primary learning focus"""
        finnish_count = sum(1 for m in memories if 'finnish' in m['content'].lower())
        total_memories = len(memories)
        
        if finnish_count > total_memories * 0.4:
            return "Finnish Language Focus"
        elif finnish_count > 0:
            return "Mixed Learning with Finnish"
        else:
            return "General Learning"
    
    def get_conversation_insights(self, character_name: str, user_id: str) -> Dict[str, Any]:
        """Get insights for improving conversations"""
        memories = self.db.get_character_memories_optimized(character_name, user_id, 20)
        
        insights = {
            'suggested_topics': self._suggest_next_topics(memories),
            'learning_gaps': self._identify_learning_gaps(memories),
            'engagement_level': self._assess_engagement(memories),
            'next_steps': self._suggest_next_steps(memories)
        }
        
        return insights
    
    def _suggest_next_topics(self, memories: List[Dict]) -> List[str]:
        """Suggest topics based on user's interests and progress"""
        suggestions = []
        
        # Check what they've been interested in
        finnish_memories = [m for m in memories if 'finnish' in m['content'].lower()]
        if finnish_memories:
            suggestions.append("Advanced Finnish pronunciation")
            suggestions.append("Finnish cultural traditions")
        
        # Check for goals
        goal_memories = [m for m in memories if m['type'] == 'goals']
        if goal_memories:
            suggestions.append("Progress toward your learning goals")
        
        # Default suggestions for new users
        if not suggestions:
            suggestions = ["Finnish basics", "Learning preferences", "Family learning goals"]
        
        return suggestions[:3]
    
    def _identify_learning_gaps(self, memories: List[Dict]) -> List[str]:
        """Identify potential learning gaps"""
        gaps = []
        
        # Check for repeated confusion
        confusion_memories = [m for m in memories if 'confused' in m['content'].lower() or m['type'] == 'correction']
        if len(confusion_memories) > 2:
            gaps.append("Review fundamental concepts")
        
        # Check for missing practice areas
        finnish_memories = [m for m in memories if 'finnish' in m['content'].lower()]
        if finnish_memories:
            has_pronunciation = any('pronunciation' in m['content'].lower() for m in finnish_memories)
            has_vocabulary = any('vocabulary' in m['content'].lower() for m in finnish_memories)
            
            if not has_pronunciation:
                gaps.append("Finnish pronunciation practice needed")
            if not has_vocabulary:
                gaps.append("Vocabulary building opportunities")
        
        return gaps[:3]
    
    def _assess_engagement(self, memories: List[Dict]) -> str:
        """Assess user engagement level"""
        if len(memories) < 3:
            return "Getting started"
        elif len(memories) < 10:
            return "Building engagement"
        elif len(memories) < 20:
            return "Actively engaged"
        else:
            return "Highly engaged learner"
    
    def _suggest_next_steps(self, memories: List[Dict]) -> List[str]:
        """Suggest next steps for learning"""
        steps = []
        
        # Based on recent activity
        recent_memories = memories[:5]  # Most recent
        
        if any(m['type'] == 'goals' for m in recent_memories):
            steps.append("Continue working toward your stated goals")
        
        if any('finnish' in m['content'].lower() for m in recent_memories):
            steps.append("Practice Finnish conversation with daily scenarios")
        
        # Default suggestions
        if not steps:
            steps = [
                "Set specific learning goals",
                "Practice with real-world examples",
                "Build on your interests"
            ]
        
        return steps[:3]

# Utility functions for integration
def integrate_with_existing_database(db):
    """Add enhanced memory methods to existing database"""
    
    # Add enhanced memory storage method
    def store_enhanced_memory(memory_item: MemoryItem):
        """Store enhanced memory item using existing database structure"""
        db.store_character_memory(
            memory_item.character_name,
            memory_item.user_id,
            memory_item.memory_type,
            memory_item.content,
            memory_item.importance_score
        )
    
    # Add the method to the database instance
    db.store_enhanced_memory = store_enhanced_memory
    
    return db
