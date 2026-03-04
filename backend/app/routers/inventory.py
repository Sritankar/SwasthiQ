from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Medicine, MedicineStatus
from app.schemas import (
    InventorySummary,
    MedicineCreate,
    MedicineOut,
    MedicineUpdate,
    PaginatedMedicines,
    StatusUpdateRequest,
)
from app.services import apply_status_transition, build_medicine_from_payload, derive_medicine_status

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/summary")
def get_inventory_summary(db: Session = Depends(get_db)):
    total_medicines = db.scalar(select(func.count(Medicine.id))) or 0
    grouped_statuses = db.execute(select(Medicine.status, func.count(Medicine.id)).group_by(Medicine.status)).all()
    status_count_map = {status_key: count for status_key, count in grouped_statuses}
    total_stock_units = db.scalar(select(func.coalesce(func.sum(Medicine.stock_quantity), 0))) or 0
    inventory_value = db.scalar(
        select(func.coalesce(func.sum(Medicine.unit_price * Medicine.stock_quantity), 0))
    ) or Decimal("0")

    payload = InventorySummary(
        total_medicines=total_medicines,
        active_count=status_count_map.get(MedicineStatus.ACTIVE, 0),
        low_stock_count=status_count_map.get(MedicineStatus.LOW_STOCK, 0),
        expired_count=status_count_map.get(MedicineStatus.EXPIRED, 0),
        out_of_stock_count=status_count_map.get(MedicineStatus.OUT_OF_STOCK, 0),
        total_stock_units=total_stock_units,
        inventory_value=Decimal(inventory_value),
    )
    return {"success": True, "data": payload}


@router.get("/medicines")
def list_medicines(
    q: str | None = Query(default=None, min_length=1, max_length=120),
    category: str | None = Query(default=None, min_length=2, max_length=80),
    status_filter: MedicineStatus | None = Query(default=None, alias="status"),
    low_stock: bool | None = Query(default=None),
    expired: bool | None = Query(default=None),
    out_of_stock: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    filters = []
    if q:
        term = f"%{q.strip()}%"
        filters.append(
            or_(
                Medicine.name.ilike(term),
                Medicine.generic_name.ilike(term),
                Medicine.category.ilike(term),
                Medicine.batch_number.ilike(term),
                Medicine.manufacturer.ilike(term),
            )
        )

    if category:
        filters.append(Medicine.category.ilike(category.strip()))

    if status_filter:
        filters.append(Medicine.status == status_filter)

    if low_stock is not None:
        low_stock_filter = and_(Medicine.stock_quantity > 0, Medicine.stock_quantity <= Medicine.reorder_level)
        filters.append(low_stock_filter if low_stock else ~low_stock_filter)

    if expired is not None:
        expired_filter = Medicine.expiry_date < date.today()
        filters.append(expired_filter if expired else ~expired_filter)

    if out_of_stock is not None:
        out_of_stock_filter = Medicine.stock_quantity <= 0
        filters.append(out_of_stock_filter if out_of_stock else ~out_of_stock_filter)

    stmt = select(Medicine)
    if filters:
        stmt = stmt.where(*filters)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Medicine.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    payload = PaginatedMedicines(items=rows, total=total, page=page, page_size=page_size)
    return {"success": True, "data": payload}


@router.get("/medicines/{medicine_id}")
def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    medicine = db.get(Medicine, medicine_id)
    if not medicine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
    return {"success": True, "data": MedicineOut.model_validate(medicine)}


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    categories = db.scalars(select(Medicine.category).distinct().order_by(Medicine.category.asc())).all()
    return {"success": True, "data": categories}


@router.post("/medicines", status_code=status.HTTP_201_CREATED)
def create_medicine(payload: MedicineCreate, db: Session = Depends(get_db)):
    duplicate_batch = db.scalar(select(Medicine.id).where(Medicine.batch_number == payload.batch_number.strip()))
    if duplicate_batch:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Medicine with this batch number already exists",
        )

    medicine = build_medicine_from_payload(payload)
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    return {"success": True, "data": MedicineOut.model_validate(medicine)}


@router.put("/medicines/{medicine_id}")
def update_medicine(medicine_id: int, payload: MedicineUpdate, db: Session = Depends(get_db)):
    medicine = db.get(Medicine, medicine_id)
    if not medicine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")

    if "batch_number" in update_data:
        duplicate_batch = db.scalar(
            select(Medicine.id).where(
                Medicine.batch_number == update_data["batch_number"].strip(),
                Medicine.id != medicine_id,
            )
        )
        if duplicate_batch:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Medicine with this batch number already exists",
            )

    for field, value in update_data.items():
        if isinstance(value, str):
            setattr(medicine, field, value.strip())
        else:
            setattr(medicine, field, value)

    medicine.status = derive_medicine_status(
        expiry_date=medicine.expiry_date,
        stock_quantity=medicine.stock_quantity,
        reorder_level=medicine.reorder_level,
    )
    db.commit()
    db.refresh(medicine)
    return {"success": True, "data": MedicineOut.model_validate(medicine)}


@router.patch("/medicines/{medicine_id}/status")
def mark_medicine_status(medicine_id: int, payload: StatusUpdateRequest, db: Session = Depends(get_db)):
    medicine = db.get(Medicine, medicine_id)
    if not medicine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")

    apply_status_transition(medicine, MedicineStatus(payload.status))
    db.commit()
    db.refresh(medicine)
    return {"success": True, "data": MedicineOut.model_validate(medicine)}

