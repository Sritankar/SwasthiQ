from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Medicine, MedicineStatus, PatientSaleRecord, Sale
from app.schemas import PaginatedPatientSaleRecords, PatientSaleCreate, PatientSaleRecordOut
from app.services import derive_medicine_status

router = APIRouter(prefix="/api/patient-sales", tags=["patient-sales"])


def _to_record_out(record: PatientSaleRecord, medicine_name: str) -> PatientSaleRecordOut:
    return PatientSaleRecordOut(
        id=record.id,
        sale_id=record.sale_id,
        patient_id=record.patient_id,
        patient_name=record.patient_name,
        medicine_id=record.medicine_id,
        medicine_name=medicine_name,
        quantity=record.quantity,
        unit_price=record.unit_price,
        total_amount=record.total_amount,
        dosage_instructions=record.dosage_instructions,
        notes=record.notes,
        sold_at=record.sold_at,
        created_at=record.created_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_patient_sale(payload: PatientSaleCreate, db: Session = Depends(get_db)):
    medicine = db.get(Medicine, payload.medicine_id)
    if not medicine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")

    today = date.today()
    if medicine.expiry_date < today:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot sell expired medicine")

    if medicine.stock_quantity <= 0 or medicine.status == MedicineStatus.OUT_OF_STOCK:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Medicine is out of stock")

    if medicine.stock_quantity < payload.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock for this sale")

    sold_at = datetime.utcnow()
    unit_price = Decimal(medicine.unit_price)
    total_amount = (unit_price * payload.quantity).quantize(Decimal("0.01"))

    sale = Sale(
        medicine_id=medicine.id,
        quantity=payload.quantity,
        total_amount=total_amount,
        sold_at=sold_at,
    )
    db.add(sale)
    db.flush()

    record = PatientSaleRecord(
        sale_id=sale.id,
        patient_id=payload.patient_id.strip(),
        patient_name=payload.patient_name.strip() if payload.patient_name else None,
        medicine_id=medicine.id,
        quantity=payload.quantity,
        unit_price=unit_price,
        total_amount=total_amount,
        dosage_instructions=payload.dosage_instructions.strip() if payload.dosage_instructions else None,
        notes=payload.notes.strip() if payload.notes else None,
        sold_at=sold_at,
    )
    db.add(record)

    medicine.stock_quantity -= payload.quantity
    medicine.status = derive_medicine_status(
        expiry_date=medicine.expiry_date,
        stock_quantity=medicine.stock_quantity,
        reorder_level=medicine.reorder_level,
    )

    db.commit()
    db.refresh(record)

    return {"success": True, "data": _to_record_out(record, medicine.name)}


@router.get("")
def list_patient_sales(
    q: str | None = Query(default=None, min_length=1, max_length=120),
    patient_id: str | None = Query(default=None, min_length=1, max_length=64),
    medicine_id: int | None = Query(default=None, ge=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(PatientSaleRecord, Medicine.name).join(Medicine, Medicine.id == PatientSaleRecord.medicine_id)
    filters = []

    if q:
        term = f"%{q.strip()}%"
        filters.append(
            or_(
                PatientSaleRecord.patient_id.ilike(term),
                PatientSaleRecord.patient_name.ilike(term),
                Medicine.name.ilike(term),
            )
        )

    if patient_id:
        filters.append(PatientSaleRecord.patient_id.ilike(patient_id.strip()))

    if medicine_id:
        filters.append(PatientSaleRecord.medicine_id == medicine_id)

    if filters:
        stmt = stmt.where(*filters)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        stmt.order_by(PatientSaleRecord.sold_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    items = [_to_record_out(row[0], row[1]) for row in rows]
    payload = PaginatedPatientSaleRecords(items=items, total=total, page=page, page_size=page_size)
    return {"success": True, "data": payload}


@router.get("/patients/{patient_id}/records")
def get_patient_medicine_records(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = (
        select(PatientSaleRecord, Medicine.name)
        .join(Medicine, Medicine.id == PatientSaleRecord.medicine_id)
        .where(PatientSaleRecord.patient_id == patient_id.strip())
        .order_by(PatientSaleRecord.sold_at.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    items = [_to_record_out(row[0], row[1]) for row in rows]
    return {"success": True, "data": items}

