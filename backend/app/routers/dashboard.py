from datetime import date, datetime, time, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Medicine, MedicineStatus, PurchaseOrder, PurchaseOrderStatus, Sale
from app.schemas import (
    ItemsSoldSummary,
    LowStockSummary,
    PurchaseOrderSummary,
    RecentSale,
    RecentSalesSummary,
    SalesSummary,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min)
    end = start + timedelta(days=1)
    return start, end


@router.get("/sales-summary")
def get_todays_sales_summary(
    target_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    target_date = target_date or date.today()
    start, end = _day_bounds(target_date)
    revenue = db.scalar(
        select(func.coalesce(func.sum(Sale.total_amount), 0)).where(Sale.sold_at >= start, Sale.sold_at < end)
    )
    transactions = db.scalar(select(func.count(Sale.id)).where(Sale.sold_at >= start, Sale.sold_at < end)) or 0
    average = Decimal(revenue) / transactions if transactions else Decimal("0.00")
    data = SalesSummary(
        date=target_date,
        total_revenue=Decimal(revenue),
        transaction_count=transactions,
        average_order_value=average.quantize(Decimal("0.01")),
    )
    return {"success": True, "data": data}


@router.get("/items-sold")
def get_total_items_sold(
    target_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    target_date = target_date or date.today()
    start, end = _day_bounds(target_date)
    total_items = db.scalar(
        select(func.coalesce(func.sum(Sale.quantity), 0)).where(Sale.sold_at >= start, Sale.sold_at < end)
    )
    data = ItemsSoldSummary(date=target_date, total_items_sold=int(total_items or 0))
    return {"success": True, "data": data}


@router.get("/low-stock")
def get_low_stock_items(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    low_stock_filter = Medicine.status.in_([MedicineStatus.LOW_STOCK, MedicineStatus.OUT_OF_STOCK])
    total_low_stock = db.scalar(select(func.count(Medicine.id)).where(low_stock_filter)) or 0
    stmt = (
        select(Medicine)
        .where(low_stock_filter)
        .order_by(Medicine.stock_quantity.asc(), Medicine.name.asc())
        .limit(limit)
    )
    items = db.scalars(stmt).all()
    data = LowStockSummary(low_stock_count=total_low_stock, items=items)
    return {"success": True, "data": data}


@router.get("/purchase-orders")
def get_purchase_order_summary(db: Session = Depends(get_db)):
    total_orders = db.scalar(select(func.count(PurchaseOrder.id))) or 0
    counts = db.execute(
        select(PurchaseOrder.status, func.count(PurchaseOrder.id)).group_by(PurchaseOrder.status)
    ).all()
    status_map = {status: count for status, count in counts}
    total_order_value = db.scalar(select(func.coalesce(func.sum(PurchaseOrder.total_amount), 0))) or 0
    data = PurchaseOrderSummary(
        total_orders=total_orders,
        pending_orders=status_map.get(PurchaseOrderStatus.PENDING, 0),
        completed_orders=status_map.get(PurchaseOrderStatus.COMPLETED, 0),
        cancelled_orders=status_map.get(PurchaseOrderStatus.CANCELLED, 0),
        total_order_value=Decimal(total_order_value),
    )
    return {"success": True, "data": data}


@router.get("/recent-sales")
def get_recent_sales(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Sale.id, Sale.medicine_id, Medicine.name, Sale.quantity, Sale.total_amount, Sale.sold_at)
        .join(Medicine, Medicine.id == Sale.medicine_id)
        .order_by(Sale.sold_at.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    sales = [
        RecentSale(
            id=row.id,
            medicine_id=row.medicine_id,
            medicine_name=row.name,
            quantity=row.quantity,
            total_amount=row.total_amount,
            sold_at=row.sold_at,
        )
        for row in rows
    ]
    data = RecentSalesSummary(sales=sales)
    return {"success": True, "data": data}
