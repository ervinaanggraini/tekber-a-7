from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ..core.schemas import PersistentDeletion, TimestampSchema, UUIDSchema
from ..models.financial_transaction import TransactionCategory, TransactionType


class FinancialTransactionBase(BaseModel):
    """Base schema untuk transaksi keuangan"""
    amount: Annotated[
        Decimal, 
        Field(
            gt=0, 
            decimal_places=2, 
            examples=[50000.00, 150000.50, 25000.75],
            description="Jumlah uang dalam Rupiah"
        )
    ]
    transaction_type: Annotated[
        TransactionType, 
        Field(examples=[TransactionType.INCOME, TransactionType.EXPENSE])
    ]
    category: Annotated[
        TransactionCategory,
        Field(examples=[TransactionCategory.FOOD, TransactionCategory.SALARY])
    ]
    description: Annotated[
        str | None, 
        Field(
            max_length=500, 
            default=None,
            examples=["Gaji bulan November", "Makan siang di restoran", "Beli buku pemrograman"],
            description="Deskripsi optional untuk transaksi"
        )
    ]
    transaction_date: Annotated[
        datetime,
        Field(
            examples=["2025-11-20T10:30:00Z"],
            description="Tanggal dan waktu transaksi dilakukan"
        )
    ]


class FinancialTransaction(TimestampSchema, FinancialTransactionBase, UUIDSchema, PersistentDeletion):
    """Full model dengan semua fields untuk internal use"""
    user_id: int


class FinancialTransactionRead(BaseModel):
    """Schema untuk response data transaksi"""
    id: int
    user_id: int
    amount: Decimal
    transaction_type: TransactionType
    category: TransactionCategory
    description: str | None
    transaction_date: datetime
    created_at: datetime


class FinancialTransactionCreate(FinancialTransactionBase):
    """Schema untuk membuat transaksi baru"""
    model_config = ConfigDict(extra="forbid")
    
    # user_id akan diisi otomatis dari current_user, tidak perlu input


class FinancialTransactionCreateInternal(FinancialTransactionCreate):
    """Schema internal dengan user_id untuk database operation"""
    user_id: int


class FinancialTransactionUpdate(BaseModel):
    """Schema untuk update transaksi"""
    model_config = ConfigDict(extra="forbid")
    
    amount: Annotated[
        Decimal | None, 
        Field(
            gt=0, 
            decimal_places=2, 
            default=None,
            examples=[75000.00]
        )
    ] = None
    transaction_type: Annotated[TransactionType | None, Field(default=None)] = None
    category: Annotated[TransactionCategory | None, Field(default=None)] = None
    description: Annotated[
        str | None, 
        Field(max_length=500, default=None)
    ] = None
    transaction_date: Annotated[datetime | None, Field(default=None)] = None


class FinancialTransactionUpdateInternal(FinancialTransactionUpdate):
    """Schema internal untuk update dengan timestamp"""
    updated_at: datetime


class FinancialSummary(BaseModel):
    """Schema untuk summary keuangan pengguna"""
    total_income: Annotated[
        Decimal, 
        Field(examples=[5000000.00], description="Total pemasukan")
    ]
    total_expense: Annotated[
        Decimal, 
        Field(examples=[3500000.00], description="Total pengeluaran")
    ]
    balance: Annotated[
        Decimal, 
        Field(examples=[1500000.00], description="Saldo (income - expense)")
    ]
    transaction_count: Annotated[
        int, 
        Field(examples=[125], description="Jumlah total transaksi")
    ]
    income_count: Annotated[
        int, 
        Field(examples=[45], description="Jumlah transaksi pemasukan")
    ]
    expense_count: Annotated[
        int, 
        Field(examples=[80], description="Jumlah transaksi pengeluaran")
    ]


class CategorySummary(BaseModel):
    """Schema untuk summary per kategori"""
    category: TransactionCategory
    total_amount: Decimal
    transaction_count: int
    percentage: Annotated[
        float, 
        Field(examples=[15.5], description="Persentase dari total")
    ]


class FinancialAnalytics(BaseModel):
    """Schema untuk analytics keuangan yang lebih detail"""
    summary: FinancialSummary
    income_by_category: list[CategorySummary]
    expense_by_category: list[CategorySummary]
    monthly_trend: Annotated[
        dict[str, Decimal], 
        Field(
            examples=[{"2025-10": 2500000.00, "2025-11": 3200000.00}],
            description="Trend bulanan (format: YYYY-MM)"
        )
    ]


class FinancialTransactionFilter(BaseModel):
    """Schema untuk filter transaksi"""
    transaction_type: TransactionType | None = None
    category: TransactionCategory | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None