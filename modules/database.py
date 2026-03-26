"""
SQLite database layer for the Luxury Hotel POS system.
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Optional

from modules.models import (
    Room, Guest, Reservation, Product, Order, OrderItem, Invoice, HotelSettings
)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hotel_pos.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database() -> None:
    """Create all tables and seed initial data if needed."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS rooms (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                number          TEXT NOT NULL UNIQUE,
                room_type       TEXT NOT NULL,
                price_per_night REAL NOT NULL,
                status          TEXT NOT NULL DEFAULT 'AVAILABLE',
                floor           INTEGER NOT NULL DEFAULT 1,
                description     TEXT DEFAULT '',
                amenities       TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS guests (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name      TEXT NOT NULL,
                last_name       TEXT NOT NULL,
                id_document     TEXT NOT NULL,
                document_type   TEXT NOT NULL DEFAULT 'PASSPORT',
                email           TEXT DEFAULT '',
                phone           TEXT DEFAULT '',
                nationality     TEXT DEFAULT '',
                address         TEXT DEFAULT '',
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reservations (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id         INTEGER NOT NULL REFERENCES rooms(id),
                guest_id        INTEGER NOT NULL REFERENCES guests(id),
                check_in        TEXT NOT NULL,
                check_out       TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'CONFIRMED',
                adults          INTEGER NOT NULL DEFAULT 1,
                children        INTEGER NOT NULL DEFAULT 0,
                notes           TEXT DEFAULT '',
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                category    TEXT NOT NULL,
                price       REAL NOT NULL,
                description TEXT DEFAULT '',
                stock       INTEGER NOT NULL DEFAULT 0,
                unit        TEXT NOT NULL DEFAULT 'unit',
                active      INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS orders (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                reservation_id  INTEGER REFERENCES reservations(id),
                room_id         INTEGER REFERENCES rooms(id),
                order_type      TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'OPEN',
                total           REAL NOT NULL DEFAULT 0,
                notes           TEXT DEFAULT '',
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id    INTEGER NOT NULL REFERENCES orders(id),
                product_id  INTEGER NOT NULL REFERENCES products(id),
                quantity    INTEGER NOT NULL,
                unit_price  REAL NOT NULL,
                subtotal    REAL NOT NULL,
                notes       TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                reservation_id  INTEGER NOT NULL REFERENCES reservations(id),
                folio_number    TEXT NOT NULL UNIQUE,
                subtotal        REAL NOT NULL,
                tax_rate        REAL NOT NULL,
                tax_amount      REAL NOT NULL,
                discount        REAL NOT NULL DEFAULT 0,
                total           REAL NOT NULL,
                payment_method  TEXT NOT NULL,
                payment_status  TEXT NOT NULL DEFAULT 'PENDING',
                notes           TEXT DEFAULT '',
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key     TEXT PRIMARY KEY,
                value   TEXT NOT NULL
            );
        """)
        _seed_settings(conn)
        _seed_sample_data(conn)


def _seed_settings(conn: sqlite3.Connection) -> None:
    defaults = {
        "hotel_name": "Hotel de Lujo",
        "address": "Av. Reforma 100, Ciudad de México",
        "phone": "+52 55 1234 5678",
        "email": "contacto@hoteldelujo.mx",
        "website": "www.hoteldelujo.mx",
        "tax_rate": "16.0",
        "currency": "MXN",
        "currency_symbol": "$",
        "logo_path": "",
        "check_in_time": "14:00",
        "check_out_time": "12:00",
        "invoice_footer": "Gracias por su preferencia. ¡Esperamos verle pronto!",
    }
    for key, value in defaults.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )


def _seed_sample_data(conn: sqlite3.Connection) -> None:
    """Insert demo rooms and products only if the tables are empty."""
    if conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 0:
        rooms = [
            ("101", "SINGLE",      1800.0, 1),
            ("102", "SINGLE",      1800.0, 1),
            ("201", "DOUBLE",      2800.0, 2),
            ("202", "DOUBLE",      2800.0, 2),
            ("301", "SUITE",       5500.0, 3),
            ("302", "SUITE",       5500.0, 3),
            ("401", "PRESIDENTIAL",12000.0, 4),
        ]
        conn.executemany(
            "INSERT INTO rooms (number, room_type, price_per_night, floor) VALUES (?,?,?,?)",
            rooms,
        )

    if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        products = [
            ("Agua Mineral",       "BEVERAGE",  45.0),
            ("Jugo de Naranja",    "BEVERAGE",  80.0),
            ("Café Americano",     "BEVERAGE",  70.0),
            ("Copa de Vino Tinto", "BEVERAGE", 180.0),
            ("Cerveza Importada",  "BEVERAGE", 120.0),
            ("Desayuno Continental","FOOD",    250.0),
            ("Club Sandwich",      "FOOD",     180.0),
            ("Ensalada Caesar",    "FOOD",     160.0),
            ("Filete de Res",      "FOOD",     480.0),
            ("Botana Surtida",     "FOOD",     220.0),
            ("Masaje Relajante 60min","SPA",   900.0),
            ("Facial Hidratante",  "SPA",      750.0),
            ("Lavado y Planchado", "LAUNDRY",  150.0),
            ("Servicio Express",   "LAUNDRY",  250.0),
            ("Chocolates Finos",   "MINIBAR",   95.0),
            ("Snack Mixto",        "MINIBAR",   75.0),
        ]
        conn.executemany(
            "INSERT INTO products (name, category, price) VALUES (?,?,?)",
            products,
        )


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def load_settings() -> HotelSettings:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    data = {r["key"]: r["value"] for r in rows}
    return HotelSettings(
        hotel_name=data.get("hotel_name", "Hotel de Lujo"),
        address=data.get("address", ""),
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        website=data.get("website", ""),
        tax_rate=float(data.get("tax_rate", "16.0")),
        currency=data.get("currency", "MXN"),
        currency_symbol=data.get("currency_symbol", "$"),
        logo_path=data.get("logo_path", ""),
        check_in_time=data.get("check_in_time", "14:00"),
        check_out_time=data.get("check_out_time", "12:00"),
        invoice_footer=data.get("invoice_footer", ""),
    )


def save_settings(settings: HotelSettings) -> None:
    data = {
        "hotel_name": settings.hotel_name,
        "address": settings.address,
        "phone": settings.phone,
        "email": settings.email,
        "website": settings.website,
        "tax_rate": str(settings.tax_rate),
        "currency": settings.currency,
        "currency_symbol": settings.currency_symbol,
        "logo_path": settings.logo_path,
        "check_in_time": settings.check_in_time,
        "check_out_time": settings.check_out_time,
        "invoice_footer": settings.invoice_footer,
    }
    with get_connection() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            list(data.items()),
        )


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

def get_all_rooms() -> List[Room]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM rooms ORDER BY number").fetchall()
    return [_row_to_room(r) for r in rows]


def get_room(room_id: int) -> Optional[Room]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM rooms WHERE id=?", (room_id,)).fetchone()
    return _row_to_room(row) if row else None


def save_room(room: Room) -> Room:
    with get_connection() as conn:
        if room.id == 0:
            cur = conn.execute(
                "INSERT INTO rooms (number,room_type,price_per_night,status,floor,description,amenities) VALUES (?,?,?,?,?,?,?)",
                (room.number, room.room_type, room.price_per_night, room.status, room.floor, room.description, room.amenities),
            )
            room.id = cur.lastrowid
        else:
            conn.execute(
                "UPDATE rooms SET number=?,room_type=?,price_per_night=?,status=?,floor=?,description=?,amenities=? WHERE id=?",
                (room.number, room.room_type, room.price_per_night, room.status, room.floor, room.description, room.amenities, room.id),
            )
    return room


def update_room_status(room_id: int, status: str, conn: sqlite3.Connection = None) -> None:
    if conn is not None:
        conn.execute("UPDATE rooms SET status=? WHERE id=?", (status, room_id))
    else:
        with get_connection() as c:
            c.execute("UPDATE rooms SET status=? WHERE id=?", (status, room_id))


def _row_to_room(row) -> Room:
    return Room(
        id=row["id"], number=row["number"], room_type=row["room_type"],
        price_per_night=row["price_per_night"], status=row["status"],
        floor=row["floor"], description=row["description"] or "",
        amenities=row["amenities"] or "",
    )


# ---------------------------------------------------------------------------
# Guests
# ---------------------------------------------------------------------------

def get_all_guests() -> List[Guest]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM guests ORDER BY last_name, first_name").fetchall()
    return [_row_to_guest(r) for r in rows]


def search_guests(query: str) -> List[Guest]:
    q = f"%{query}%"
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM guests WHERE first_name LIKE ? OR last_name LIKE ? OR id_document LIKE ? ORDER BY last_name",
            (q, q, q),
        ).fetchall()
    return [_row_to_guest(r) for r in rows]


def save_guest(guest: Guest) -> Guest:
    with get_connection() as conn:
        if guest.id == 0:
            cur = conn.execute(
                "INSERT INTO guests (first_name,last_name,id_document,document_type,email,phone,nationality,address,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (guest.first_name, guest.last_name, guest.id_document, guest.document_type,
                 guest.email, guest.phone, guest.nationality, guest.address, guest.created_at),
            )
            guest.id = cur.lastrowid
        else:
            conn.execute(
                "UPDATE guests SET first_name=?,last_name=?,id_document=?,document_type=?,email=?,phone=?,nationality=?,address=? WHERE id=?",
                (guest.first_name, guest.last_name, guest.id_document, guest.document_type,
                 guest.email, guest.phone, guest.nationality, guest.address, guest.id),
            )
    return guest


def _row_to_guest(row) -> Guest:
    return Guest(
        id=row["id"], first_name=row["first_name"], last_name=row["last_name"],
        id_document=row["id_document"], document_type=row["document_type"],
        email=row["email"] or "", phone=row["phone"] or "",
        nationality=row["nationality"] or "", address=row["address"] or "",
        created_at=row["created_at"],
    )


# ---------------------------------------------------------------------------
# Reservations
# ---------------------------------------------------------------------------

def get_all_reservations(status_filter: Optional[str] = None) -> List[Reservation]:
    sql = """
        SELECT r.*, rm.number AS room_number, rm.room_type, rm.price_per_night,
               (g.first_name || ' ' || g.last_name) AS guest_name
        FROM reservations r
        JOIN rooms rm ON rm.id = r.room_id
        JOIN guests g ON g.id = r.guest_id
    """
    params: tuple = ()
    if status_filter:
        sql += " WHERE r.status = ?"
        params = (status_filter,)
    sql += " ORDER BY r.check_in DESC"
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_reservation(r) for r in rows]


def get_reservation(reservation_id: int) -> Optional[Reservation]:
    sql = """
        SELECT r.*, rm.number AS room_number, rm.room_type, rm.price_per_night,
               (g.first_name || ' ' || g.last_name) AS guest_name
        FROM reservations r
        JOIN rooms rm ON rm.id = r.room_id
        JOIN guests g ON g.id = r.guest_id
        WHERE r.id = ?
    """
    with get_connection() as conn:
        row = conn.execute(sql, (reservation_id,)).fetchone()
    return _row_to_reservation(row) if row else None


def save_reservation(res: Reservation) -> Reservation:
    with get_connection() as conn:
        if res.id == 0:
            cur = conn.execute(
                "INSERT INTO reservations (room_id,guest_id,check_in,check_out,status,adults,children,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (res.room_id, res.guest_id, res.check_in, res.check_out, res.status, res.adults, res.children, res.notes, res.created_at),
            )
            res.id = cur.lastrowid
            update_room_status(res.room_id, "RESERVED", conn)
        else:
            conn.execute(
                "UPDATE reservations SET room_id=?,guest_id=?,check_in=?,check_out=?,status=?,adults=?,children=?,notes=? WHERE id=?",
                (res.room_id, res.guest_id, res.check_in, res.check_out, res.status, res.adults, res.children, res.notes, res.id),
            )
    return res


def _row_to_reservation(row) -> Reservation:
    return Reservation(
        id=row["id"], room_id=row["room_id"], guest_id=row["guest_id"],
        check_in=row["check_in"], check_out=row["check_out"],
        status=row["status"], adults=row["adults"], children=row["children"],
        notes=row["notes"] or "", created_at=row["created_at"],
        room_number=row["room_number"], room_type=row["room_type"],
        price_per_night=row["price_per_night"], guest_name=row["guest_name"],
    )


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def get_all_products(category: Optional[str] = None) -> List[Product]:
    if category:
        sql = "SELECT * FROM products WHERE active=1 AND category=? ORDER BY name"
        params: tuple = (category,)
    else:
        sql = "SELECT * FROM products WHERE active=1 ORDER BY category, name"
        params = ()
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_product(r) for r in rows]


def save_product(product: Product) -> Product:
    with get_connection() as conn:
        if product.id == 0:
            cur = conn.execute(
                "INSERT INTO products (name,category,price,description,stock,unit,active) VALUES (?,?,?,?,?,?,?)",
                (product.name, product.category, product.price, product.description, product.stock, product.unit, int(product.active)),
            )
            product.id = cur.lastrowid
        else:
            conn.execute(
                "UPDATE products SET name=?,category=?,price=?,description=?,stock=?,unit=?,active=? WHERE id=?",
                (product.name, product.category, product.price, product.description, product.stock, product.unit, int(product.active), product.id),
            )
    return product


def _row_to_product(row) -> Product:
    return Product(
        id=row["id"], name=row["name"], category=row["category"],
        price=row["price"], description=row["description"] or "",
        stock=row["stock"], unit=row["unit"], active=bool(row["active"]),
    )


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

def get_orders(status: Optional[str] = None, reservation_id: Optional[int] = None) -> List[Order]:
    sql = """
        SELECT o.*, rm.number AS room_number,
               COALESCE((g.first_name || ' ' || g.last_name), '') AS guest_name
        FROM orders o
        LEFT JOIN rooms rm ON rm.id = o.room_id
        LEFT JOIN reservations res ON res.id = o.reservation_id
        LEFT JOIN guests g ON g.id = res.guest_id
        WHERE 1=1
    """
    params: list = []
    if status:
        sql += " AND o.status = ?"
        params.append(status)
    if reservation_id:
        sql += " AND o.reservation_id = ?"
        params.append(reservation_id)
    sql += " ORDER BY o.created_at DESC"
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_order(r) for r in rows]


def get_order(order_id: int) -> Optional[Order]:
    sql = """
        SELECT o.*, rm.number AS room_number,
               COALESCE((g.first_name || ' ' || g.last_name), '') AS guest_name
        FROM orders o
        LEFT JOIN rooms rm ON rm.id = o.room_id
        LEFT JOIN reservations res ON res.id = o.reservation_id
        LEFT JOIN guests g ON g.id = res.guest_id
        WHERE o.id = ?
    """
    with get_connection() as conn:
        row = conn.execute(sql, (order_id,)).fetchone()
        if not row:
            return None
        order = _row_to_order(row)
        items = conn.execute(
            "SELECT oi.*, p.name AS product_name FROM order_items oi JOIN products p ON p.id=oi.product_id WHERE oi.order_id=?",
            (order_id,),
        ).fetchall()
    order.items = [_row_to_order_item(i) for i in items]
    return order


def save_order(order: Order) -> Order:
    with get_connection() as conn:
        if order.id == 0:
            cur = conn.execute(
                "INSERT INTO orders (reservation_id,room_id,order_type,status,total,notes,created_at) VALUES (?,?,?,?,?,?,?)",
                (order.reservation_id, order.room_id, order.order_type, order.status, order.total, order.notes, order.created_at),
            )
            order.id = cur.lastrowid
        else:
            conn.execute(
                "UPDATE orders SET reservation_id=?,room_id=?,order_type=?,status=?,total=?,notes=? WHERE id=?",
                (order.reservation_id, order.room_id, order.order_type, order.status, order.total, order.notes, order.id),
            )
        # Replace items
        conn.execute("DELETE FROM order_items WHERE order_id=?", (order.id,))
        for item in order.items:
            item.order_id = order.id
            cur2 = conn.execute(
                "INSERT INTO order_items (order_id,product_id,quantity,unit_price,subtotal,notes) VALUES (?,?,?,?,?,?)",
                (item.order_id, item.product_id, item.quantity, item.unit_price, item.subtotal, item.notes),
            )
            item.id = cur2.lastrowid
    return order


def _row_to_order(row) -> Order:
    return Order(
        id=row["id"], reservation_id=row["reservation_id"],
        room_id=row["room_id"], order_type=row["order_type"],
        status=row["status"], total=row["total"],
        notes=row["notes"] or "", created_at=row["created_at"],
        room_number=row["room_number"] or "", guest_name=row["guest_name"] or "",
    )


def _row_to_order_item(row) -> OrderItem:
    return OrderItem(
        id=row["id"], order_id=row["order_id"], product_id=row["product_id"],
        quantity=row["quantity"], unit_price=row["unit_price"],
        subtotal=row["subtotal"], notes=row["notes"] or "",
        product_name=row["product_name"],
    )


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------

def _next_folio() -> str:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
    return f"F{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"


def save_invoice(invoice: Invoice) -> Invoice:
    if not invoice.folio_number:
        invoice.folio_number = _next_folio()
    if not invoice.created_at:
        invoice.created_at = datetime.now().isoformat()
    with get_connection() as conn:
        if invoice.id == 0:
            cur = conn.execute(
                "INSERT INTO invoices (reservation_id,folio_number,subtotal,tax_rate,tax_amount,discount,total,payment_method,payment_status,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (invoice.reservation_id, invoice.folio_number, invoice.subtotal, invoice.tax_rate,
                 invoice.tax_amount, invoice.discount, invoice.total, invoice.payment_method,
                 invoice.payment_status, invoice.notes, invoice.created_at),
            )
            invoice.id = cur.lastrowid
        else:
            conn.execute(
                "UPDATE invoices SET payment_status=?,notes=? WHERE id=?",
                (invoice.payment_status, invoice.notes, invoice.id),
            )
    return invoice


def get_invoices() -> List[Invoice]:
    sql = """
        SELECT inv.*, (g.first_name || ' ' || g.last_name) AS guest_name, rm.number AS room_number
        FROM invoices inv
        JOIN reservations res ON res.id = inv.reservation_id
        JOIN guests g ON g.id = res.guest_id
        JOIN rooms rm ON rm.id = res.room_id
        ORDER BY inv.created_at DESC
    """
    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
    return [_row_to_invoice(r) for r in rows]


def get_invoice(invoice_id: int) -> Optional[Invoice]:
    sql = """
        SELECT inv.*, (g.first_name || ' ' || g.last_name) AS guest_name, rm.number AS room_number
        FROM invoices inv
        JOIN reservations res ON res.id = inv.reservation_id
        JOIN guests g ON g.id = res.guest_id
        JOIN rooms rm ON rm.id = res.room_id
        WHERE inv.id = ?
    """
    with get_connection() as conn:
        row = conn.execute(sql, (invoice_id,)).fetchone()
    return _row_to_invoice(row) if row else None


def _row_to_invoice(row) -> Invoice:
    return Invoice(
        id=row["id"], reservation_id=row["reservation_id"],
        folio_number=row["folio_number"], subtotal=row["subtotal"],
        tax_rate=row["tax_rate"], tax_amount=row["tax_amount"],
        discount=row["discount"], total=row["total"],
        payment_method=row["payment_method"], payment_status=row["payment_status"],
        notes=row["notes"] or "", created_at=row["created_at"],
        guest_name=row["guest_name"], room_number=row["room_number"],
    )


# ---------------------------------------------------------------------------
# Reports helpers
# ---------------------------------------------------------------------------

def report_revenue(start_date: str, end_date: str) -> dict:
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COALESCE(SUM(total),0) FROM invoices WHERE payment_status='PAID' AND replace(created_at,'T',' ') BETWEEN ? AND ?",
            (start_date, end_date + " 23:59:59"),
        ).fetchone()[0]
        count = conn.execute(
            "SELECT COUNT(*) FROM invoices WHERE payment_status='PAID' AND replace(created_at,'T',' ') BETWEEN ? AND ?",
            (start_date, end_date + " 23:59:59"),
        ).fetchone()[0]
        by_method = conn.execute(
            "SELECT payment_method, COALESCE(SUM(total),0) AS amount FROM invoices WHERE payment_status='PAID' AND replace(created_at,'T',' ') BETWEEN ? AND ? GROUP BY payment_method",
            (start_date, end_date + " 23:59:59"),
        ).fetchall()
    return {
        "total": total,
        "count": count,
        "by_method": {r["payment_method"]: r["amount"] for r in by_method},
    }


def report_occupancy() -> dict:
    with get_connection() as conn:
        total_rooms = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
        occupied = conn.execute("SELECT COUNT(*) FROM rooms WHERE status='OCCUPIED'").fetchone()[0]
        reserved = conn.execute("SELECT COUNT(*) FROM rooms WHERE status='RESERVED'").fetchone()[0]
        available = conn.execute("SELECT COUNT(*) FROM rooms WHERE status='AVAILABLE'").fetchone()[0]
        maintenance = conn.execute("SELECT COUNT(*) FROM rooms WHERE status='MAINTENANCE'").fetchone()[0]
    return {
        "total": total_rooms,
        "occupied": occupied,
        "reserved": reserved,
        "available": available,
        "maintenance": maintenance,
        "occupancy_rate": round((occupied / total_rooms * 100) if total_rooms else 0, 1),
    }
