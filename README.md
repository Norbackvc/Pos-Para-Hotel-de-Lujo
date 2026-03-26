# POS para Hotel de Lujo

Sistema de Punto de Venta (POS) para hotel de lujo, desarrollado en Python con interfaz gráfica tkinter y base de datos SQLite.

## Requisitos

- Python 3.10 o superior
- tkinter (incluido en la instalación estándar de Python; en Ubuntu: `sudo apt install python3-tk`)

## Ejecución

```bash
python hotel_pos.py
```

## Credenciales de demo

| Usuario | Contraseña  | Rol         |
|---------|-------------|-------------|
| admin   | hotel123    | Administrador |
| cajero  | cajero456   | Cajero      |
| mesero  | mesero789   | Mesero      |

## Módulos

- 🍽️ **Restaurante** – Mesas, menú por categorías, órdenes y cobro con IVA
- 🛏️ **Habitaciones** – Check-in / check-out, listado de reservaciones
- 🍸 **Bar** – Menú de cócteles y bebidas, órdenes rápidas
- 💆 **Spa** – Agenda de citas, servicios y cobro directo
- 📋 **Reportes** – Ventas por módulo y rango de fechas, top productos, ocupación
- ⚙️ **Configuración** – Datos del hotel, gestión de usuarios y productos

## Estructura

```
hotel_pos.py        # Punto de entrada
modules/
    database.py     # SQLite: esquema, seed y operaciones de datos
    estilos.py      # Tema visual (colores, fuentes, estilos)
    login.py        # Ventana de inicio de sesión
    dashboard.py    # Panel principal con tarjetas de módulos
    restaurante.py  # Módulo Restaurante
    habitaciones.py # Módulo Habitaciones
    bar.py          # Módulo Bar
    spa.py          # Módulo Spa
    reportes.py     # Módulo Reportes
    configuracion.py# Módulo Configuración
```

La base de datos `hotel_pos.db` se crea automáticamente al ejecutar la aplicación.
