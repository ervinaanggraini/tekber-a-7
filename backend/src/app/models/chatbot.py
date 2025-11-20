import uuid as uuid_pkg
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from ..core.db.database import Base


class MessageRole(str, Enum):
    """Role untuk message dalam conversation"""
    USER = "user"          # Message dari user
    ASSISTANT = "assistant" # Response dari AI
    SYSTEM = "system"      # System message (optional)


class ConversationStatus(str, Enum):
    """Status conversation"""
    ACTIVE = "active"       # Conversation aktif
    ARCHIVED = "archived"   # Conversation diarsipkan
    DELETED = "deleted"     # Conversation dihapus


class ChatConversation(Base):
    """
    Model untuk menyimpan conversation chatbot
    
    Attributes:
        id: Primary key
        user_id: Foreign key ke user yang memiliki conversation
        title: Judul conversation (auto-generated atau custom)
        status: Status conversation (active/archived/deleted)
        model_name: Nama model AI yang digunakan (dari OpenRouter)
        system_prompt: System prompt yang digunakan (optional)
        total_messages: Jumlah total message dalam conversation
        uuid: Unique identifier
        created_at: Timestamp pembuatan
        updated_at: Timestamp update terakhir
        deleted_at: Timestamp penghapusan (soft delete)
        is_deleted: Flag untuk soft delete
    """
    __tablename__ = "chat_conversation"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, init=False)
    
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[ConversationStatus] = mapped_column(String(20), default=ConversationStatus.ACTIVE, init=False)
    model_name: Mapped[str] = mapped_column(String(100), default="anthropic/claude-3.5-sonnet", init=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, default=None, init=False)
    total_messages: Mapped[int] = mapped_column(default=0, init=False)
    
    # Standard fields
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), default_factory=uuid7, unique=True, init=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC), init=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True, init=False)


class ChatMessage(Base):
    """
    Model untuk menyimpan individual message dalam conversation
    
    Attributes:
        id: Primary key
        conversation_id: Foreign key ke conversation
        role: Role message (user/assistant/system)
        content: Isi message
        model_name: Model yang digunakan untuk generate response (untuk assistant messages)
        token_count: Jumlah token yang digunakan (optional)
        cost: Biaya untuk message ini (optional, dalam USD)
        response_time: Waktu response dari AI (dalam seconds)
        uuid: Unique identifier
        created_at: Timestamp pembuatan
        updated_at: Timestamp update terakhir
        is_deleted: Flag untuk soft delete
    """
    __tablename__ = "chat_message"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("chat_conversation.id"), index=True, init=False)
    
    role: Mapped[MessageRole] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    
    # Metadata untuk AI responses
    model_name: Mapped[str | None] = mapped_column(String(100), default=None, init=False)
    token_count: Mapped[int | None] = mapped_column(default=None, init=False)
    cost: Mapped[float | None] = mapped_column(default=None, init=False)  # dalam USD
    response_time: Mapped[float | None] = mapped_column(default=None, init=False)  # dalam seconds
    
    # Standard fields
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), default_factory=uuid7, unique=True, init=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC), init=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True, init=False)