"""Chatbot module service."""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from app.modules.chatbot.repository import ChatbotRepository
import logging
import re

logger = logging.getLogger(__name__)


class ChatbotService:
    """Chatbot service for rule-based conversation and NLU."""

    def __init__(self, repository: ChatbotRepository):
        """Initialize service."""
        self.repository = repository
        self.intent_patterns = {}
        self.faqs = {}

    async def init_knowledge_base(self):
        """Initialize chatbot knowledge base from database."""
        try:
            # Load intents
            intents = await self.repository.get_all_intents()
            for intent in intents:
                intent_name = intent.get("intent_name")
                self.intent_patterns[intent_name] = {
                    "patterns": intent.get("patterns", []),
                    "responses": intent.get("responses", []),
                }
            
            # Load FAQs
            faqs = await self.repository.get_all_faqs()
            for faq in faqs:
                category = faq.get("category")
                if category not in self.faqs:
                    self.faqs[category] = []
                self.faqs[category].append(faq)
            
            logger.info(f"Loaded {len(self.intent_patterns)} intents and {len(self.faqs)} FAQ categories")
        except Exception as e:
            logger.error(f"Error initializing knowledge base: {str(e)}")

    async def create_conversation(
        self, user_id: Optional[str] = None
    ) -> str:
        """Create new conversation."""
        try:
            conversation_id = await self.repository.create_conversation(user_id)
            return conversation_id
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise

    async def process_message(
        self,
        conversation_id: str,
        user_message: str,
    ) -> Tuple[str, float, str]:
        """Process user message and return bot response.
        
        Returns: (bot_response, confidence, intent)
        """
        try:
            # Detect intent
            intent, confidence = await self._detect_intent(user_message)
            
            # Get bot response based on intent
            bot_response = await self._generate_response(intent, user_message, confidence)
            
            # Store messages in conversation
            await self.repository.add_message(
                conversation_id, "user", user_message, intent
            )
            await self.repository.add_message(
                conversation_id, "bot", bot_response["text"]
            )
            
            return bot_response, confidence, intent
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

    async def _detect_intent(self, user_message: str) -> Tuple[str, float]:
        """Detect intent from user message using pattern matching."""
        try:
            user_message_lower = user_message.lower()
            best_match_intent = "default"
            best_confidence = 0.0
            
            # Check against defined intents
            for intent_name, intent_data in self.intent_patterns.items():
                patterns = intent_data.get("patterns", [])
                
                for pattern in patterns:
                    # Simple keyword matching (can be enhanced with regex)
                    pattern_lower = pattern.lower()
                    
                    # Exact match
                    if pattern_lower == user_message_lower:
                        return intent_name, 1.0
                    
                    # Substring match
                    if pattern_lower in user_message_lower:
                        confidence = 0.9
                        if confidence > best_confidence:
                            best_match_intent = intent_name
                            best_confidence = confidence
                    
                    # Word match (any word from pattern)
                    pattern_words = pattern_lower.split()
                    message_words = user_message_lower.split()
                    matches = sum(1 for w in pattern_words if w in message_words)
                    
                    if matches > 0:
                        confidence = min(0.8, matches / len(pattern_words))
                        if confidence > best_confidence:
                            best_match_intent = intent_name
                            best_confidence = confidence
            
            # Default intent if no match
            if best_confidence == 0.0:
                best_match_intent = "default"
                best_confidence = 0.5
            
            return best_match_intent, best_confidence
        except Exception as e:
            logger.error(f"Error detecting intent: {str(e)}")
            return "default", 0.5

    async def _generate_response(
        self,
        intent: str,
        user_message: str,
        confidence: float,
    ) -> Dict[str, Any]:
        """Generate response based on detected intent."""
        try:
            response_text = ""
            buttons = None
            
            # Get response from intent patterns
            if intent in self.intent_patterns:
                responses = self.intent_patterns[intent].get("responses", [])
                if responses:
                    response_text = responses[0]  # Use first response
                    
                    # Add buttons for specific intents
                    if intent == "guitar_selection":
                        buttons = [
                            {"label": "Beginner", "value": "beginner"},
                            {"label": "Intermediate", "value": "intermediate"},
                            {"label": "Advanced", "value": "advanced"},
                        ]
                    elif intent == "help_products":
                        buttons = [
                            {"label": "Browse Products", "value": "browse"},
                            {"label": "Search", "value": "search"},
                        ]
            
            # Fall back to FAQ search if no intent match
            if not response_text:
                faqs = await self.repository.search_faqs(user_message)
                if faqs:
                    faq = faqs[0]  # Use best match
                    response_text = faq.get("answer", "I'm not sure how to help with that.")
                else:
                    response_text = "I'm not sure about that. Can you try rephrasing your question or ask about guitar selection, product information, or FAQs?"
            
            return {
                "type": "text",
                "text": response_text,
                "buttons": buttons,
            }
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "type": "text",
                "text": "Sorry, I encountered an error. Please try again.",
            }

    async def create_faq(
        self,
        question: str,
        answer: str,
        category: str,
        keywords: List[str],
    ) -> str:
        """Create FAQ."""
        try:
            faq_data = {
                "question": question,
                "answer": answer,
                "category": category,
                "keywords": keywords,
                "created_at": datetime.utcnow(),
            }
            return await self.repository.create_faq(faq_data)
        except Exception as e:
            logger.error(f"Error creating FAQ: {str(e)}")
            raise

    async def get_all_faqs(self) -> List[Dict[str, Any]]:
        """Get all FAQs."""
        try:
            return await self.repository.get_all_faqs()
        except Exception as e:
            logger.error(f"Error getting FAQs: {str(e)}")
            return []

    async def get_faqs_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get FAQs by category."""
        try:
            return await self.repository.get_faqs_by_category(category)
        except Exception as e:
            logger.error(f"Error getting FAQs: {str(e)}")
            return []

    async def search_faqs(self, query: str) -> List[Dict[str, Any]]:
        """Search FAQs."""
        try:
            return await self.repository.search_faqs(query)
        except Exception as e:
            logger.error(f"Error searching FAQs: {str(e)}")
            return []

    async def create_intent(
        self,
        intent_name: str,
        patterns: List[str],
        responses: List[str],
    ) -> str:
        """Create intent pattern."""
        try:
            intent_data = {
                "intent_name": intent_name,
                "patterns": patterns,
                "responses": responses,
                "created_at": datetime.utcnow(),
            }
            intent_id = await self.repository.create_intent(intent_data)
            
            # Update in-memory patterns
            self.intent_patterns[intent_name] = {
                "patterns": patterns,
                "responses": responses,
            }
            
            return intent_id
        except Exception as e:
            logger.error(f"Error creating intent: {str(e)}")
            raise

    async def get_conversation_history(
        self, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Get conversation history."""
        try:
            return await self.repository.get_message_history(conversation_id)
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

    async def get_user_conversations(
        self, user_id: str
    ) -> List[Dict[str, Any]]:
        """Get user's conversations."""
        try:
            return await self.repository.get_user_conversations(user_id)
        except Exception as e:
            logger.error(f"Error getting user conversations: {str(e)}")
            return []

    async def initialize_default_intents(self):
        """Initialize default intents and FAQs."""
        try:
            # Check if already initialized
            existing_intents = await self.repository.get_all_intents()
            if existing_intents:
                logger.info("Intents already initialized")
                return
            
            # Create default intents
            default_intents = [
                {
                    "intent_name": "greeting",
                    "patterns": ["hello", "hi", "hey", "greetings", "what's up"],
                    "responses": ["Hello! Welcome to Jimi Music. How can I help you today?"],
                },
                {
                    "intent_name": "guitar_selection",
                    "patterns": [
                        "guitar recommendation",
                        "which guitar should i buy",
                        "beginner guitar",
                        "best guitar for me",
                        "help me choose a guitar",
                    ],
                    "responses": [
                        "I'd be happy to help you choose a guitar! Let me ask you a few questions...",
                    ],
                },
                {
                    "intent_name": "help_products",
                    "patterns": [
                        "show products",
                        "what products",
                        "browse guitars",
                        "product information",
                        "tell me about products",
                    ],
                    "responses": [
                        "We have a wide range of guitars and music instruments. You can browse our products to see the full catalog.",
                    ],
                },
                {
                    "intent_name": "pricing",
                    "patterns": [
                        "price",
                        "cost",
                        "how much",
                        "affordable",
                        "budget",
                    ],
                    "responses": [
                        "We have guitars for all budgets! Our prices range from beginner-friendly options to professional instruments.",
                    ],
                },
                {
                    "intent_name": "delivery",
                    "patterns": [
                        "shipping",
                        "delivery",
                        "how long",
                        "when will i get",
                        "delivery time",
                    ],
                    "responses": [
                        "We offer fast delivery based on your location. Delivery is calculated based on distance from our warehouse.",
                    ],
                },
                {
                    "intent_name": "default",
                    "patterns": [],
                    "responses": [
                        "I'm not sure about that. Can you try rephrasing or asking about our products, prices, or delivery?",
                    ],
                },
            ]
            
            for intent in default_intents:
                await self.repository.create_intent(intent)
            
            # Create default FAQs
            default_faqs = [
                {
                    "question": "What's the difference between acoustic and electric guitars?",
                    "answer": "Acoustic guitars produce sound naturally through their hollow body and don't need electricity. Electric guitars require an amplifier to be heard but offer more versatility in sound.",
                    "category": "beginner_guide",
                    "keywords": ["acoustic", "electric", "difference"],
                },
                {
                    "question": "How do I know what size guitar to buy?",
                    "answer": "Guitar sizes are typically 1/4, 1/2, 3/4, and full-size (4/4). Children usually start with smaller sizes, while adults typically use full-size. Visit us to try different sizes.",
                    "category": "beginner_guide",
                    "keywords": ["size", "fit", "choose"],
                },
                {
                    "question": "Do you offer warranties on guitars?",
                    "answer": "Yes, most of our guitars come with manufacturer warranties ranging from 1 to 5 years depending on the model.",
                    "category": "faq",
                    "keywords": ["warranty", "guarantee", "protection"],
                },
                {
                    "question": "Can you help with guitar lessons?",
                    "answer": "We occasionally post guitar tips on our social media. For professional lessons, we can recommend local instructors in your area.",
                    "category": "services",
                    "keywords": ["lessons", "tutorial", "learning"],
                },
            ]
            
            for faq in default_faqs:
                await self.repository.create_faq(faq["question"], faq["answer"], faq["category"], faq["keywords"])
            
            logger.info(f"Initialized {len(default_intents)} intents and {len(default_faqs)} FAQs")
        except Exception as e:
            logger.error(f"Error initializing default intents: {str(e)}")
