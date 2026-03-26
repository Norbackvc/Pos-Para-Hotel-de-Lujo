"""
dashboard.py – Panel principal con tarjetas de acceso a módulos.
"""

import tkinter as tk
from tkinter import messagebox

from modules import database as db
from modules import estilos as st

MODULOS = [
    ("🍽️",  "Restaurante",  "restaurante"),
    ("🛏️",  "Habitaciones", "habitaciones"),
    ("🍸",  "Bar",          "bar"),
    ("💆",  "Spa",          "spa"),
    ("📋",  "Reportes",     "reportes"),
    ("⚙️",  "Configuración","configuracion"),
]


class VentanaDashboard(tk.Toplevel):
    """Panel principal del POS. Se abre tras autenticarse."""

    def __init__(self, usuario: dict, on_logout=None):
        super().__init__()
        self.usuario   = usuario
        self.on_logout = on_logout
        nombre_hotel = db.get_config("hotel_nombre", "Hotel de Lujo")
        self.title(f"{nombre_hotel} – POS")
        self.configure(bg=st.OSCURO)
        try:
            self.state("zoomed")          # Windows
        except Exception:
            self.attributes("-zoomed", True)  # Linux
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_main()

    def _build_header(self):
        header = tk.Frame(self, bg=st.OSCURO_MEDIO,
                          highlightthickness=1,
                          highlightbackground=st.DORADO)
        header.pack(fill=tk.X)

        izq = tk.Frame(header, bg=st.OSCURO_MEDIO)
        izq.pack(side=tk.LEFT, padx=20, pady=12)
        tk.Label(izq, text="🏨", font=("Segoe UI", 18),
                 bg=st.OSCURO_MEDIO, fg=st.DORADO).pack(side=tk.LEFT)
        nombre_hotel = db.get_config("hotel_nombre", "Hotel de Lujo")
        tk.Label(izq, text=f"  {nombre_hotel} – POS",
                 font=("Segoe UI", 13, "bold"),
                 bg=st.OSCURO_MEDIO, fg=st.DORADO).pack(side=tk.LEFT)

        der = tk.Frame(header, bg=st.OSCURO_MEDIO)
        der.pack(side=tk.RIGHT, padx=20, pady=12)
        nombre = self.usuario.get("nombre", self.usuario.get("usuario", ""))
        rol    = self.usuario.get("rol", "")
        tk.Label(der, text=f"{nombre} ({rol})",
                 font=("Segoe UI", 10),
                 bg=st.OSCURO_MEDIO, fg=st.TEXTO_GRIS).pack(side=tk.LEFT, padx=(0, 16))
        tk.Button(
            der, text="Cerrar Sesión",
            command=self._cerrar_sesion,
            bg=st.OSCURO_MEDIO, fg=st.DORADO,
            font=("Segoe UI", 9), relief="flat",
            cursor="hand2", padx=10, pady=4,
            highlightthickness=1, highlightbackground=st.DORADO,
            activebackground=st.OSCURO_CLARO, activeforeground=st.DORADO_CLARO,
        ).pack(side=tk.LEFT)

    def _build_main(self):
        main = tk.Frame(self, bg=st.OSCURO)
        main.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)

        tk.Label(
            main,
            text="Bienvenido al Panel Principal",
            font=("Segoe UI", 17, "bold"),
            bg=st.OSCURO, fg=st.DORADO_CLARO,
        ).pack(anchor=tk.W, pady=(0, 24))

        grid = tk.Frame(main, bg=st.OSCURO)
        grid.pack(fill=tk.BOTH, expand=True)

        for i, (icono, texto, key) in enumerate(MODULOS):
            fila = i // 3
            col  = i % 3
            self._tarjeta(grid, icono, texto, key).grid(
                row=fila, column=col, padx=14, pady=14, sticky="nsew"
            )

        for col in range(3):
            grid.columnconfigure(col, weight=1)
        for fila in range((len(MODULOS) + 2) // 3):
            grid.rowconfigure(fila, weight=1)

    def _tarjeta(self, parent, icono: str, texto: str, key: str) -> tk.Frame:
        frame = tk.Frame(
            parent,
            bg=st.OSCURO_MEDIO,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground="#2a2a4a",
        )

        def _enter(_e):
            frame.configure(highlightbackground=st.DORADO,
                            bg=st.OSCURO_CLARO)
            lbl_icono.configure(bg=st.OSCURO_CLARO)
            lbl_texto.configure(bg=st.OSCURO_CLARO)

        def _leave(_e):
            frame.configure(highlightbackground="#2a2a4a",
                            bg=st.OSCURO_MEDIO)
            lbl_icono.configure(bg=st.OSCURO_MEDIO)
            lbl_texto.configure(bg=st.OSCURO_MEDIO)

        def _click(_e=None):
            self._abrir_modulo(key)

        frame.bind("<Enter>",  _enter)
        frame.bind("<Leave>",  _leave)
        frame.bind("<Button-1>", _click)

        lbl_icono = tk.Label(frame, text=icono, font=("Segoe UI", 38),
                             bg=st.OSCURO_MEDIO, fg=st.TEXTO_CLARO)
        lbl_icono.pack(pady=(28, 6))
        lbl_icono.bind("<Button-1>", _click)
        lbl_icono.bind("<Enter>",  _enter)
        lbl_icono.bind("<Leave>",  _leave)

        lbl_texto = tk.Label(frame, text=texto,
                             font=("Segoe UI", 12, "bold"),
                             bg=st.OSCURO_MEDIO, fg=st.TEXTO_CLARO)
        lbl_texto.pack(pady=(0, 28))
        lbl_texto.bind("<Button-1>", _click)
        lbl_texto.bind("<Enter>",  _enter)
        lbl_texto.bind("<Leave>",  _leave)

        return frame

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _cerrar_sesion(self):
        if messagebox.askyesno("Cerrar Sesión",
                               "¿Desea cerrar la sesión actual?",
                               parent=self):
            if self.on_logout:
                self.on_logout(self)

    def _abrir_modulo(self, key: str):
        import importlib
        modulo_map = {
            "restaurante":   "modules.restaurante",
            "habitaciones":  "modules.habitaciones",
            "bar":           "modules.bar",
            "spa":           "modules.spa",
            "reportes":      "modules.reportes",
            "configuracion": "modules.configuracion",
        }
        clase_map = {
            "restaurante":   "VentanaRestaurante",
            "habitaciones":  "VentanaHabitaciones",
            "bar":           "VentanaBar",
            "spa":           "VentanaSpa",
            "reportes":      "VentanaReportes",
            "configuracion": "VentanaConfiguracion",
        }
        mod_path = modulo_map.get(key)
        clase_nombre = clase_map.get(key)
        if not mod_path:
            return
        try:
            modulo = importlib.import_module(mod_path)
            Clase  = getattr(modulo, clase_nombre)
            ventana = Clase(self, self.usuario)
            ventana.grab_set()
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)
