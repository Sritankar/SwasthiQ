from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import MedicineStatus, PurchaseOrderStatus


class MedicineBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    generic_name: str | None = Field(default=None, max_length=120)
    category: str = Field(..., min_length=2, max_length=80)
    manufacturer: str | None = Field(default=None, max_length=120)
    batch_number: str = Field(..., min_length=3, max_length=64)
    unit_price: Decimal = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)
    reorder_level: int = Field(..., ge=0)
    expiry_date: date
    is_active: bool = True


class MedicineCreate(MedicineBase):
    pass


class MedicineUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    generic_name: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, min_length=2, max_length=80)
    manufacturer: str | None = Field(default=None, max_length=120)
    batch_number: str | None = Field(default=None, min_length=3, max_length=64)
    unit_price: Decimal | None = Field(default=None, gt=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    expiry_date: date | None = None
    is_active: bool | None = None


class MedicineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    generic_name: str | None
    category: str
    manufacturer: str | None
    batch_number: str
    unit_price: Decimal
    stock_quantity: int
    reorder_level: int
    expiry_date: date
    status: MedicineStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime


class InventorySummary(BaseModel):
    total_medicines: int
    active_count: int
    low_stock_count: int
    expired_count: int
    out_of_stock_count: int
    total_stock_units: int
    inventory_value: Decimal


class PaginatedMedicines(BaseModel):
    items: list[MedicineOut]
    total: int
    page: int
    page_size: int


class SalesSummary(BaseModel):
    date: date
    total_revenue: Decimal
    transaction_count: int
    average_order_value: Decimal


class ItemsSoldSummary(BaseModel):
    date: date
    total_items_sold: int


class LowStockItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    stock_quantity: int
    reorder_level: int
    expiry_date: date
    status: MedicineStatus


class LowStockSummary(BaseModel):
    low_stock_count: int
    items: list[LowStockItem]


class PurchaseOrderSummary(BaseModel):
    total_orders: int
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    total_order_value: Decimal


class RecentSale(BaseModel):
    id: int
    medicine_id: int
    medicine_name: str
    quantity: int
    total_amount: Decimal
    sold_at: datetime


class RecentSalesSummary(BaseModel):
    sales: list[RecentSale]


class StatusUpdateRequest(BaseModel):
    status: Literal["active", "low_stock", "expired", "out_of_stock"]


class PurchaseOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vendor_name: str
    items_count: int
    total_amount: Decimal
    status: PurchaseOrderStatus
    created_at: datetime
    expected_delivery: date | None


class PatientSaleCreate(BaseModel):
    patient_id: str = Field(..., min_length=1, max_length=64)
    patient_name: str | None = Field(default=None, max_length=120)
    medicine_id: int = Field(..., ge=1)
    quantity: int = Field(..., ge=1)
    dosage_instructions: str | None = Field(default=None, max_length=250)
    notes: str | None = Field(default=None, max_length=500)


class PatientSaleRecordOut(BaseModel):
    id: int
    sale_id: int
    patient_id: str
    patient_name: str | None
    medicine_id: int
    medicine_name: str
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    dosage_instructions: str | None
    notes: str | None
    sold_at: datetime
    created_at: datetime


class PaginatedPatientSaleRecords(BaseModel):
    items: list[PatientSaleRecordOut]
    total: int
    page: int
    page_size: int
