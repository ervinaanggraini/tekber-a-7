from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID

from fastcrud import FastCRUD
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.chatbot import ChatConversation, ChatMessage, ConversationStatus, MessageRole
from ..schemas.chatbot import (
    ChatConversationCreate,
    ChatConversationUpdate,
    ChatConversationRead,
    ChatMessageCreate,
    ChatMessageRead,
    ChatStats,
)


CRUDChatConversation = FastCRUD[ChatConversation, ChatConversationCreate, ChatConversationUpdate, ChatConversationUpdate, Dict[str, Any], ChatConversationRead]

class CRUDChatConversationExt(CRUDChatConversation):
    """CRUD operations untuk ChatConversation"""
    
    async def get_user_conversations(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        status: Optional[ConversationStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChatConversation]:
        """
        Get conversations untuk specific user dengan optional status filter
        
        Args:
            db: Database session
            user_id: User ID
            status: Optional conversation status filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of conversations ordered by updated_at desc
        """
        conditions = [ChatConversation.user_id == user_id]
        
        if status:
            conditions.append(ChatConversation.status == status)
        
        return await self.get_multi(
            db=db,
            skip=skip,
            limit=limit,
            where=and_(*conditions),
            order_by=desc(ChatConversation.updated_at),
            schema_to_select=[
                ChatConversation.id,
                ChatConversation.title,
                ChatConversation.status,
                ChatConversation.created_at,
                ChatConversation.updated_at,
                ChatConversation.message_count,
                ChatConversation.last_message_at
            ]
        )
    
    async def get_with_messages(
        self,
        db: AsyncSession,
        *,
        conversation_id: UUID,
        user_id: UUID
    ) -> Optional[ChatConversation]:
        """
        Get conversation dengan semua messages nya
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID untuk security check
            
        Returns:
            Conversation with messages atau None jika tidak ditemukan
        """
        stmt = (
            select(ChatConversation)
            .options(selectinload(ChatConversation.messages))
            .where(
                and_(
                    ChatConversation.id == conversation_id,
                    ChatConversation.user_id == user_id
                )
            )
        )
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_conversation_stats(
        self,
        db: AsyncSession,
        *,
        conversation_id: UUID
    ) -> Optional[ChatConversation]:
        """
        Update conversation statistics (message count, last message time)
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            
        Returns:
            Updated conversation atau None jika tidak ditemukan
        """
        # Get message count and last message time
        stmt = (
            select(
                func.count(ChatMessage.id).label("message_count"),
                func.max(ChatMessage.created_at).label("last_message_at")
            )
            .where(ChatMessage.conversation_id == conversation_id)
        )
        
        result = await db.execute(stmt)
        stats = result.first()
        
        if not stats:
            return None
        
        # Update conversation
        update_data = {
            "message_count": stats.message_count,
            "last_message_at": stats.last_message_at,
            "updated_at": datetime.utcnow()
        }
        
        return await self.update(
            db=db,
            object_id=conversation_id,
            object_data=update_data
        )
    
    async def get_user_stats(
        self,
        db: AsyncSession,
        *,
        user_id: UUID
    ) -> ChatStats:
        """
        Get chat statistics untuk user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Chat statistics
        """
        # Conversation stats
        conv_stmt = (
            select(
                func.count(ChatConversation.id).label("total_conversations"),
                func.count().filter(ChatConversation.status == ConversationStatus.ACTIVE).label("active_conversations"),
                func.sum(ChatConversation.message_count).label("total_messages")
            )
            .where(ChatConversation.user_id == user_id)
        )
        
        conv_result = await db.execute(conv_stmt)
        conv_stats = conv_result.first()
        
        # Message stats by role
        msg_stmt = (
            select(
                ChatMessage.role,
                func.count(ChatMessage.id).label("count")
            )
            .join(ChatConversation)
            .where(ChatConversation.user_id == user_id)
            .group_by(ChatMessage.role)
        )
        
        msg_result = await db.execute(msg_stmt)
        msg_stats = {row.role.value: row.count for row in msg_result}
        
        return ChatStats(
            total_conversations=conv_stats.total_conversations or 0,
            active_conversations=conv_stats.active_conversations or 0,
            total_messages=conv_stats.total_messages or 0,
            user_messages=msg_stats.get("user", 0),
            assistant_messages=msg_stats.get("assistant", 0),
            system_messages=msg_stats.get("system", 0)
        )


CRUDChatMessage = FastCRUD[ChatMessage, ChatMessageCreate, Dict[str, Any], Dict[str, Any], Dict[str, Any], ChatMessageRead]

class CRUDChatMessageExt(CRUDChatMessage):
    """CRUD operations untuk ChatMessage"""
    
    async def create_with_conversation_update(
        self,
        db: AsyncSession,
        *,
        obj_in: ChatMessageCreate,
        conversation_id: UUID
    ) -> ChatMessage:
        """
        Create message dan update conversation statistics
        
        Args:
            db: Database session
            obj_in: Message data
            conversation_id: Conversation ID
            
        Returns:
            Created message
        """
        # Create message
        message_data = obj_in.model_dump()
        message_data["conversation_id"] = conversation_id
        
        message = await self.create(db=db, object_data=message_data)
        
        # Update conversation stats
        await crud_chat_conversation.update_conversation_stats(
            db=db, 
            conversation_id=conversation_id
        )
        
        return message
    
    async def get_conversation_messages(
        self,
        db: AsyncSession,
        *,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 100,
        role_filter: Optional[MessageRole] = None
    ) -> List[ChatMessage]:
        """
        Get messages untuk specific conversation
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            role_filter: Optional role filter
            
        Returns:
            List of messages ordered by created_at asc
        """
        conditions = [ChatMessage.conversation_id == conversation_id]
        
        if role_filter:
            conditions.append(ChatMessage.role == role_filter)
        
        return await self.get_multi(
            db=db,
            skip=skip,
            limit=limit,
            where=and_(*conditions),
            order_by=ChatMessage.created_at
        )
    
    async def get_recent_context(
        self,
        db: AsyncSession,
        *,
        conversation_id: UUID,
        limit: int = 10
    ) -> List[ChatMessage]:
        """
        Get recent messages untuk conversation context
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            limit: Maximum number of recent messages
            
        Returns:
            List of recent messages ordered by created_at desc
        """
        return await self.get_multi(
            db=db,
            limit=limit,
            where=ChatMessage.conversation_id == conversation_id,
            order_by=desc(ChatMessage.created_at)
        )
    
    async def search_messages(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        search_query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[ChatMessage]:
        """
        Search messages berdasarkan content
        
        Args:
            db: Database session
            user_id: User ID untuk security
            search_query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching messages
        """
        stmt = (
            select(ChatMessage)
            .join(ChatConversation)
            .where(
                and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.content.ilike(f"%{search_query}%")
                )
            )
            .order_by(desc(ChatMessage.created_at))
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all())


# Create CRUD instances
crud_chat_conversation = CRUDChatConversationExt(ChatConversation)
crud_chat_message = CRUDChatMessageExt(ChatMessage)