"""Chatbot module repository."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import uuid

logger = logging.getLogger(__name__)


class ChatbotRepository:
    """Chatbot repository for database operations."""

    def __init__(self, mongo_db: AsyncIOMotorDatabase):
        """Initialize repository."""
        self.mongo_db = mongo_db

    async def init_indexes(self):
        """Initialize MongoDB indexes."""
        try:
            conversations_col = self.mongo_db["chatbot_conversations"]
            faqs_col = self.mongo_db["chatbot_faqs"]
            intents_col = self.mongo_db["chatbot_intents"]
            
            # Conversations indexes
            await conversations_col.create_index("conversation_id", unique=True)
            await conversations_col.create_index("user_id")
            await conversations_col.create_index("created_at")
            
            # FAQs indexes
            await faqs_col.create_index("category")
            await faqs_col.create_index([("keywords", "text"), ("question", "text"), ("answer", "text")])
            
            # Intents index
            await intents_col.create_index("intent_name", unique=True)
            
            logger.info("Chatbot indexes initialized")
        except Exception as e:
            logger.error(f"Error initializing chatbot indexes: {str(e)}")

    async def create_conversation(
        self, user_id: Optional[str] = None
    ) -> str:
        """Create new conversation."""
        try:
            conversations_col = self.mongo_db["chatbot_conversations"]
            conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
            
            await conversations_col.insert_one({
                "conversation_id": conversation_id,
                "user_id": user_id,
                "messages": [],
                "intent_history": [],
                "created_at": datetime.utcnow(),
                "last_message_at": datetime.utcnow(),
            })
            
            return conversation_id
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise

    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        try:
            conversations_col = self.mongo_db["chatbot_conversations"]
            return await conversations_col.find_one({"conversation_id": conversation_id})
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return None

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        text: str,
        intent: Optional[str] = None,
    ) -> bool:
        """Add message to conversation."""
        try:
            conversations_col = self.mongo_db["chatbot_conversations"]
            
            message = {
                "role": role,
                "text": text,
                "timestamp": datetime.utcnow(),
            }
            
            update_data = {
                "$push": {"messages": message},
                "$set": {"last_message_at": datetime.utcnow()},
            }
            
            if intent:
                update_data["$push"]["intent_history"] = intent
            
            result = await conversations_col.update_one(
                {"conversation_id": conversation_id},
                update_data,
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            return False

    async def get_message_history(
        self, conversation_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get message history."""
        try:
            conversations_col = self.mongo_db["chatbot_conversations"]
            conversation = await conversations_col.find_one(
                {"conversation_id": conversation_id}
            )
            
            if not conversation:
                return []
            
            messages = conversation.get("messages", [])
            return messages[-limit:]  # Return last N messages
        except Exception as e:
            logger.error(f"Error getting message history: {str(e)}")
            return []

    async def create_faq(self, faq_data: Dict[str, Any]) -> str:
        """Create FAQ."""
        try:
            faqs_col = self.mongo_db["chatbot_faqs"]
            result = await faqs_col.insert_one(faq_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating FAQ: {str(e)}")
            raise

    async def get_all_faqs(self) -> List[Dict[str, Any]]:
        """Get all FAQs."""
        try:
            faqs_col = self.mongo_db["chatbot_faqs"]
            faqs = []
            async for faq in faqs_col.find():
                faq["id"] = str(faq.get("_id"))
                faqs.append(faq)
            return faqs
        except Exception as e:
            logger.error(f"Error getting FAQs: {str(e)}")
            return []

    async def get_faqs_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get FAQs by category."""
        try:
            faqs_col = self.mongo_db["chatbot_faqs"]
            faqs = []
            async for faq in faqs_col.find({"category": category}):
                faq["id"] = str(faq.get("_id"))
                faqs.append(faq)
            return faqs
        except Exception as e:
            logger.error(f"Error getting FAQs by category: {str(e)}")
            return []

    async def search_faqs(self, query: str) -> List[Dict[str, Any]]:
        """Search FAQs using text search."""
        try:
            faqs_col = self.mongo_db["chatbot_faqs"]
            faqs = []
            async for faq in faqs_col.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]):
                faq["id"] = str(faq.get("_id"))
                faqs.append(faq)
            return faqs
        except Exception as e:
            logger.error(f"Error searching FAQs: {str(e)}")
            return []

    async def create_intent(self, intent_data: Dict[str, Any]) -> str:
        """Create intent pattern."""
        try:
            intents_col = self.mongo_db["chatbot_intents"]
            result = await intents_col.insert_one(intent_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating intent: {str(e)}")
            raise

    async def get_all_intents(self) -> List[Dict[str, Any]]:
        """Get all intents."""
        try:
            intents_col = self.mongo_db["chatbot_intents"]
            intents = []
            async for intent in intents_col.find():
                intent["id"] = str(intent.get("_id"))
                intents.append(intent)
            return intents
        except Exception as e:
            logger.error(f"Error getting intents: {str(e)}")
            return []

    async def get_intent_by_name(self, intent_name: str) -> Optional[Dict[str, Any]]:
        """Get intent by name."""
        try:
            intents_col = self.mongo_db["chatbot_intents"]
            return await intents_col.find_one({"intent_name": intent_name})
        except Exception as e:
            logger.error(f"Error getting intent: {str(e)}")
            return None

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation (for cleanup after timeout)."""
        try:
            conversations_col = self.mongo_db["chatbot_conversations"]
            result = await conversations_col.delete_one({
                "conversation_id": conversation_id
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            return False

    async def get_user_conversations(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user's conversation history."""
        try:
            conversations_col = self.mongo_db["chatbot_conversations"]
            conversations = []
            async for conv in conversations_col.find(
                {"user_id": user_id}
            ).sort("last_message_at", -1).limit(limit):
                conv["id"] = str(conv.get("_id"))
                conversations.append(conv)
            return conversations
        except Exception as e:
            logger.error(f"Error getting user conversations: {str(e)}")
            return []
