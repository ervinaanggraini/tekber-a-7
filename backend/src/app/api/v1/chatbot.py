from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...core.exceptions import BadRequestException, NotFoundException
from ...api.dependencies import get_current_user
from ...core.services.openrouter_service import openrouter_service
from ...crud.crud_chatbot import crud_chat_conversation, crud_chat_message
from ...models.chatbot import ConversationStatus, MessageRole
from ...models.user import User
from ...schemas.chatbot import (
    ChatConversationCreate,
    ChatConversationRead,
    ChatConversationUpdate,
    ChatMessageRead,
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ChatStats,
)

router = APIRouter()
security = HTTPBearer()


@router.post("/chat", response_model=ChatResponse, summary="Send Chat Message")
async def send_chat_message(
    request: ChatRequest,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Mengirim pesan chat dan mendapatkan response dari AI
    
    Flow:
    1. Jika conversation_id tidak ada, buat conversation baru
    2. Simpan user message ke database
    3. Kirim request ke OpenRouter API
    4. Simpan AI response ke database
    5. Return response dengan conversation info
    
    **Parameters:**
    - **message**: Pesan dari user
    - **conversation_id**: Optional ID conversation yang sudah ada
    - **model**: Model AI yang digunakan (default: claude-3.5-sonnet)
    - **temperature**: Kreativitas response (0.0-2.0)
    - **max_tokens**: Maksimum token untuk response
    
    **Returns:**
    - Response dari AI dengan metadata conversation
    """
    try:
        conversation_id = request.conversation_id
        
        # Jika tidak ada conversation_id, buat conversation baru
        if not conversation_id:
            # Generate title dari first message (max 100 chars)
            title = request.message[:100]
            if len(request.message) > 100:
                title += "..."
            
            conversation_data = ChatConversationCreate(
                title=title,
                user_id=current_user.id
            )
            
            conversation = await crud_chat_conversation.create(
                db=db, 
                object_data=conversation_data.model_dump()
            )
            conversation_id = conversation.id
            
        else:
            # Verify conversation belongs to user
            conversation = await crud_chat_conversation.get(
                db=db, 
                schema_to_select=[],
                id=conversation_id
            )
            
            if not conversation or conversation.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            
            # Check if conversation is active
            if conversation.status != ConversationStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot send message to inactive conversation"
                )
        
        # Simpan user message
        user_message_data = {
            "role": MessageRole.USER,
            "content": request.message,
            "metadata": {"client_timestamp": request.timestamp}
        }
        
        await crud_chat_message.create_with_conversation_update(
            db=db,
            obj_in=user_message_data,
            conversation_id=conversation_id
        )
        
        # Get recent context untuk AI
        recent_messages = await crud_chat_message.get_recent_context(
            db=db,
            conversation_id=conversation_id,
            limit=10
        )
        
        # Format messages untuk OpenRouter API
        api_messages = []
        
        # Add system message jika ada
        if request.system_message:
            api_messages.append({
                "role": "system",
                "content": request.system_message
            })
        
        # Add conversation history (reverse order karena get_recent_context return desc)
        for msg in reversed(recent_messages):
            api_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        # Send request ke OpenRouter
        ai_response = await openrouter_service.send_chat_request(
            messages=api_messages,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Simpan AI response
        ai_message_data = {
            "role": MessageRole.ASSISTANT,
            "content": ai_response["content"],
            "metadata": {
                "model": ai_response["model"],
                "usage": ai_response["usage"],
                "response_time": ai_response["response_time"],
                "estimated_cost": ai_response["estimated_cost"]
            }
        }
        
        await crud_chat_message.create_with_conversation_update(
            db=db,
            obj_in=ai_message_data,
            conversation_id=conversation_id
        )
        
        return ChatResponse(
            message=ai_response["content"],
            conversation_id=conversation_id,
            model=ai_response["model"],
            usage=ai_response["usage"],
            response_time=ai_response["response_time"],
            estimated_cost=ai_response["estimated_cost"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat request failed: {str(e)}"
        )


@router.get("/conversations", response_model=List[ChatConversationRead], summary="Get User Conversations")
async def get_conversations(
    status: Optional[ConversationStatus] = Query(None, description="Filter by conversation status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
) -> List[ChatConversationRead]:
    """
    Mendapatkan daftar conversation milik user
    
    **Parameters:**
    - **status**: Filter berdasarkan status (ACTIVE/ARCHIVED/DELETED)
    - **skip**: Jumlah record yang dilewati
    - **limit**: Maksimum record yang dikembalikan
    
    **Returns:**
    - List conversation ordered by updated_at descending
    """
    conversations = await crud_chat_conversation.get_user_conversations(
        db=db,
        user_id=current_user.id,
        status=status,
        skip=skip,
        limit=limit
    )
    
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail, summary="Get Conversation Detail")
async def get_conversation_detail(
    conversation_id: UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
) -> ConversationDetail:
    """
    Mendapatkan detail conversation beserta semua messages
    
    **Parameters:**
    - **conversation_id**: UUID conversation
    
    **Returns:**
    - Conversation detail dengan semua messages
    """
    conversation = await crud_chat_conversation.get_with_messages(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        status=conversation.status,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=conversation.message_count,
        last_message_at=conversation.last_message_at,
        messages=[
            ChatMessageRead(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                metadata=msg.metadata
            )
            for msg in conversation.messages
        ]
    )


@router.put("/conversations/{conversation_id}", response_model=ChatConversationRead, summary="Update Conversation")
async def update_conversation(
    conversation_id: UUID,
    update_data: ChatConversationUpdate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
) -> ChatConversationRead:
    """
    Update conversation (title atau status)
    
    **Parameters:**
    - **conversation_id**: UUID conversation
    - **title**: Title baru (optional)
    - **status**: Status baru (optional)
    
    **Returns:**
    - Updated conversation
    """
    # Verify conversation belongs to user
    existing = await crud_chat_conversation.get(
        db=db, 
        schema_to_select=[],
        id=conversation_id
    )
    
    if not existing or existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    updated_conversation = await crud_chat_conversation.update(
        db=db,
        object_id=conversation_id,
        object_data=update_data.model_dump(exclude_unset=True)
    )
    
    return updated_conversation


@router.delete("/conversations/{conversation_id}", summary="Delete Conversation")
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Soft delete conversation (set status to DELETED)
    
    **Parameters:**
    - **conversation_id**: UUID conversation
    
    **Returns:**
    - Success message
    """
    # Verify conversation belongs to user
    existing = await crud_chat_conversation.get(
        db=db, 
        schema_to_select=[],
        id=conversation_id
    )
    
    if not existing or existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Soft delete by setting status
    await crud_chat_conversation.update(
        db=db,
        object_id=conversation_id,
        object_data={"status": ConversationStatus.DELETED}
    )
    
    return {"message": "Conversation deleted successfully"}


@router.get("/messages/search", response_model=List[ChatMessageRead], summary="Search Messages")
async def search_messages(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
) -> List[ChatMessageRead]:
    """
    Mencari messages berdasarkan content
    
    **Parameters:**
    - **q**: Search query (minimum 1 character)
    - **skip**: Jumlah record yang dilewati
    - **limit**: Maksimum record yang dikembalikan
    
    **Returns:**
    - List messages yang mengandung search query
    """
    messages = await crud_chat_message.search_messages(
        db=db,
        user_id=current_user.id,
        search_query=q,
        skip=skip,
        limit=limit
    )
    
    return messages


@router.get("/stats", response_model=ChatStats, summary="Get Chat Statistics")
async def get_chat_stats(
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
) -> ChatStats:
    """
    Mendapatkan statistik chat untuk user
    
    **Returns:**
    - Chat statistics including:
      - Total conversations
      - Active conversations
      - Total messages
      - Messages by role
    """
    stats = await crud_chat_conversation.get_user_stats(
        db=db,
        user_id=current_user.id
    )
    
    return stats


@router.get("/models", summary="Get Available AI Models")
async def get_available_models() -> Dict[str, Any]:
    """
    Mendapatkan daftar model AI yang tersedia
    
    **Returns:**
    - List of available AI models dengan pricing info
    """
    try:
        models = await openrouter_service.get_available_models()
        return {
            "models": models,
            "total": len(models)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available models: {str(e)}"
        )


@router.get("/health", summary="Chat Service Health Check")
async def chat_health_check() -> Dict[str, Any]:
    """
    Health check untuk chat service dan OpenRouter API
    
    **Returns:**
    - Service status information
    """
    try:
        openrouter_healthy = await openrouter_service.health_check()
        
        return {
            "status": "healthy" if openrouter_healthy else "degraded",
            "openrouter_api": "available" if openrouter_healthy else "unavailable",
            "timestamp": "2024-01-01T00:00:00Z"  # Will be auto-generated in real implementation
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "openrouter_api": "error",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }