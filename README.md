# POS Para Hotel de Lujo 🏨

Sistema de Punto de Venta (POS) para hoteles de lujo, desarrollado en **Python** con interfaz gráfica **Tkinter** y base de datos **SQLite**.

---

## ✨ Características

| Módulo | Descripción |
|---|---|
| 🏨 Habitaciones | Alta, edición y control de estado (disponible / ocupada / reservada / mantenimiento) |
| 📅 Reservas | Gestión completa: check-in, check-out, cancelación |
| 👤 Huéspedes | Registro de clientes con búsqueda rápida |
| 🍽️ Pedidos | Room service, restaurante, bar, spa, lavandería |
| 🧾 Facturación | Generación de facturas con IVA, descuentos y vista previa imprimible |
| 📦 Productos | Catálogo con categorías y precios |
| 📊 Reportes | Ocupación y ingresos por período |
| ⚙️ Configuración | Nombre del hotel, moneda, IVA, logo personalizable |

---

## 🚀 Instalación

### Requisitos
- Python 3.9+
- (Opcional) `Pillow` para mostrar el logo del hotel

```bash
pip install -r requirements.txt
```

### Ejecutar

```bash
python hotel_pos.py
```

---

## 🖼️ Logo del Hotel

1. Coloca tu archivo de logo (PNG/JPG) en la carpeta `assets/`.
2. Abre la pestaña **⚙️ Configuración**.
3. Haz clic en **📂 Seleccionar Logo** y elige el archivo.
4. Guarda la configuración.

El logo aparecerá en el encabezado de la aplicación y en las facturas impresas.

---

## 🗂️ Estructura del Proyecto

```
hotel_pos.py          ← Punto de entrada principal
modules/
  database.py         ← Capa de acceso a datos (SQLite)
  models.py           ← Modelos de datos
  ui/
    rooms.py          ← Panel de habitaciones
    reservations.py   ← Panel de reservas
    guests.py         ← Panel de huéspedes
    orders.py         ← Panel de pedidos
    billing.py        ← Panel de facturación
    products.py       ← Panel de productos
    reports.py        ← Panel de reportes
    settings.py       ← Panel de configuración
assets/               ← Logo e imágenes del hotel
hotel_pos.db          ← Base de datos SQLite (se crea automáticamente)
requirements.txt
```

---

## 📄 Licencia

MIT
