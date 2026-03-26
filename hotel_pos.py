#!/usr/bin/env python3
"""
hotel_pos.py – Punto de entrada del Sistema POS para Hotel de Lujo.

Uso:
    python hotel_pos.py

Requisitos:
    Python 3.10+  (usa union types con |)
    tkinter       (incluido en la instalación estándar de Python)
    sqlite3       (módulo estándar de Python)
"""

import sys
import os

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(__file__))

from modules import database as db
from modules.login import VentanaLogin


def main():
    # Inicializar la base de datos (crea tablas y datos de ejemplo si es necesario)
    db.inicializar_bd()

    # Lanzar la ventana de login
    app = VentanaLogin()
    app.mainloop()


if __name__ == "__main__":
    main()
