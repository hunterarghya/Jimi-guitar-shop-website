"""Chatbot module router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
import uuid

from app.core import get_mongo_db
from app.core.security import get_current_user
from app.modules.chatbot.schemas import (
    ChatRequest,
    ChatResponse,
    ChatbotMessage,
    FAQItem,
)
from app.modules.chatbot.service import ChatbotService
from app.modules.chatbot.repository import ChatbotRepository
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chatbot", tags=["chatbot"])

# Global service instance (initialized on startup)
chatbot_service: ChatbotService = None


async def get_chatbot_service(
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> ChatbotService:
    """Get chatbot service."""
    global chatbot_service
    if chatbot_service is None:
        repository = ChatbotRepository(mongo_db)
        chatbot_service = ChatbotService(repository)
        await chatbot_service.init_knowledge_base()
    return chatbot_service


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatbotService = Depends(get_chatbot_service),
    current_user: dict = Depends(get_current_user),
):
    """Chat with the Jimi assistant.
    
    Features:
    - Multi-turn conversation with context
    - Intent detection (guitar selection, products, pricing, delivery, etc.)
    - FAQ search capability
    - Button-based interactions for guided flows
    - Conversation history tracking
    
    Parameters:
    - message: User message
    - conversation_id: Optional conversation ID for context (creates new if not provided)
    
    Returns:
    - conversation_id: Conversation ID for context
    - user_message: Echo of user message
    - bot_response: Bot response with optional buttons
    - confidence: Intent detection confidence (0-1)
    - intent: Detected intent
    - timestamp: Response timestamp
    """
    try:
        # Get or create conversation
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = await service.create_conversation(
                user_id=current_user.get("sub")
            )
        
        # Process message
        bot_response, confidence, intent = await service.process_message(
            conversation_id, request.message
        )
        
        return ChatResponse(
            conversation_id=conversation_id,
            user_message=request.message,
            bot_response=ChatbotMessage(**bot_response),
            confidence=confidence,
            intent=intent,
            timestamp=__import__('datetime').datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.post("/start")
async def start_conversation(
    service: ChatbotService = Depends(get_chatbot_service),
    current_user: dict = Depends(get_current_user),
):
    """Start a new conversation.
    
    Returns:
    - conversation_id: New conversation ID
    - initial_message: Welcome message
    """
    try:
        conversation_id = await service.create_conversation(
            user_id=current_user.get("sub")
        )
        
        return {
            "conversation_id": conversation_id,
            "initial_message": {
                "type": "text",
                "text": "Hello! Welcome to Jimi Music. How can I help you today?",
                "buttons": [
                    {"label": "Guitar Selection", "value": "guitar_selection"},
                    {"label": "Browse Products", "value": "products"},
                    {"label": "FAQs", "value": "faqs"},
                ],
            },
        }
    except Exception as e:
        logger.error(f"Error starting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start conversation")


@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: str,
    service: ChatbotService = Depends(get_chatbot_service),
    current_user: dict = Depends(get_current_user),
):
    """Get conversation history.
    
    Parameters:
    - conversation_id: Conversation ID
    
    Returns:
    - List of messages with role (user/bot) and text
    """
    try:
        history = await service.get_conversation_history(conversation_id)
        return {
            "conversation_id": conversation_id,
            "messages": history,
        }
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get history")


@router.get("/my-conversations")
async def get_my_conversations(
    service: ChatbotService = Depends(get_chatbot_service),
    current_user: dict = Depends(get_current_user),
):
    """Get user's conversation history.
    
    Returns:
    - List of recent conversations with last message timestamp
    """
    try:
        conversations = await service.get_user_conversations(
            current_user.get("sub")
        )
        return {
            "user_id": current_user.get("sub"),
            "conversations": conversations,
        }
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get conversations")


# FAQ endpoints

@router.get("/faqs", response_model=List[FAQItem])
async def get_faqs(
    category: str = Query(None, description="Filter by category"),
    service: ChatbotService = Depends(get_chatbot_service),
):
    """Get FAQs.
    
    Parameters:
    - category: Optional category filter (beginner_guide, faq, services, etc.)
    
    Returns:
    - List of FAQs
    """
    try:
        if category:
            faqs = await service.get_faqs_by_category(category)
        else:
            faqs = await service.get_all_faqs()
        
        return [FAQItem(**faq) for faq in faqs]
    except Exception as e:
        logger.error(f"Error getting FAQs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get FAQs")


@router.get("/faqs/search")
async def search_faqs(
    query: str = Query(..., min_length=3, description="Search query"),
    service: ChatbotService = Depends(get_chatbot_service),
):
    """Search FAQs.
    
    Parameters:
    - query: Search query (min 3 characters)
    
    Returns:
    - Matching FAQs sorted by relevance
    """
    try:
        faqs = await service.search_faqs(query)
        return {
            "query": query,
            "results": [FAQItem(**faq) for faq in faqs],
            "count": len(faqs),
        }
    except Exception as e:
        logger.error(f"Error searching FAQs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search FAQs")


@router.post("/faqs", response_model=FAQItem)
async def create_faq(
    question: str,
    answer: str,
    category: str,
    keywords: List[str],
    service: ChatbotService = Depends(get_chatbot_service),
    current_user: dict = Depends(get_current_user),
):
    """Create FAQ (admin only).
    
    Requires: Admin role
    """
    try:
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=403,
                detail="Only admins can create FAQs",
            )
        
        faq_id = await service.create_faq(question, answer, category, keywords)
        
        return FAQItem(
            question=question,
            answer=answer,
            category=category,
            keywords=keywords,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating FAQ: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create FAQ")


# Intent management endpoints (admin)

@router.post("/intents")
async def create_intent(
    intent_name: str,
    patterns: List[str],
    responses: List[str],
    service: ChatbotService = Depends(get_chatbot_service),
    current_user: dict = Depends(get_current_user),
):
    """Create chatbot intent (admin only).
    
    Parameters:
    - intent_name: Unique intent name
    - patterns: List of user message patterns to match
    - responses: List of possible bot responses
    
    Requires: Admin role
    """
    try:
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=403,
                detail="Only admins can create intents",
            )
        
        intent_id = await service.create_intent(intent_name, patterns, responses)
        
        return {
            "intent_id": intent_id,
            "intent_name": intent_name,
            "patterns": patterns,
            "responses": responses,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating intent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create intent")


@router.get("/health")
async def chatbot_health():
    """Chatbot health check."""
    return {
        "status": "healthy",
        "service": "chatbot",
        "message": "Chatbot service is running",
    }
