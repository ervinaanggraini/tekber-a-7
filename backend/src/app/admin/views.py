from typing import Annotated

from crudadmin import CRUDAdmin
from crudadmin.admin_interface.model_view import PasswordTransformer
from pydantic import BaseModel, Field

from ..core.security import get_password_hash
from ..models.user import User
from ..models.financial_transaction import FinancialTransaction
from ..models.chatbot import ChatConversation, ChatMessage
from ..schemas.user import UserCreate, UserCreateInternal, UserUpdate
from ..schemas.financial_transaction import FinancialTransactionCreate, FinancialTransactionUpdate
from ..schemas.chatbot import ChatConversationCreate, ChatConversationUpdate, ChatMessageCreate


def register_admin_views(admin: CRUDAdmin) -> None:
    """Register all models and their schemas with the admin interface.

    This function adds all available models to the admin interface with appropriate
    schemas and permissions.
    """

    password_transformer = PasswordTransformer(
        password_field="password",
        hashed_field="hashed_password",
        hash_function=get_password_hash,
        required_fields=["name", "username", "email"],
    )

    admin.add_view(
        model=User,
        create_schema=UserCreate,
        update_schema=UserUpdate,
        update_internal_schema=UserCreateInternal,
        password_transformer=password_transformer,
        allowed_actions={"view", "create", "update"},
    )

    # Financial Transactions
    admin.add_view(
        model=FinancialTransaction,
        create_schema=FinancialTransactionCreate,
        update_schema=FinancialTransactionUpdate,
        allowed_actions={"view", "create", "update", "delete"},
    )

    # Chat Conversations
    admin.add_view(
        model=ChatConversation,
        create_schema=ChatConversationCreate,
        update_schema=ChatConversationUpdate,
        allowed_actions={"view", "update", "delete"},
    )

    # Chat Messages (view only untuk monitoring)
    admin.add_view(
        model=ChatMessage,
        create_schema=ChatMessageCreate,
        update_schema=ChatMessageCreate,  # Using create schema since we don't allow updates
        allowed_actions={"view"},
    )
