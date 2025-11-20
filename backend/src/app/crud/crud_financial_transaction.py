from datetime import datetime
from decimal import Decimal
from typing import Any

from fastcrud import FastCRUD
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.financial_transaction import FinancialTransaction, TransactionType
from ..schemas.financial_transaction import (
    FinancialTransactionCreateInternal,
    FinancialTransactionUpdate,
    FinancialTransactionUpdateInternal,
)


# Create typed CRUD class
CRUDFinancialTransaction = FastCRUD[
    FinancialTransaction, 
    FinancialTransactionCreateInternal, 
    FinancialTransactionUpdate,
    FinancialTransactionUpdateInternal,
    dict,  # Delete schema
    dict   # Read schema
]

class FinancialTransactionService:
    """
    CRUD operations untuk Financial Transaction
    
    Extends FastCRUD dengan methods tambahan untuk financial analytics
    """
    
    async def get_user_transactions(
        self, 
        db: AsyncSession, 
        user_id: int,
        transaction_type: TransactionType | None = None,
        category: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        offset: int = 0,
        limit: int = 100
    ) -> dict[str, Any]:
        """
        Get filtered transactions untuk user tertentu
        
        Args:
            db: Database session
            user_id: ID user
            transaction_type: Filter berdasarkan tipe transaksi
            category: Filter berdasarkan kategori
            start_date: Tanggal mulai
            end_date: Tanggal akhir
            min_amount: Minimum amount
            max_amount: Maximum amount
            offset: Offset untuk pagination
            limit: Limit untuk pagination
            
        Returns:
            Dict dengan data transaksi dan total count
        """
        conditions = [
            FinancialTransaction.user_id == user_id,
            FinancialTransaction.is_deleted == False
        ]
        
        if transaction_type:
            conditions.append(FinancialTransaction.transaction_type == transaction_type)
        
        if category:
            conditions.append(FinancialTransaction.category == category)
            
        if start_date:
            conditions.append(FinancialTransaction.transaction_date >= start_date)
            
        if end_date:
            conditions.append(FinancialTransaction.transaction_date <= end_date)
            
        if min_amount is not None:
            conditions.append(FinancialTransaction.amount >= min_amount)
            
        if max_amount is not None:
            conditions.append(FinancialTransaction.amount <= max_amount)
        
        return await self.get_multi(
            db=db,
            offset=offset,
            limit=limit,
            **{condition.left.name: condition.right.value for condition in conditions if hasattr(condition.right, 'value')},
            is_deleted=False
        )
    
    async def get_financial_summary(
        self, 
        db: AsyncSession, 
        user_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> dict[str, Any]:
        """
        Mendapatkan summary keuangan user
        
        Args:
            db: Database session
            user_id: ID user
            start_date: Filter tanggal mulai (optional)
            end_date: Filter tanggal akhir (optional)
            
        Returns:
            Dict berisi summary finansial
        """
        conditions = [
            FinancialTransaction.user_id == user_id,
            FinancialTransaction.is_deleted == False
        ]
        
        if start_date:
            conditions.append(FinancialTransaction.transaction_date >= start_date)
        if end_date:
            conditions.append(FinancialTransaction.transaction_date <= end_date)
        
        # Query untuk total income
        income_query = select(
            func.coalesce(func.sum(FinancialTransaction.amount), 0).label('total_income'),
            func.count(FinancialTransaction.id).label('income_count')
        ).where(
            and_(
                *conditions,
                FinancialTransaction.transaction_type == TransactionType.INCOME
            )
        )
        
        # Query untuk total expense
        expense_query = select(
            func.coalesce(func.sum(FinancialTransaction.amount), 0).label('total_expense'),
            func.count(FinancialTransaction.id).label('expense_count')
        ).where(
            and_(
                *conditions,
                FinancialTransaction.transaction_type == TransactionType.EXPENSE
            )
        )
        
        # Execute queries
        income_result = await db.execute(income_query)
        expense_result = await db.execute(expense_query)
        
        income_data = income_result.first()
        expense_data = expense_result.first()
        
        total_income = income_data.total_income if income_data else Decimal('0')
        total_expense = expense_data.total_expense if expense_data else Decimal('0')
        income_count = income_data.income_count if income_data else 0
        expense_count = expense_data.expense_count if expense_data else 0
        
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "transaction_count": income_count + expense_count,
            "income_count": income_count,
            "expense_count": expense_count
        }
    
    async def get_category_summary(
        self,
        db: AsyncSession,
        user_id: int,
        transaction_type: TransactionType,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> list[dict[str, Any]]:
        """
        Mendapatkan summary per kategori
        
        Args:
            db: Database session
            user_id: ID user
            transaction_type: Tipe transaksi (income/expense)
            start_date: Filter tanggal mulai (optional)
            end_date: Filter tanggal akhir (optional)
            
        Returns:
            List berisi summary per kategori
        """
        conditions = [
            FinancialTransaction.user_id == user_id,
            FinancialTransaction.is_deleted == False,
            FinancialTransaction.transaction_type == transaction_type
        ]
        
        if start_date:
            conditions.append(FinancialTransaction.transaction_date >= start_date)
        if end_date:
            conditions.append(FinancialTransaction.transaction_date <= end_date)
        
        query = select(
            FinancialTransaction.category,
            func.sum(FinancialTransaction.amount).label('total_amount'),
            func.count(FinancialTransaction.id).label('transaction_count')
        ).where(
            and_(*conditions)
        ).group_by(
            FinancialTransaction.category
        ).order_by(
            func.sum(FinancialTransaction.amount).desc()
        )
        
        result = await db.execute(query)
        categories = result.all()
        
        # Calculate total untuk percentage
        total_all = sum(cat.total_amount for cat in categories)
        
        return [
            {
                "category": cat.category,
                "total_amount": cat.total_amount,
                "transaction_count": cat.transaction_count,
                "percentage": float(cat.total_amount / total_all * 100) if total_all > 0 else 0.0
            }
            for cat in categories
        ]
    
    async def get_monthly_trend(
        self,
        db: AsyncSession,
        user_id: int,
        months: int = 12
    ) -> dict[str, Decimal]:
        """
        Mendapatkan trend bulanan untuk beberapa bulan terakhir
        
        Args:
            db: Database session
            user_id: ID user
            months: Jumlah bulan yang ingin ditampilkan (default 12)
            
        Returns:
            Dict dengan format {YYYY-MM: balance}
        """
        query = select(
            func.to_char(FinancialTransaction.transaction_date, 'YYYY-MM').label('month'),
            func.sum(
                func.case(
                    (FinancialTransaction.transaction_type == TransactionType.INCOME, FinancialTransaction.amount),
                    else_=-FinancialTransaction.amount
                )
            ).label('net_amount')
        ).where(
            and_(
                FinancialTransaction.user_id == user_id,
                FinancialTransaction.is_deleted == False,
                FinancialTransaction.transaction_date >= func.date_trunc('month', func.current_date()) - func.interval(f'{months-1} months')
            )
        ).group_by(
            func.to_char(FinancialTransaction.transaction_date, 'YYYY-MM')
        ).order_by(
            func.to_char(FinancialTransaction.transaction_date, 'YYYY-MM')
        )
        
        result = await db.execute(query)
        trends = result.all()
        
        return {
            trend.month: trend.net_amount
            for trend in trends
        }


# Instance untuk digunakan di endpoints
crud_financial_transaction = CRUDFinancialTransaction(FinancialTransaction)
financial_service = FinancialTransactionService()