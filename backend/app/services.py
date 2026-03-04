from datetime import date, timedelta
from decimal import Decimal

from app.models import Medicine, MedicineStatus
from app.schemas import MedicineCreate


def derive_medicine_status(expiry_date: date, stock_quantity: int, reorder_level: int) -> MedicineStatus:
    today = date.today()
    if expiry_date < today:
        return MedicineStatus.EXPIRED
    if stock_quantity <= 0:
        return MedicineStatus.OUT_OF_STOCK
    if stock_quantity <= reorder_level:
        return MedicineStatus.LOW_STOCK
    return MedicineStatus.ACTIVE


def apply_status_transition(medicine: Medicine, target_status: MedicineStatus) -> None:
    today = date.today()
    if target_status == MedicineStatus.EXPIRED and medicine.expiry_date >= today:
        medicine.expiry_date = today - timedelta(days=1)

    if target_status == MedicineStatus.OUT_OF_STOCK:
        medicine.stock_quantity = 0

    if target_status == MedicineStatus.LOW_STOCK:
        medicine.reorder_level = max(medicine.reorder_level, 1)
        if medicine.stock_quantity == 0:
            medicine.stock_quantity = medicine.reorder_level
        else:
            medicine.stock_quantity = min(medicine.stock_quantity, medicine.reorder_level)
        if medicine.expiry_date < today:
            medicine.expiry_date = today + timedelta(days=180)

    if target_status == MedicineStatus.ACTIVE:
        if medicine.expiry_date < today:
            medicine.expiry_date = today + timedelta(days=180)
        if medicine.stock_quantity <= medicine.reorder_level:
            medicine.stock_quantity = max(medicine.reorder_level + 1, 1)

    medicine.status = derive_medicine_status(
        expiry_date=medicine.expiry_date,
        stock_quantity=medicine.stock_quantity,
        reorder_level=medicine.reorder_level,
    )


def build_medicine_from_payload(payload: MedicineCreate) -> Medicine:
    status = derive_medicine_status(
        expiry_date=payload.expiry_date,
        stock_quantity=payload.stock_quantity,
        reorder_level=payload.reorder_level,
    )
    return Medicine(
        name=payload.name.strip(),
        generic_name=(payload.generic_name.strip() if payload.generic_name else None),
        category=payload.category.strip(),
        manufacturer=(payload.manufacturer.strip() if payload.manufacturer else None),
        batch_number=payload.batch_number.strip(),
        unit_price=Decimal(payload.unit_price),
        stock_quantity=payload.stock_quantity,
        reorder_level=payload.reorder_level,
        expiry_date=payload.expiry_date,
        status=status,
        is_active=payload.is_active,
    )

