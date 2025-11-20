from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastcrud import PaginatedListResponse, compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import ForbiddenException, NotFoundException
from ...crud.crud_financial_transaction import crud_financial_transaction
from ...models.financial_transaction import TransactionCategory, TransactionType
from ...schemas.financial_transaction import (
    CategorySummary,
    FinancialAnalytics,
    FinancialSummary,
    FinancialTransactionCreate,
    FinancialTransactionCreateInternal,
    FinancialTransactionRead,
    FinancialTransactionUpdate,
    FinancialTransactionUpdateInternal,
)

router = APIRouter(tags=["Financial Transactions"])


@router.post(
    "/transaction",
    response_model=FinancialTransactionRead,
    status_code=201,
    summary="Tambah Transaksi Keuangan",
    description="""
    Menambahkan transaksi keuangan baru (pemasukan atau pengeluaran).
    
    **Parameter:**
    - **amount**: Jumlah uang dalam Rupiah (harus > 0)
    - **transaction_type**: Jenis transaksi ('income' atau 'expense')  
    - **category**: Kategori transaksi (lihat enum untuk pilihan lengkap)
    - **description**: Deskripsi optional untuk transaksi
    - **transaction_date**: Tanggal dan waktu transaksi dilakukan
    
    **Contoh kategori:**
    - Income: salary, freelance, business, investment, gift, other_income
    - Expense: food, transport, health, education, entertainment, shopping, bills, rent, other_expense
    
    **Response:**
    Data transaksi yang berhasil dibuat dengan ID dan timestamp.
    """
)
async def create_transaction(
    request: Request,
    transaction: FinancialTransactionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict[str, Any]:
    """Membuat transaksi keuangan baru"""
    
    # Buat internal schema dengan user_id dari current user
    transaction_internal = FinancialTransactionCreateInternal(
        **transaction.model_dump(),
        user_id=current_user["id"]
    )
    
    created_transaction = await crud_financial_transaction.create(
        db=db, 
        object=transaction_internal,
        schema_to_select=FinancialTransactionRead
    )
    
    if created_transaction is None:
        raise NotFoundException("Failed to create transaction")
        
    return created_transaction


@router.get(
    "/transactions",
    response_model=PaginatedListResponse[FinancialTransactionRead],
    summary="List Transaksi Keuangan",
    description="""
    Mengambil daftar transaksi keuangan user dengan berbagai filter dan pagination.
    
    **Filter yang tersedia:**
    - **transaction_type**: Filter berdasarkan jenis ('income' atau 'expense')
    - **category**: Filter berdasarkan kategori
    - **start_date**: Tanggal mulai (ISO format: YYYY-MM-DDTHH:mm:ss)
    - **end_date**: Tanggal akhir (ISO format: YYYY-MM-DDTHH:mm:ss)  
    - **min_amount**: Minimum amount
    - **max_amount**: Maximum amount
    
    **Pagination:**
    - **page**: Nomor halaman (default: 1)
    - **items_per_page**: Jumlah item per halaman (default: 10, max: 100)
    
    **Response:**
    Daftar transaksi dengan informasi pagination (total items, total pages, dll).
    """
)
async def get_transactions(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: Annotated[int, Query(ge=1, description="Nomor halaman")] = 1,
    items_per_page: Annotated[int, Query(ge=1, le=100, description="Item per halaman")] = 10,
    transaction_type: Annotated[
        TransactionType | None, 
        Query(description="Filter berdasarkan tipe transaksi")
    ] = None,
    category: Annotated[
        TransactionCategory | None,
        Query(description="Filter berdasarkan kategori")
    ] = None,
    start_date: Annotated[
        datetime | None,
        Query(description="Tanggal mulai (ISO format)")
    ] = None,
    end_date: Annotated[
        datetime | None,
        Query(description="Tanggal akhir (ISO format)")
    ] = None,
    min_amount: Annotated[
        Decimal | None,
        Query(ge=0, description="Minimum amount")
    ] = None,
    max_amount: Annotated[
        Decimal | None,
        Query(ge=0, description="Maximum amount")
    ] = None,
) -> dict:
    """Mengambil daftar transaksi user dengan filter"""
    
    transactions_data = await crud_financial_transaction.get_user_transactions(
        db=db,
        user_id=current_user["id"],
        transaction_type=transaction_type,
        category=category.value if category else None,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        offset=compute_offset(page, items_per_page),
        limit=items_per_page
    )
    
    response: dict[str, Any] = paginated_response(
        crud_data=transactions_data,
        page=page,
        items_per_page=items_per_page
    )
    return response


@router.get(
    "/transaction/{transaction_id}",
    response_model=FinancialTransactionRead,
    summary="Detail Transaksi",
    description="""
    Mengambil detail transaksi keuangan berdasarkan ID.
    
    **Parameter:**
    - **transaction_id**: ID transaksi yang ingin diambil
    
    **Response:**
    Detail lengkap dari transaksi yang diminta.
    
    **Error:**
    - 404: Transaksi tidak ditemukan atau bukan milik user
    """
)
async def get_transaction(
    request: Request,
    transaction_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict[str, Any]:
    """Mengambil detail transaksi berdasarkan ID"""
    
    transaction = await crud_financial_transaction.get(
        db=db,
        id=transaction_id,
        user_id=current_user["id"],
        is_deleted=False,
        schema_to_select=FinancialTransactionRead
    )
    
    if transaction is None:
        raise NotFoundException("Transaction not found")
        
    return transaction


@router.patch(
    "/transaction/{transaction_id}",
    response_model=dict[str, str],
    summary="Update Transaksi",
    description="""
    Mengupdate transaksi keuangan yang ada.
    
    **Parameter:**
    - **transaction_id**: ID transaksi yang ingin diupdate
    - Body berisi field yang ingin diupdate (semua field optional)
    
    **Field yang bisa diupdate:**
    - amount: Jumlah uang baru
    - transaction_type: Jenis transaksi baru
    - category: Kategori baru
    - description: Deskripsi baru
    - transaction_date: Tanggal transaksi baru
    
    **Response:**
    Pesan konfirmasi update berhasil.
    
    **Error:**
    - 404: Transaksi tidak ditemukan atau bukan milik user
    """
)
async def update_transaction(
    request: Request,
    transaction_id: int,
    values: FinancialTransactionUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict[str, str]:
    """Update transaksi keuangan"""
    
    # Cek apakah transaksi exists dan milik user
    existing_transaction = await crud_financial_transaction.get(
        db=db,
        id=transaction_id,
        user_id=current_user["id"],
        is_deleted=False
    )
    
    if existing_transaction is None:
        raise NotFoundException("Transaction not found")
    
    # Prepare update data dengan timestamp
    update_data = FinancialTransactionUpdateInternal(
        **values.model_dump(exclude_unset=True),
        updated_at=datetime.now(UTC)
    )
    
    await crud_financial_transaction.update(
        db=db,
        object=update_data,
        id=transaction_id,
        user_id=current_user["id"]
    )
    
    return {"message": "Transaction updated successfully"}


@router.delete(
    "/transaction/{transaction_id}",
    response_model=dict[str, str],
    summary="Hapus Transaksi (Soft Delete)",
    description="""
    Menghapus transaksi keuangan (soft delete).
    
    **Parameter:**
    - **transaction_id**: ID transaksi yang ingin dihapus
    
    **Note:**
    Transaksi akan di-soft delete (is_deleted=True) sehingga masih ada di database
    tapi tidak muncul di query normal. Ini untuk menjaga integritas data finansial.
    
    **Response:**
    Pesan konfirmasi penghapusan berhasil.
    
    **Error:**
    - 404: Transaksi tidak ditemukan atau bukan milik user
    """
)
async def delete_transaction(
    request: Request,
    transaction_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict[str, str]:
    """Soft delete transaksi keuangan"""
    
    # Cek apakah transaksi exists dan milik user
    existing_transaction = await crud_financial_transaction.get(
        db=db,
        id=transaction_id,
        user_id=current_user["id"],
        is_deleted=False
    )
    
    if existing_transaction is None:
        raise NotFoundException("Transaction not found")
    
    await crud_financial_transaction.delete(
        db=db,
        id=transaction_id,
        user_id=current_user["id"]
    )
    
    return {"message": "Transaction deleted successfully"}


@router.delete(
    "/transaction/{transaction_id}/permanent",
    response_model=dict[str, str],
    summary="Hapus Transaksi Permanen (Hard Delete)",
    description="""
    Menghapus transaksi keuangan secara permanen dari database.
    
    **Parameter:**
    - **transaction_id**: ID transaksi yang ingin dihapus permanen
    
    **⚠️ PERINGATAN:**
    Ini adalah penghapusan permanen! Data tidak dapat dikembalikan setelah dihapus.
    Gunakan dengan hati-hati.
    
    **Response:**
    Pesan konfirmasi penghapusan permanen berhasil.
    
    **Error:**
    - 404: Transaksi tidak ditemukan atau bukan milik user
    """
)
async def permanent_delete_transaction(
    request: Request,
    transaction_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict[str, str]:
    """Hard delete transaksi keuangan"""
    
    # Cek apakah transaksi exists dan milik user
    existing_transaction = await crud_financial_transaction.get(
        db=db,
        id=transaction_id,
        user_id=current_user["id"]
    )
    
    if existing_transaction is None:
        raise NotFoundException("Transaction not found")
    
    await crud_financial_transaction.db_delete(
        db=db,
        id=transaction_id,
        user_id=current_user["id"]
    )
    
    return {"message": "Transaction permanently deleted"}


@router.get(
    "/financial/summary",
    response_model=FinancialSummary,
    summary="Summary Keuangan",
    description="""
    Mendapatkan ringkasan keuangan user secara keseluruhan atau dalam periode tertentu.
    
    **Parameter (Optional):**
    - **start_date**: Tanggal mulai untuk filter periode (ISO format)
    - **end_date**: Tanggal akhir untuk filter periode (ISO format)
    
    **Response:**
    - **total_income**: Total pemasukan
    - **total_expense**: Total pengeluaran  
    - **balance**: Saldo (income - expense)
    - **transaction_count**: Jumlah total transaksi
    - **income_count**: Jumlah transaksi pemasukan
    - **expense_count**: Jumlah transaksi pengeluaran
    
    **Contoh penggunaan:**
    - Tanpa parameter: Summary keseluruhan
    - Dengan periode: Summary bulan/tahun tertentu
    """
)
async def get_financial_summary(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    start_date: Annotated[
        datetime | None,
        Query(description="Tanggal mulai periode (ISO format)")
    ] = None,
    end_date: Annotated[
        datetime | None,
        Query(description="Tanggal akhir periode (ISO format)")
    ] = None,
) -> dict[str, Any]:
    """Mendapatkan summary keuangan user"""
    
    summary = await crud_financial_transaction.get_financial_summary(
        db=db,
        user_id=current_user["id"],
        start_date=start_date,
        end_date=end_date
    )
    
    return summary


@router.get(
    "/financial/analytics",
    response_model=FinancialAnalytics,
    summary="Analytics Keuangan Detail",
    description="""
    Mendapatkan analytics keuangan yang lebih detail termasuk breakdown per kategori dan trend bulanan.
    
    **Parameter (Optional):**
    - **start_date**: Tanggal mulai untuk filter periode (ISO format)
    - **end_date**: Tanggal akhir untuk filter periode (ISO format)
    - **months**: Jumlah bulan untuk trend analysis (default: 12)
    
    **Response:**
    - **summary**: Summary dasar keuangan
    - **income_by_category**: Breakdown pemasukan per kategori
    - **expense_by_category**: Breakdown pengeluaran per kategori
    - **monthly_trend**: Trend net income per bulan
    
    **Use case:**
    - Dashboard analytics
    - Laporan keuangan bulanan/tahunan
    - Analisis pola spending
    """
)
async def get_financial_analytics(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    start_date: Annotated[
        datetime | None,
        Query(description="Tanggal mulai periode")
    ] = None,
    end_date: Annotated[
        datetime | None,
        Query(description="Tanggal akhir periode")
    ] = None,
    months: Annotated[
        int,
        Query(ge=1, le=60, description="Jumlah bulan untuk trend")
    ] = 12,
) -> dict[str, Any]:
    """Mendapatkan analytics keuangan detail"""
    
    # Get basic summary
    summary = await crud_financial_transaction.get_financial_summary(
        db=db,
        user_id=current_user["id"],
        start_date=start_date,
        end_date=end_date
    )
    
    # Get category breakdowns
    income_categories = await crud_financial_transaction.get_category_summary(
        db=db,
        user_id=current_user["id"],
        transaction_type=TransactionType.INCOME,
        start_date=start_date,
        end_date=end_date
    )
    
    expense_categories = await crud_financial_transaction.get_category_summary(
        db=db,
        user_id=current_user["id"],
        transaction_type=TransactionType.EXPENSE,
        start_date=start_date,
        end_date=end_date
    )
    
    # Get monthly trend
    monthly_trend = await crud_financial_transaction.get_monthly_trend(
        db=db,
        user_id=current_user["id"],
        months=months
    )
    
    return {
        "summary": summary,
        "income_by_category": income_categories,
        "expense_by_category": expense_categories,
        "monthly_trend": monthly_trend
    }


@router.get(
    "/financial/categories/{transaction_type}",
    response_model=list[CategorySummary],
    summary="Summary per Kategori",
    description="""
    Mendapatkan breakdown keuangan per kategori untuk jenis transaksi tertentu.
    
    **Parameter:**
    - **transaction_type**: Jenis transaksi ('income' atau 'expense')
    - **start_date**: Tanggal mulai untuk filter periode (optional)
    - **end_date**: Tanggal akhir untuk filter periode (optional)
    
    **Response:**
    List kategori dengan:
    - **category**: Nama kategori
    - **total_amount**: Total amount untuk kategori
    - **transaction_count**: Jumlah transaksi
    - **percentage**: Persentase dari total
    
    **Use case:**
    - Melihat pengeluaran terbesar per kategori
    - Analisis sumber income utama
    - Budget tracking per kategori
    """
)
async def get_category_summary(
    request: Request,
    transaction_type: TransactionType,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    start_date: Annotated[
        datetime | None,
        Query(description="Tanggal mulai periode")
    ] = None,
    end_date: Annotated[
        datetime | None,
        Query(description="Tanggal akhir periode")
    ] = None,
) -> list[dict[str, Any]]:
    """Mendapatkan summary per kategori"""
    
    categories = await crud_financial_transaction.get_category_summary(
        db=db,
        user_id=current_user["id"],
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date
    )
    
    return categories