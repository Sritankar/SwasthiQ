from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Medicine, PurchaseOrder, PurchaseOrderStatus, Sale
from app.schemas import MedicineCreate
from app.services import build_medicine_from_payload


def seed_database(db: Session) -> None:
    has_records = db.scalar(select(Medicine.id).limit(1))
    if has_records:
        return

    today = date.today()
    medicines_payload = [
        {
            "name": "Paracetamol 650",
            "generic_name": "Acetaminophen",
            "category": "Pain Relief",
            "manufacturer": "HealWell Labs",
            "batch_number": "PARA650-A1",
            "unit_price": Decimal("3.50"),
            "stock_quantity": 220,
            "reorder_level": 50,
            "expiry_date": today + timedelta(days=370),
            "is_active": True,
        },
        {
            "name": "Amoxicillin 500",
            "generic_name": "Amoxicillin",
            "category": "Antibiotic",
            "manufacturer": "NexCure Pharma",
            "batch_number": "AMX500-B4",
            "unit_price": Decimal("7.90"),
            "stock_quantity": 18,
            "reorder_level": 25,
            "expiry_date": today + timedelta(days=280),
            "is_active": True,
        },
        {
            "name": "Cetirizine 10",
            "generic_name": "Cetirizine",
            "category": "Allergy",
            "manufacturer": "MediSphere",
            "batch_number": "CET10-C2",
            "unit_price": Decimal("4.10"),
            "stock_quantity": 0,
            "reorder_level": 20,
            "expiry_date": today + timedelta(days=210),
            "is_active": True,
        },
        {
            "name": "Metformin 500",
            "generic_name": "Metformin",
            "category": "Diabetes",
            "manufacturer": "VitalSync",
            "batch_number": "MET500-D9",
            "unit_price": Decimal("6.40"),
            "stock_quantity": 44,
            "reorder_level": 35,
            "expiry_date": today - timedelta(days=12),
            "is_active": True,
        },
        {
            "name": "Azithromycin 250",
            "generic_name": "Azithromycin",
            "category": "Antibiotic",
            "manufacturer": "HealWell Labs",
            "batch_number": "AZI250-E6",
            "unit_price": Decimal("11.25"),
            "stock_quantity": 76,
            "reorder_level": 30,
            "expiry_date": today + timedelta(days=400),
            "is_active": True,
        },
        {
            "name": "Omeprazole 20",
            "generic_name": "Omeprazole",
            "category": "Digestive",
            "manufacturer": "CoreMeds",
            "batch_number": "OME20-F7",
            "unit_price": Decimal("5.70"),
            "stock_quantity": 29,
            "reorder_level": 25,
            "expiry_date": today + timedelta(days=320),
            "is_active": True,
        },
    ]

    medicines = []
    for payload in medicines_payload:
        medicine = build_medicine_from_payload(payload=MedicineCreate(**payload))
        medicines.append(medicine)
    db.add_all(medicines)
    db.flush()

    sales = [
        Sale(
            medicine_id=medicines[0].id,
            quantity=18,
            total_amount=Decimal("63.00"),
            sold_at=datetime.utcnow() - timedelta(hours=1, minutes=30),
        ),
        Sale(
            medicine_id=medicines[1].id,
            quantity=8,
            total_amount=Decimal("63.20"),
            sold_at=datetime.utcnow() - timedelta(hours=3),
        ),
        Sale(
            medicine_id=medicines[4].id,
            quantity=5,
            total_amount=Decimal("56.25"),
            sold_at=datetime.utcnow() - timedelta(hours=5),
        ),
        Sale(
            medicine_id=medicines[5].id,
            quantity=9,
            total_amount=Decimal("51.30"),
            sold_at=datetime.utcnow() - timedelta(hours=8),
        ),
        Sale(
            medicine_id=medicines[0].id,
            quantity=13,
            total_amount=Decimal("45.50"),
            sold_at=datetime.utcnow() - timedelta(days=1, hours=2),
        ),
    ]
    db.add_all(sales)

    purchase_orders = [
        PurchaseOrder(
            vendor_name="Zenline Distributors",
            items_count=4,
            total_amount=Decimal("560.00"),
            status=PurchaseOrderStatus.PENDING,
            expected_delivery=today + timedelta(days=2),
        ),
        PurchaseOrder(
            vendor_name="OmniMed Supply",
            items_count=6,
            total_amount=Decimal("1240.50"),
            status=PurchaseOrderStatus.COMPLETED,
            expected_delivery=today - timedelta(days=1),
        ),
        PurchaseOrder(
            vendor_name="PrimeCare Wholesale",
            items_count=2,
            total_amount=Decimal("310.75"),
            status=PurchaseOrderStatus.CANCELLED,
            expected_delivery=None,
        ),
    ]
    db.add_all(purchase_orders)
    db.commit()
