import uuid as uuid_pkg
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from ..core.db.database import Base


class TransactionType(str, Enum):
    """Tipe transaksi keuangan"""
    INCOME = "income"      # Pemasukan
    EXPENSE = "expense"    # Pengeluaran


class TransactionCategory(str, Enum):
    """Kategori transaksi keuangan"""
    # Kategori Income
    SALARY = "salary"                    # Gaji
    FREELANCE = "freelance"             # Freelance
    BUSINESS = "business"               # Bisnis
    INVESTMENT = "investment"           # Investasi
    GIFT = "gift"                      # Hadiah
    OTHER_INCOME = "other_income"      # Pemasukan lainnya
    
    # Kategori Expense
    FOOD = "food"                      # Makanan
    TRANSPORT = "transport"            # Transportasi
    HEALTH = "health"                  # Kesehatan
    EDUCATION = "education"            # Pendidikan
    ENTERTAINMENT = "entertainment"     # Hiburan
    SHOPPING = "shopping"              # Belanja
    BILLS = "bills"                    # Tagihan
    RENT = "rent"                      # Sewa
    INVESTMENT_EXP = "investment_exp"  # Investasi
    OTHER_EXPENSE = "other_expense"    # Pengeluaran lainnya


class FinancialTransaction(Base):
    """
    Model untuk mencatat transaksi keuangan pengguna
    
    Attributes:
        id: Primary key
        user_id: Foreign key ke tabel user
        amount: Jumlah uang (menggunakan Decimal untuk precision)
        transaction_type: Jenis transaksi (income/expense)
        category: Kategori transaksi
        description: Deskripsi transaksi
        transaction_date: Tanggal transaksi
        uuid: Unique identifier
        created_at: Timestamp pembuatan
        updated_at: Timestamp update terakhir
        deleted_at: Timestamp penghapusan (soft delete)
        is_deleted: Flag untuk soft delete
    """
    __tablename__ = "financial_transaction"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, init=False)
    
    # Menggunakan Numeric untuk precision dalam mata uang
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2))
    
    transaction_type: Mapped[TransactionType] = mapped_column(String(10), index=True)
    category: Mapped[TransactionCategory] = mapped_column(String(20), index=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    
    description: Mapped[str | None] = mapped_column(Text, default=None, init=False)
    
    # Standard fields
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), default_factory=uuid7, unique=True, init=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC), init=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True, init=False)