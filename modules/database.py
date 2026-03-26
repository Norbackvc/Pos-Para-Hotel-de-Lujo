"""
Hotel POS - Módulo de base de datos (SQLite)
Gestiona todas las operaciones de base de datos del sistema.
"""

import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hotel_pos.db")


def get_connection():
    """Retorna una conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_db():
    """Crea todas las tablas necesarias si no existen e inserta datos iniciales."""
    conn = get_connection()
    cur = conn.cursor()

    # ── Configuración del hotel ──────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # ── Habitaciones ────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            number      TEXT    NOT NULL UNIQUE,
            type        TEXT    NOT NULL,
            capacity    INTEGER NOT NULL DEFAULT 2,
            price_night REAL    NOT NULL,
            status      TEXT    NOT NULL DEFAULT 'disponible',
            floor       INTEGER NOT NULL DEFAULT 1,
            description TEXT    DEFAULT ''
        )
    """)

    # ── Huéspedes ────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            id_number   TEXT    NOT NULL,
            email       TEXT    DEFAULT '',
            phone       TEXT    DEFAULT '',
            nationality TEXT    DEFAULT '',
            created_at  TEXT    NOT NULL
        )
    """)

    # ── Reservas ─────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id      INTEGER NOT NULL REFERENCES rooms(id),
            guest_id     INTEGER NOT NULL REFERENCES guests(id),
            checkin      TEXT    NOT NULL,
            checkout     TEXT,
            nights       INTEGER NOT NULL DEFAULT 1,
            total_room   REAL    NOT NULL DEFAULT 0,
            status       TEXT    NOT NULL DEFAULT 'activa',
            notes        TEXT    DEFAULT '',
            created_at   TEXT    NOT NULL
        )
    """)

    # ── Ítems de menú ────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            price       REAL    NOT NULL,
            description TEXT    DEFAULT '',
            available   INTEGER NOT NULL DEFAULT 1
        )
    """)

    # ── Servicios del hotel ──────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            price       REAL    NOT NULL,
            description TEXT    DEFAULT '',
            available   INTEGER NOT NULL DEFAULT 1
        )
    """)

    # ── Órdenes ──────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER REFERENCES reservations(id),
            guest_id       INTEGER REFERENCES guests(id),
            type           TEXT    NOT NULL,
            status         TEXT    NOT NULL DEFAULT 'abierta',
            subtotal       REAL    NOT NULL DEFAULT 0,
            tax            REAL    NOT NULL DEFAULT 0,
            total          REAL    NOT NULL DEFAULT 0,
            notes          TEXT    DEFAULT '',
            created_at     TEXT    NOT NULL,
            closed_at      TEXT
        )
    """)

    # ── Ítems de una orden ────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER NOT NULL REFERENCES orders(id),
            item_name   TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 1,
            unit_price  REAL    NOT NULL,
            subtotal    REAL    NOT NULL
        )
    """)

    # ── Facturas / Cobros ────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER REFERENCES reservations(id),
            guest_name     TEXT    NOT NULL,
            room_number    TEXT    NOT NULL,
            room_total     REAL    NOT NULL DEFAULT 0,
            services_total REAL    NOT NULL DEFAULT 0,
            subtotal       REAL    NOT NULL DEFAULT 0,
            tax            REAL    NOT NULL DEFAULT 0,
            total          REAL    NOT NULL DEFAULT 0,
            payment_method TEXT    NOT NULL DEFAULT 'efectivo',
            status         TEXT    NOT NULL DEFAULT 'pendiente',
            created_at     TEXT    NOT NULL,
            paid_at        TEXT
        )
    """)

    conn.commit()

    # ── Datos iniciales ──────────────────────────────────────────────────────
    _seed_config(cur)
    _seed_rooms(cur)
    _seed_menu(cur)
    _seed_services(cur)

    conn.commit()
    conn.close()


def _seed_config(cur):
    defaults = {
        "hotel_name": "Grand Luxe Hotel",
        "hotel_address": "Av. Principal 100, Ciudad",
        "hotel_phone": "+1 (555) 000-0000",
        "hotel_email": "info@grandluxe.com",
        "hotel_logo": "",
        "currency": "USD",
        "currency_symbol": "$",
        "tax_rate": "15",
        "theme": "dark",
    }
    for key, value in defaults.items():
        cur.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (key, value))


def _seed_rooms(cur):
    existing = cur.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
    if existing > 0:
        return
    rooms = [
        ("101", "Estándar",    2, 150.00, 1),
        ("102", "Estándar",    2, 150.00, 1),
        ("103", "Estándar",    2, 150.00, 1),
        ("201", "Deluxe",      2, 250.00, 2),
        ("202", "Deluxe",      2, 250.00, 2),
        ("203", "Deluxe",      3, 280.00, 2),
        ("301", "Suite",       4, 450.00, 3),
        ("302", "Suite",       4, 450.00, 3),
        ("401", "Suite Presidencial", 6, 900.00, 4),
        ("PH",  "Penthouse",   8, 1500.00, 5),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO rooms (number, type, capacity, price_night, floor) VALUES (?,?,?,?,?)",
        rooms,
    )


def _seed_menu(cur):
    existing = cur.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0]
    if existing > 0:
        return
    items = [
        # Desayunos
        ("Desayuno Americano",      "Desayunos",  25.00, "Huevos, tocino, tostadas, jugo"),
        ("Desayuno Continental",    "Desayunos",  18.00, "Croissant, mermelada, café"),
        ("Omelette de la Casa",     "Desayunos",  22.00, "Omelette con verduras y queso"),
        # Entradas
        ("Ceviche de Camarón",      "Entradas",   18.00, "Camarón fresco, limón, cilantro"),
        ("Carpaccio de Res",        "Entradas",   22.00, "Res marinada, alcaparras, parmesano"),
        ("Tabla de Quesos",         "Entradas",   28.00, "Selección de quesos premium"),
        # Platos Principales
        ("Filete Mignon",           "Principales",75.00, "Filete de res, salsa al vino"),
        ("Langosta Termidor",       "Principales",95.00, "Langosta fresca, mantequilla"),
        ("Salmón en Costra",        "Principales",65.00, "Salmón atlántico, hierbas"),
        ("Risotto de Trufa",        "Principales",55.00, "Arroz arbóreo, trufa negra"),
        # Postres
        ("Coulant de Chocolate",    "Postres",    18.00, "Bizcocho de chocolate caliente"),
        ("Crème Brûlée",            "Postres",    15.00, "Crema francesa caramelizada"),
        ("Selección de Helados",    "Postres",    12.00, "3 bolas de helado artesanal"),
        # Bebidas
        ("Agua Mineral",            "Bebidas",     5.00, "500ml"),
        ("Refresco",                "Bebidas",     6.00, "Lata 355ml"),
        ("Jugo Natural",            "Bebidas",     8.00, "Naranja, mango o piña"),
        ("Café Espresso",           "Bebidas",     6.00, "Doble ristretto"),
        ("Copa de Vino Tinto",      "Bebidas",    15.00, "Malbec reserva"),
        ("Copa de Champagne",       "Bebidas",    22.00, "Moet & Chandon"),
        # Bar
        ("Cocktail Signature",      "Bar",        18.00, "Creación exclusiva del bartender"),
        ("Whisky Premium",          "Bar",        25.00, "Single malt 12 años"),
        ("Gin Tonic",               "Bar",        16.00, "Hendricks, pepino, tónica"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO menu_items (name, category, price, description) VALUES (?,?,?,?)",
        items,
    )


def _seed_services(cur):
    existing = cur.execute("SELECT COUNT(*) FROM services").fetchone()[0]
    if existing > 0:
        return
    services = [
        # Spa
        ("Masaje Relajante 60 min",     "Spa",          120.00, "Masaje sueco de cuerpo completo"),
        ("Masaje de Piedras Calientes", "Spa",          150.00, "Terapia con piedras volcánicas"),
        ("Facial Hidratante",           "Spa",           90.00, "Tratamiento facial premium"),
        ("Circuito de Aguas",           "Spa",           60.00, "Acceso ilimitado hidromasaje"),
        # Lavandería
        ("Lavado y Planchado",          "Lavandería",    35.00, "Hasta 5 prendas"),
        ("Lavado Express",              "Lavandería",    50.00, "Entrega en 3 horas"),
        ("Tintorería Premium",          "Lavandería",    80.00, "Trajes y vestidos formales"),
        # Transporte
        ("Transfer Aeropuerto",         "Transporte",    85.00, "Ida o vuelta, vehículo de lujo"),
        ("Renta de Auto con Chofer",    "Transporte",   200.00, "Por día, Mercedes o similar"),
        ("Tour Ciudad VIP",             "Transporte",   150.00, "4 horas, guía privado"),
        # Habitación
        ("Room Service",                "Habitación",    15.00, "Cargo por servicio a habitación"),
        ("Despertador VIP",             "Habitación",    10.00, "Desayuno en cama incluido"),
        ("Decoración Romántica",        "Habitación",   120.00, "Pétalos, velas, champagne"),
        ("Amenidades Premium",          "Habitación",    45.00, "Kit de lujo para habitación"),
        # Eventos
        ("Sala de Reuniones",           "Eventos",      300.00, "Por día, capacidad 20 personas"),
        ("Salón de Eventos",            "Eventos",     1200.00, "Por día, capacidad 200 personas"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO services (name, category, price, description) VALUES (?,?,?,?)",
        services,
    )


# ── Helpers de configuración ─────────────────────────────────────────────────

def get_config(key: str) -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
        return row["value"] if row else ""


def set_config(key: str, value: str):
    with get_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?,?)", (key, value))
        conn.commit()


def get_all_config() -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM config").fetchall()
        return {r["key"]: r["value"] for r in rows}


# ── Habitaciones ─────────────────────────────────────────────────────────────

def get_all_rooms():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM rooms ORDER BY floor, number").fetchall()


def get_room(room_id: int):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM rooms WHERE id=?", (room_id,)).fetchone()


def get_room_by_number(number: str):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM rooms WHERE number=?", (number,)).fetchone()


def update_room_status(room_id: int, status: str):
    with get_connection() as conn:
        conn.execute("UPDATE rooms SET status=? WHERE id=?", (status, room_id))
        conn.commit()


def add_room(number, rtype, capacity, price, floor, description=""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO rooms (number, type, capacity, price_night, floor, description) VALUES (?,?,?,?,?,?)",
            (number, rtype, capacity, price, floor, description),
        )
        conn.commit()


def update_room(room_id, number, rtype, capacity, price, floor, description=""):
    with get_connection() as conn:
        conn.execute(
            "UPDATE rooms SET number=?, type=?, capacity=?, price_night=?, floor=?, description=? WHERE id=?",
            (number, rtype, capacity, price, floor, description, room_id),
        )
        conn.commit()


# ── Huéspedes ────────────────────────────────────────────────────────────────

def add_guest(name, id_number, email="", phone="", nationality=""):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO guests (name, id_number, email, phone, nationality, created_at) VALUES (?,?,?,?,?,?)",
            (name, id_number, email, phone, nationality, datetime.now().isoformat()),
        )
        conn.commit()
        return cur.lastrowid


def get_guest(guest_id: int):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM guests WHERE id=?", (guest_id,)).fetchone()


def search_guests(query: str):
    with get_connection() as conn:
        q = f"%{query}%"
        return conn.execute(
            "SELECT * FROM guests WHERE name LIKE ? OR id_number LIKE ? ORDER BY name",
            (q, q),
        ).fetchall()


def get_all_guests():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM guests ORDER BY name").fetchall()


# ── Reservas ──────────────────────────────────────────────────────────────────

def create_reservation(room_id, guest_id, checkin, nights, total_room, notes=""):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO reservations
               (room_id, guest_id, checkin, nights, total_room, notes, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (room_id, guest_id, checkin, nights, total_room, notes, datetime.now().isoformat()),
        )
        conn.execute("UPDATE rooms SET status='ocupada' WHERE id=?", (room_id,))
        conn.commit()
        return cur.lastrowid


def checkout_reservation(reservation_id: int):
    with get_connection() as conn:
        now = datetime.now().isoformat()
        row = conn.execute("SELECT room_id FROM reservations WHERE id=?", (reservation_id,)).fetchone()
        conn.execute(
            "UPDATE reservations SET status='completada', checkout=? WHERE id=?",
            (now, reservation_id),
        )
        conn.execute("UPDATE rooms SET status='disponible' WHERE id=?", (row["room_id"],))
        conn.commit()


def get_active_reservations():
    with get_connection() as conn:
        return conn.execute(
            """SELECT r.*, g.name AS guest_name, g.phone, g.email,
                      rm.number AS room_number, rm.type AS room_type, rm.price_night
               FROM reservations r
               JOIN guests g  ON g.id  = r.guest_id
               JOIN rooms  rm ON rm.id = r.room_id
               WHERE r.status = 'activa'
               ORDER BY r.checkin""",
        ).fetchall()


def get_all_reservations():
    with get_connection() as conn:
        return conn.execute(
            """SELECT r.*, g.name AS guest_name,
                      rm.number AS room_number, rm.type AS room_type
               FROM reservations r
               JOIN guests g  ON g.id  = r.guest_id
               JOIN rooms  rm ON rm.id = r.room_id
               ORDER BY r.created_at DESC""",
        ).fetchall()


def get_reservation(reservation_id: int):
    with get_connection() as conn:
        return conn.execute(
            """SELECT r.*, g.name AS guest_name, g.id_number, g.phone, g.email,
                      rm.number AS room_number, rm.type AS room_type, rm.price_night
               FROM reservations r
               JOIN guests g  ON g.id  = r.guest_id
               JOIN rooms  rm ON rm.id = r.room_id
               WHERE r.id=?""",
            (reservation_id,),
        ).fetchone()


# ── Menú ─────────────────────────────────────────────────────────────────────

def get_menu_items(category: str = None):
    with get_connection() as conn:
        if category:
            return conn.execute(
                "SELECT * FROM menu_items WHERE category=? AND available=1 ORDER BY name",
                (category,),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM menu_items WHERE available=1 ORDER BY category, name"
        ).fetchall()


def get_menu_categories():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM menu_items WHERE available=1 ORDER BY category"
        ).fetchall()
        return [r["category"] for r in rows]


def add_menu_item(name, category, price, description=""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO menu_items (name, category, price, description) VALUES (?,?,?,?)",
            (name, category, price, description),
        )
        conn.commit()


def update_menu_item(item_id, name, category, price, description, available):
    with get_connection() as conn:
        conn.execute(
            "UPDATE menu_items SET name=?, category=?, price=?, description=?, available=? WHERE id=?",
            (name, category, price, description, available, item_id),
        )
        conn.commit()


def delete_menu_item(item_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM menu_items WHERE id=?", (item_id,))
        conn.commit()


# ── Servicios ────────────────────────────────────────────────────────────────

def get_services(category: str = None):
    with get_connection() as conn:
        if category:
            return conn.execute(
                "SELECT * FROM services WHERE category=? AND available=1 ORDER BY name",
                (category,),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM services WHERE available=1 ORDER BY category, name"
        ).fetchall()


def get_service_categories():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM services WHERE available=1 ORDER BY category"
        ).fetchall()
        return [r["category"] for r in rows]


def add_service(name, category, price, description=""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO services (name, category, price, description) VALUES (?,?,?,?)",
            (name, category, price, description),
        )
        conn.commit()


def update_service(service_id, name, category, price, description, available):
    with get_connection() as conn:
        conn.execute(
            "UPDATE services SET name=?, category=?, price=?, description=?, available=? WHERE id=?",
            (name, category, price, description, available, service_id),
        )
        conn.commit()


def delete_service(service_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM services WHERE id=?", (service_id,))
        conn.commit()


# ── Órdenes ──────────────────────────────────────────────────────────────────

def create_order(order_type, reservation_id=None, guest_id=None, notes=""):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO orders (type, reservation_id, guest_id, notes, created_at)
               VALUES (?,?,?,?,?)""",
            (order_type, reservation_id, guest_id, notes, datetime.now().isoformat()),
        )
        conn.commit()
        return cur.lastrowid


