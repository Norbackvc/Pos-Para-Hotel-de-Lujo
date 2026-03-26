"""
database.py – Inicialización de la base de datos SQLite y operaciones de acceso a datos.
"""

import sqlite3
import hashlib
import hmac
import os
import secrets

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hotel_pos.db")


def get_connection():
    """Retorna una conexión a la base de datos con row_factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


_PBKDF2_ITERATIONS = 260_000
_PBKDF2_ALGO       = "sha256"


def hash_password(password: str) -> str:
    """Hashea una contraseña usando PBKDF2-HMAC-SHA256 con sal aleatoria.

    Formato de retorno: ``pbkdf2:sha256:<iter>:<salt_hex>:<hash_hex>``
    """
    salt = secrets.token_hex(16)
    dk   = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGO,
        password.encode(),
        salt.encode(),
        _PBKDF2_ITERATIONS,
    )
    return f"pbkdf2:{_PBKDF2_ALGO}:{_PBKDF2_ITERATIONS}:{salt}:{dk.hex()}"


def _verify_password(stored: str, password: str) -> bool:
    """Verifica una contraseña contra su hash almacenado (PBKDF2 o SHA-256 legacy)."""
    if stored.startswith("pbkdf2:"):
        try:
            _, algo, iterations, salt, stored_hex = stored.split(":")
            dk = hashlib.pbkdf2_hmac(
                algo,
                password.encode(),
                salt.encode(),
                int(iterations),
            )
            return hmac.compare_digest(dk.hex(), stored_hex)
        except (ValueError, TypeError):
            return False
    # Soporte legado: SHA-256 sin sal (migrado al primer login)
    return hmac.compare_digest(
        stored,
        hashlib.sha256(password.encode()).hexdigest(),
    )


def inicializar_bd():
    """Crea todas las tablas e inserta datos de ejemplo si no existen."""
    conn = get_connection()
    cur = conn.cursor()

    # ── Usuarios ──────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario         TEXT    UNIQUE NOT NULL,
            contrasena_hash TEXT    NOT NULL,
            nombre          TEXT    NOT NULL,
            rol             TEXT    NOT NULL DEFAULT 'cajero',
            activo          INTEGER NOT NULL DEFAULT 1
        )
    """)

    # ── Configuración ─────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)

    # ── Habitaciones ──────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS habitaciones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            numero      TEXT    UNIQUE NOT NULL,
            tipo        TEXT    NOT NULL,
            capacidad   INTEGER NOT NULL DEFAULT 2,
            precio_noche REAL   NOT NULL,
            estado      TEXT    NOT NULL DEFAULT 'disponible',
            descripcion TEXT    DEFAULT ''
        )
    """)

    # ── Reservaciones ─────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservaciones (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            habitacion_id   INTEGER NOT NULL REFERENCES habitaciones(id),
            cliente_nombre  TEXT    NOT NULL,
            cliente_email   TEXT    DEFAULT '',
            fecha_entrada   TEXT    NOT NULL,
            fecha_salida    TEXT    NOT NULL,
            adultos         INTEGER NOT NULL DEFAULT 1,
            ninos           INTEGER NOT NULL DEFAULT 0,
            precio_total    REAL    NOT NULL DEFAULT 0,
            estado          TEXT    NOT NULL DEFAULT 'activa',
            notas           TEXT    DEFAULT '',
            fecha_creacion  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── Mesas ─────────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mesas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            numero      TEXT    UNIQUE NOT NULL,
            capacidad   INTEGER NOT NULL DEFAULT 4,
            ubicacion   TEXT    DEFAULT '',
            estado      TEXT    NOT NULL DEFAULT 'libre'
        )
    """)

    # ── Productos ─────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL,
            categoria   TEXT    NOT NULL,
            modulo      TEXT    NOT NULL,
            precio      REAL    NOT NULL,
            descripcion TEXT    DEFAULT '',
            activo      INTEGER NOT NULL DEFAULT 1
        )
    """)

    # ── Órdenes ───────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ordenes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            modulo          TEXT    NOT NULL,
            referencia      TEXT    DEFAULT '',
            usuario_id      INTEGER REFERENCES usuarios(id),
            fecha           TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            estado          TEXT    NOT NULL DEFAULT 'abierta',
            subtotal        REAL    NOT NULL DEFAULT 0,
            impuesto        REAL    NOT NULL DEFAULT 0,
            total           REAL    NOT NULL DEFAULT 0,
            metodo_pago     TEXT    DEFAULT '',
            notas           TEXT    DEFAULT ''
        )
    """)

    # ── Ítems de orden ────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orden_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            orden_id        INTEGER NOT NULL REFERENCES ordenes(id),
            producto_id     INTEGER NOT NULL REFERENCES productos(id),
            cantidad        INTEGER NOT NULL DEFAULT 1,
            precio_unitario REAL    NOT NULL,
            subtotal        REAL    NOT NULL,
            notas           TEXT    DEFAULT ''
        )
    """)

    # ── Servicios Spa ─────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS spa_citas (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_nombre  TEXT    NOT NULL,
            servicio_id     INTEGER NOT NULL REFERENCES productos(id),
            fecha           TEXT    NOT NULL,
            hora            TEXT    NOT NULL,
            duracion_min    INTEGER NOT NULL DEFAULT 60,
            terapeuta       TEXT    DEFAULT '',
            estado          TEXT    NOT NULL DEFAULT 'programada',
            notas           TEXT    DEFAULT '',
            fecha_creacion  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    conn.commit()

    # ── Seed de datos iniciales ────────────────────────────────────────────────
    _seed_usuarios(cur, conn)
    _seed_configuracion(cur, conn)
    _seed_habitaciones(cur, conn)
    _seed_mesas(cur, conn)
    _seed_productos(cur, conn)

    conn.close()


def _seed_usuarios(cur, conn):
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        usuarios = [
            ("admin",  hash_password("hotel123"),  "Administrador", "admin"),
            ("cajero", hash_password("cajero456"), "Cajero",        "cajero"),
            ("mesero", hash_password("mesero789"), "Mesero",        "mesero"),
        ]
        cur.executemany(
            "INSERT INTO usuarios (usuario, contrasena_hash, nombre, rol) VALUES (?,?,?,?)",
            usuarios,
        )
        conn.commit()


def _seed_configuracion(cur, conn):
    cur.execute("SELECT COUNT(*) FROM configuracion")
    if cur.fetchone()[0] == 0:
        config = [
            ("hotel_nombre",   "Hotel de Lujo"),
            ("hotel_slogan",   "Sistema de Punto de Venta"),
            ("impuesto_pct",   "16"),
            ("moneda_simbolo", "$"),
            ("version",        "1.0.0"),
        ]
        cur.executemany("INSERT OR IGNORE INTO configuracion VALUES (?,?)", config)
        conn.commit()


def _seed_habitaciones(cur, conn):
    cur.execute("SELECT COUNT(*) FROM habitaciones")
    if cur.fetchone()[0] == 0:
        habitaciones = [
            ("101", "Estándar",    2, 1500.00, "disponible", "Vista al jardín"),
            ("102", "Estándar",    2, 1500.00, "disponible", "Vista al jardín"),
            ("103", "Estándar",    2, 1500.00, "disponible", "Vista a la calle"),
            ("201", "Deluxe",      2, 2500.00, "disponible", "Vista al mar"),
            ("202", "Deluxe",      2, 2500.00, "disponible", "Vista al mar"),
            ("203", "Junior Suite",3, 3800.00, "disponible", "Sala de estar"),
            ("301", "Suite",       4, 5500.00, "disponible", "Terraza privada"),
            ("302", "Suite",       4, 5500.00, "disponible", "Jacuzzi"),
            ("401", "Penthouse",   6, 9500.00, "disponible", "Piso completo, piscina privada"),
        ]
        cur.executemany(
            "INSERT INTO habitaciones (numero,tipo,capacidad,precio_noche,estado,descripcion) VALUES (?,?,?,?,?,?)",
            habitaciones,
        )
        conn.commit()


def _seed_mesas(cur, conn):
    cur.execute("SELECT COUNT(*) FROM mesas")
    if cur.fetchone()[0] == 0:
        mesas = [
            ("M01", 2, "Terraza"),
            ("M02", 2, "Terraza"),
            ("M03", 4, "Salón principal"),
            ("M04", 4, "Salón principal"),
            ("M05", 4, "Salón principal"),
            ("M06", 6, "Salón principal"),
            ("M07", 6, "Salón privado"),
            ("M08", 8, "Salón privado"),
            ("B01", 2, "Bar"),
            ("B02", 2, "Bar"),
        ]
        cur.executemany(
            "INSERT INTO mesas (numero, capacidad, ubicacion) VALUES (?,?,?)",
            mesas,
        )
        conn.commit()


def _seed_productos(cur, conn):
    cur.execute("SELECT COUNT(*) FROM productos")
    if cur.fetchone()[0] == 0:
        productos = [
            # Restaurante – Entradas
            ("Carpaccio de res",     "Entradas",   "restaurante", 185.00, "Con alcaparras y parmesano"),
            ("Foie gras",            "Entradas",   "restaurante", 220.00, "Con brioche tostado"),
            ("Ensalada niçoise",     "Entradas",   "restaurante", 145.00, "Atún sellado"),
            # Restaurante – Platos fuertes
            ("Filete mignon",        "Platos fuertes", "restaurante", 450.00, "8 oz, salsa de vino tinto"),
            ("Langosta a la parrilla","Platos fuertes","restaurante", 680.00, "Media langosta"),
            ("Risotto de hongos",    "Platos fuertes", "restaurante", 290.00, "Trufa negra"),
            ("Salmón en costra",     "Platos fuertes", "restaurante", 380.00, "Costra de hierbas"),
            # Restaurante – Postres
            ("Fondant de chocolate", "Postres",    "restaurante", 135.00, "Con helado de vainilla"),
            ("Crème brûlée",         "Postres",    "restaurante", 110.00, "Receta clásica"),
            ("Tarta tatin",          "Postres",    "restaurante", 120.00, "Manzana caramelizada"),
            # Restaurante – Bebidas
            ("Agua mineral",         "Bebidas",    "restaurante",  45.00, "500 ml"),
            ("Jugo natural",         "Bebidas",    "restaurante",  75.00, "Naranja o piña"),
            ("Café espresso",        "Bebidas",    "restaurante",  55.00, "Doble shot"),
            # Bar – Cócteles
            ("Martini clásico",      "Cócteles",   "bar",  150.00, "Dry martini con oliva"),
            ("Mojito",               "Cócteles",   "bar",  130.00, "Menta fresca"),
            ("Negroni",              "Cócteles",   "bar",  145.00, "Campari, gin, vermut"),
            ("Cosmopolitan",         "Cócteles",   "bar",  140.00, "Vodka, triple sec, cranberry"),
            ("Old Fashioned",        "Cócteles",   "bar",  160.00, "Bourbon, bitters"),
            # Bar – Vinos
            ("Vino tinto (copa)",    "Vinos",      "bar",  120.00, "Cabernet Sauvignon"),
            ("Vino blanco (copa)",   "Vinos",      "bar",  110.00, "Chardonnay"),
            ("Champagne (copa)",     "Vinos",      "bar",  195.00, "Brut"),
            # Bar – Cervezas
            ("Cerveza artesanal",    "Cervezas",   "bar",   85.00, "Pale Ale local"),
            ("Cerveza importada",    "Cervezas",   "bar",   95.00, "Heineken, Corona, etc."),
            # Bar – Sin alcohol
            ("Agua con gas",         "Sin alcohol","bar",   45.00, ""),
            ("Refresco",             "Sin alcohol","bar",   50.00, ""),
            # Spa – Masajes
            ("Masaje relajante",     "Masajes",    "spa",  850.00, "60 minutos"),
            ("Masaje de tejido profundo","Masajes","spa", 1050.00, "75 minutos"),
            ("Masaje de piedras calientes","Masajes","spa",1200.00, "90 minutos"),
            ("Masaje de aromas",     "Masajes",    "spa",  950.00, "60 minutos"),
            # Spa – Tratamientos
            ("Facial rejuvenecedor", "Faciales",   "spa",  750.00, "60 minutos"),
            ("Exfoliación corporal", "Tratamientos","spa", 680.00, "45 minutos"),
            ("Envolvimiento de lodo","Tratamientos","spa", 900.00, "60 minutos"),
            # Spa – Paquetes
            ("Día de spa completo",  "Paquetes",   "spa", 3500.00, "Masaje + facial + almuerzo"),
            ("Paquete luna de miel", "Paquetes",   "spa", 4200.00, "Tratamiento para parejas"),
        ]
        cur.executemany(
            "INSERT INTO productos (nombre,categoria,modulo,precio,descripcion) VALUES (?,?,?,?,?)",
            productos,
        )
        conn.commit()


# ── Funciones de utilidad ──────────────────────────────────────────────────────

def get_config(clave: str, default: str = "") -> str:
    conn = get_connection()
    row = conn.execute("SELECT valor FROM configuracion WHERE clave=?", (clave,)).fetchone()
    conn.close()
    return row["valor"] if row else default


def set_config(clave: str, valor: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO configuracion VALUES (?,?)", (clave, valor))
    conn.commit()
    conn.close()


def verificar_credenciales(usuario: str, contrasena: str):
    """Retorna la fila del usuario o None si las credenciales son incorrectas."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM usuarios WHERE usuario=? AND activo=1",
        (usuario,),
    ).fetchone()
    if row is None or not _verify_password(row["contrasena_hash"], contrasena):
        conn.close()
        return None
    conn.close()
    return row
