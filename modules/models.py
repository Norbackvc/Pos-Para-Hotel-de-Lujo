"""
Data models for the Luxury Hotel POS system.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Room:
    id: int
    number: str
    room_type: str          # SINGLE, DOUBLE, SUITE, PRESIDENTIAL
    price_per_night: float
    status: str             # AVAILABLE, OCCUPIED, MAINTENANCE, RESERVED
    floor: int
    description: str = ""
    amenities: str = ""


@dataclass
class Guest:
    id: int
    first_name: str
    last_name: str
    id_document: str
    document_type: str      # PASSPORT, DNI, etc.
    email: str = ""
    phone: str = ""
    nationality: str = ""
    address: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class Reservation:
    id: int
    room_id: int
    guest_id: int
    check_in: str
    check_out: str
    status: str             # CONFIRMED, CHECKED_IN, CHECKED_OUT, CANCELLED
    adults: int = 1
    children: int = 0
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    # Populated from joins
    room_number: str = ""
    room_type: str = ""
    price_per_night: float = 0.0
    guest_name: str = ""


@dataclass
class Product:
    id: int
    name: str
    category: str           # FOOD, BEVERAGE, SPA, LAUNDRY, MINIBAR, OTHER
    price: float
    description: str = ""
    stock: int = 0
    unit: str = "unit"
    active: bool = True


@dataclass
class OrderItem:
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float
    notes: str = ""
    # Populated from joins
    product_name: str = ""


@dataclass
class Order:
    id: int
    reservation_id: Optional[int]
    room_id: Optional[int]
    order_type: str         # ROOM_SERVICE, RESTAURANT, BAR, SPA, LAUNDRY
    status: str             # OPEN, CLOSED, CANCELLED
    total: float = 0.0
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    items: List[OrderItem] = field(default_factory=list)
    # Populated from joins
    room_number: str = ""
    guest_name: str = ""


@dataclass
class Invoice:
    id: int
    reservation_id: int
    folio_number: str
    subtotal: float
    tax_rate: float
    tax_amount: float
    discount: float
    total: float
    payment_method: str     # CASH, CREDIT_CARD, DEBIT_CARD, TRANSFER, ROOM_CHARGE
    payment_status: str     # PENDING, PAID, CANCELLED
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    # Populated from joins
    guest_name: str = ""
    room_number: str = ""


@dataclass
class HotelSettings:
    hotel_name: str = "Hotel de Lujo"
    address: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    tax_rate: float = 16.0          # percentage
    currency: str = "MXN"
    currency_symbol: str = "$"
    logo_path: str = ""
    check_in_time: str = "14:00"
    check_out_time: str = "12:00"
    invoice_footer: str = "Gracias por su preferencia"