def add_order_item(order_id, item_name, category, quantity, unit_price):
    subtotal = quantity * unit_price
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO order_items (order_id, item_name, category, quantity, unit_price, subtotal)
               VALUES (?,?,?,?,?,?)""",
            (order_id, item_name, category, quantity, unit_price, subtotal),
        )
        conn.commit()
    _recalculate_order(order_id)


def remove_order_item(order_item_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT order_id FROM order_items WHERE id=?", (order_item_id,)).fetchone()
        conn.execute("DELETE FROM order_items WHERE id=?", (order_item_id,))
        conn.commit()
    if row:
        _recalculate_order(row["order_id"])


def _recalculate_order(order_id: int):
    cfg = get_all_config()
    tax_rate = float(cfg.get("tax_rate", "15")) / 100
    with get_connection() as conn:
        subtotal = conn.execute(
            "SELECT COALESCE(SUM(subtotal),0) FROM order_items WHERE order_id=?", (order_id,)
        ).fetchone()[0]
        tax = round(subtotal * tax_rate, 2)
        total = round(subtotal + tax, 2)
        conn.execute(
            "UPDATE orders SET subtotal=?, tax=?, total=? WHERE id=?",
            (subtotal, tax, total, order_id),
        )
        conn.commit()


def close_order(order_id: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE orders SET status='cerrada', closed_at=? WHERE id=?",
            (datetime.now().isoformat(), order_id),
        )
        conn.commit()


def get_order(order_id: int):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()


def get_order_items(order_id: int):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM order_items WHERE order_id=? ORDER BY id", (order_id,)
        ).fetchall()


def get_open_orders():
    with get_connection() as conn:
        return conn.execute(
            """SELECT o.*, g.name AS guest_name
               FROM orders o
               LEFT JOIN guests g ON g.id = o.guest_id
               WHERE o.status = 'abierta'
               ORDER BY o.created_at DESC""",
        ).fetchall()


def get_orders_for_reservation(reservation_id: int):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM orders WHERE reservation_id=? ORDER BY created_at",
            (reservation_id,),
        ).fetchall()


# ── Facturas ─────────────────────────────────────────────────────────────────

def create_invoice(reservation_id, guest_name, room_number,
                   room_total, services_total, tax_rate_pct, payment_method):
    subtotal = room_total + services_total
    tax = round(subtotal * tax_rate_pct / 100, 2)
    total = round(subtotal + tax, 2)
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO invoices
               (reservation_id, guest_name, room_number, room_total, services_total,
                subtotal, tax, total, payment_method, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (reservation_id, guest_name, room_number, room_total, services_total,
             subtotal, tax, total, payment_method, datetime.now().isoformat()),
        )
        conn.commit()
        return cur.lastrowid


def pay_invoice(invoice_id: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE invoices SET status='pagada', paid_at=? WHERE id=?",
            (datetime.now().isoformat(), invoice_id),
        )
        conn.commit()


def get_invoice(invoice_id: int):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()


def get_all_invoices():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM invoices ORDER BY created_at DESC").fetchall()


# ── Reportes ─────────────────────────────────────────────────────────────────

def get_daily_summary(date_str: str) -> dict:
    with get_connection() as conn:
        day = date_str[:10]
        invoices = conn.execute(
            "SELECT COUNT(*) AS cnt, COALESCE(SUM(total),0) AS revenue "
            "FROM invoices WHERE substr(paid_at,1,10) = ? AND status='pagada'",
            (day,),
        ).fetchone()
        checkins = conn.execute(
            "SELECT COUNT(*) AS cnt FROM reservations WHERE substr(checkin,1,10) = ?",
            (day,),
        ).fetchone()
        checkouts = conn.execute(
            "SELECT COUNT(*) AS cnt FROM reservations WHERE substr(checkout,1,10) = ?",
            (day,),
        ).fetchone()
        occupied = conn.execute(
            "SELECT COUNT(*) FROM rooms WHERE status='ocupada'"
        ).fetchone()[0]
        total_rooms = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
        return {
            "date": day,
            "invoices_count": invoices["cnt"],
            "revenue": invoices["revenue"],
            "checkins": checkins["cnt"],
            "checkouts": checkouts["cnt"],
            "occupied_rooms": occupied,
            "total_rooms": total_rooms,
        }


def get_revenue_by_period(start: str, end: str):
    """start and end should be 'YYYY-MM-DD' strings."""
    start_day = start[:10]
    end_day = end[:10]
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM invoices WHERE substr(created_at,1,10) >= ? AND substr(created_at,1,10) <= ?"
            " AND status='pagada' ORDER BY created_at",
            (start_day, end_day),
        ).fetchall()
