from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Enum as SqlEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MedicineStatus(str, Enum):
    ACTIVE = "active"
    LOW_STOCK = "low_stock"
    EXPIRED = "expired"
    OUT_OF_STOCK = "out_of_stock"


class PurchaseOrderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    generic_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    category: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    batch_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[MedicineStatus] = mapped_column(SqlEnum(MedicineStatus), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    sales: Mapped[list[Sale]] = relationship("Sale", back_populates="medicine")
    patient_sale_records: Mapped[list[PatientSaleRecord]] = relationship(
        "PatientSaleRecord", back_populates="medicine"
    )


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    medicine_id: Mapped[int] = mapped_column(Integer, ForeignKey("medicines.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    sold_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    medicine: Mapped[Medicine] = relationship("Medicine", back_populates="sales")
    patient_sale_record: Mapped[PatientSaleRecord | None] = relationship(
        "PatientSaleRecord", back_populates="sale", uselist=False
    )


class PatientSaleRecord(Base):
    __tablename__ = "patient_sale_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sale_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales.id"), unique=True, index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    patient_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    medicine_id: Mapped[int] = mapped_column(Integer, ForeignKey("medicines.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    dosage_instructions: Mapped[str | None] = mapped_column(String(250), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sold_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    medicine: Mapped[Medicine] = relationship("Medicine", back_populates="patient_sale_records")
    sale: Mapped[Sale] = relationship("Sale", back_populates="patient_sale_record")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vendor_name: Mapped[str] = mapped_column(String(120), nullable=False)
    items_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PurchaseOrderStatus] = mapped_column(SqlEnum(PurchaseOrderStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expected_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)
