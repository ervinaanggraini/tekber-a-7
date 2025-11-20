from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ..core.schemas import PersistentDeletion, TimestampSchema, UUIDSchema
from ..models.chatbot import ConversationStatus, MessageRole


class ChatMessageBase(BaseModel):
    """Base schema untuk chat message"""
    role: Annotated[MessageRole, Field(examples=[MessageRole.USER, MessageRole.ASSISTANT])]
    content: Annotated[
        str, 
        Field(
            min_length=1, 
            max_length=50000,
            examples=["Halo, bagaimana cara mengatur keuangan yang baik?", "Saya ingin membuat budget bulanan"],
            description="Isi pesan chat"
        )
    ]


class ChatMessage(TimestampSchema, ChatMessageBase, UUIDSchema):
    """Full chat message model untuk internal use"""
    conversation_id: int
    model_name: str | None = None
    token_count: int | None = None
    cost: float | None = None
    response_time: float | None = None


class ChatMessageRead(BaseModel):
    """Schema untuk response chat message"""
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    model_name: str | None
    token_count: int | None
    cost: float | None
    response_time: float | None
    created_at: datetime


class ChatMessageCreate(BaseModel):
    """Schema untuk membuat message baru"""
    model_config = ConfigDict(extra="forbid")
    
    content: Annotated[
        str, 
        Field(
            min_length=1, 
            max_length=50000,
            examples=["Bagaimana cara menabung yang efektif?"],
            description="Pesan yang ingin dikirim ke AI"
        )
    ]


class ChatMessageCreateInternal(ChatMessageBase):
    """Schema internal untuk create message"""
    conversation_id: int


# === Conversation Schemas ===

class ChatConversationBase(BaseModel):
    """Base schema untuk conversation"""
    title: Annotated[
        str,
        Field(
            min_length=1,
            max_length=200,
            examples=["Financial Planning Discussion", "Budget Questions", "Investment Advice"],
            description="Judul conversation"
        )
    ]


class ChatConversation(TimestampSchema, ChatConversationBase, UUIDSchema, PersistentDeletion):
    """Full conversation model untuk internal use"""
    user_id: int
    status: ConversationStatus = ConversationStatus.ACTIVE
    model_name: str = "anthropic/claude-3.5-sonnet"
    system_prompt: str | None = None
    total_messages: int = 0


class ChatConversationRead(BaseModel):
    """Schema untuk response conversation"""
    id: int
    user_id: int
    title: str
    status: ConversationStatus
    model_name: str
    system_prompt: str | None
    total_messages: int
    created_at: datetime
    updated_at: datetime | None


class ChatConversationCreate(BaseModel):
    """Schema untuk membuat conversation baru"""
    model_config = ConfigDict(extra="forbid")
    
    title: Annotated[
        str | None,
        Field(
            min_length=1,
            max_length=200,
            default=None,
            examples=["Diskusi Perencanaan Keuangan"],
            description="Judul conversation (auto-generated jika kosong)"
        )
    ] = None
    model_name: Annotated[
        str,
        Field(
            default="anthropic/claude-3.5-sonnet",
            examples=[
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4-turbo",
                "google/gemini-pro",
                "mistralai/mixtral-8x7b-instruct"
            ],
            description="Model AI yang akan digunakan"
        )
    ] = "anthropic/claude-3.5-sonnet"
    system_prompt: Annotated[
        str | None,
        Field(
            max_length=2000,
            default=None,
            examples=[
                "You are a helpful financial advisor assistant. Provide practical and actionable advice.",
                "You are an expert in personal finance. Help users with budgeting, saving, and investment questions."
            ],
            description="System prompt untuk mengatur behavior AI (optional)"
        )
    ] = None


class ChatConversationCreateInternal(ChatConversationBase):
    """Schema internal untuk create conversation"""
    user_id: int
    model_name: str = "anthropic/claude-3.5-sonnet"
    system_prompt: str | None = None


class ChatConversationUpdate(BaseModel):
    """Schema untuk update conversation"""
    model_config = ConfigDict(extra="forbid")
    
    title: Annotated[str | None, Field(min_length=1, max_length=200, default=None)] = None
    status: Annotated[ConversationStatus | None, Field(default=None)] = None
    system_prompt: Annotated[str | None, Field(max_length=2000, default=None)] = None


# === Chat Request/Response Schemas ===

class ChatRequest(BaseModel):
    """Schema untuk chat request"""
    model_config = ConfigDict(extra="forbid")
    
    message: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50000,
            examples=["Bagaimana cara membuat budget bulanan yang efektif?"],
            description="Pesan yang ingin dikirim"
        )
    ]
    conversation_id: Annotated[
        int | None,
        Field(
            default=None,
            examples=[123],
            description="ID conversation yang sudah ada (buat baru jika None)"
        )
    ] = None
    model_name: Annotated[
        str,
        Field(
            default="anthropic/claude-3.5-sonnet",
            examples=[
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4-turbo",
                "google/gemini-pro"
            ],
            description="Model AI yang akan digunakan"
        )
    ] = "anthropic/claude-3.5-sonnet"
    system_prompt: Annotated[
        str | None,
        Field(
            max_length=2000,
            default=None,
            description="System prompt (hanya untuk conversation baru)"
        )
    ] = None


class ChatResponse(BaseModel):
    """Schema untuk chat response"""
    conversation_id: int
    user_message: ChatMessageRead
    assistant_message: ChatMessageRead
    conversation_title: str
    total_messages: int
    model_used: str
    response_time: float
    estimated_cost: float | None


class ConversationDetail(BaseModel):
    """Schema untuk detail conversation dengan messages"""
    conversation: ChatConversationRead
    messages: list[ChatMessageRead]


class ChatStats(BaseModel):
    """Schema untuk statistik chat user"""
    total_conversations: Annotated[int, Field(examples=[25], description="Total conversations")]
    active_conversations: Annotated[int, Field(examples=[15], description="Active conversations")]
    total_messages: Annotated[int, Field(examples=[487], description="Total messages sent")]
    total_ai_responses: Annotated[int, Field(examples=[478], description="Total AI responses")]
    total_tokens_used: Annotated[int, Field(examples=[125000], description="Total tokens used")]
    estimated_total_cost: Annotated[float, Field(examples=[12.50], description="Total estimated cost in USD")]
    favorite_model: Annotated[str, Field(examples=["anthropic/claude-3.5-sonnet"], description="Most used model")]


class AvailableModels(BaseModel):
    """Schema untuk daftar model yang tersedia"""
    models: list[dict[str, str | float]]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "models": [
                    {
                        "id": "anthropic/claude-3.5-sonnet",
                        "name": "Claude 3.5 Sonnet",
                        "description": "Most intelligent model, best for complex reasoning",
                        "input_cost": 0.003,
                        "output_cost": 0.015,
                        "context_length": 200000
                    },
                    {
                        "id": "openai/gpt-4-turbo",
                        "name": "GPT-4 Turbo",
                        "description": "OpenAI's most capable model",
                        "input_cost": 0.01,
                        "output_cost": 0.03,
                        "context_length": 128000
                    }
                ]
            }
        }
    )