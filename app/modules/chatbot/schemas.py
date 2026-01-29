"""Chatbot module schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """Message type enum."""
    TEXT = "text"
    QUESTION = "question"
    BUTTON = "button"


class Button(BaseModel):
    """Button in chatbot message."""
    label: str = Field(..., description="Button label")
    value: str = Field(..., description="Button value")


class ChatbotMessage(BaseModel):
    """Chatbot message."""
    type: MessageType = Field(default=MessageType.TEXT, description="Message type")
    text: str = Field(..., description="Message text")
    buttons: Optional[List[Button]] = Field(default=None, description="Buttons")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "text",
                "text": "How can I help you today?",
                "buttons": [
                    {"label": "Guitar Selection", "value": "guitar_selection"},
                    {"label": "FAQs", "value": "faqs"},
                ],
            }
        }


class ChatRequest(BaseModel):
    """Chat request."""
    message: str = Field(..., min_length=1, description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for context")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "I'm a beginner guitarist, what should I buy?",
                "conversation_id": "conv_123",
            }
        }


class ChatResponse(BaseModel):
    """Chat response."""
    conversation_id: str = Field(..., description="Conversation ID")
    user_message: str = Field(..., description="User message")
    bot_response: ChatbotMessage = Field(..., description="Bot response")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    intent: str = Field(..., description="Detected intent")
    timestamp: datetime = Field(..., description="Response timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123",
                "user_message": "I'm a beginner guitarist",
                "bot_response": {
                    "type": "text",
                    "text": "Great! I can help you choose the right guitar. Let me ask you a few questions...",
                    "buttons": [
                        {"label": "Budget under ₹10K", "value": "budget_10k"},
                        {"label": "Budget ₹10K - ₹25K", "value": "budget_25k"},
                    ],
                },
                "confidence": 0.95,
                "intent": "guitar_selection",
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


class FAQItem(BaseModel):
    """FAQ item."""
    question: str = Field(..., description="Question")
    answer: str = Field(..., description="Answer")
    category: str = Field(..., description="FAQ category")
    keywords: List[str] = Field(..., description="Keywords for matching")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What's the difference between acoustic and electric guitars?",
                "answer": "Acoustic guitars are louder and don't need amplification, while electric guitars require an amplifier...",
                "category": "beginner_guide",
                "keywords": ["acoustic", "electric", "difference"],
            }
        }


class ConversationContext(BaseModel):
    """Conversation context."""
    conversation_id: str = Field(..., description="Conversation ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    messages: List[dict] = Field(..., description="Message history")
    intent_history: List[str] = Field(..., description="Intent history")
    created_at: datetime = Field(..., description="Created at")
    last_message_at: datetime = Field(..., description="Last message at")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123",
                "user_id": "user_456",
                "messages": [
                    {"role": "user", "text": "I need help"},
                    {"role": "bot", "text": "Sure, what do you need help with?"},
                ],
                "intent_history": ["greeting", "help_request"],
                "created_at": "2024-01-15T10:00:00Z",
                "last_message_at": "2024-01-15T10:30:00Z",
            }
        }
