"""
Hotel POS — Sistema Punto de Venta para Hotel de Lujo
=====================================================
Aplicación principal. Punto de entrada.

Uso:
    python hotel_pos.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    _LANCZOS = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
except ImportError:
    PIL_AVAILABLE = False
    _LANCZOS = None

from modules import database as db
from modules.theme import get_theme
from modules.ui_rooms import RoomsPanel
from modules.ui_restaurant import RestaurantPanel
from modules.ui_services import ServicesPanel
from modules.ui_billing import BillingPanel
from modules.ui_reports import ReportsPanel
from modules.ui_settings import SettingsPanel


# ──────────────────────────────────────────────────────────────────────────────
# Ventana principal
# ──────────────────────────────────────────────────────────────────────────────

class HotelPOS(tk.Tk):
    """Ventana raíz del sistema POS del hotel."""

    SECTIONS = [
        ("rooms",      "🛏  Habitaciones"),
        ("restaurant", "🍽  Restaurante"),
        ("services",   "✨  Servicios"),
        ("billing",    "💳  Facturación"),
        ("reports",    "📊  Reportes"),
        ("settings",   "⚙   Configuración"),
    ]

    def __init__(self):
        super().__init__()

        # Inicializar DB
        db.initialize_db()

        # Cargar tema
        cfg = db.get_all_config()
        self.theme = get_theme(cfg.get("theme", "dark"))
        t = self.theme

        self.title("Hotel POS — Sistema de Punto de Venta")
        self.configure(bg=t["bg"])
        self.geometry("1280x780")
        self.minsize(900, 600)

        self._logo_img = None
        self._sidebar_logo_img = None
        self._active_panel = None
        self._panels = {}

        self._build_ui()
        self._switch_panel("rooms")
        self.update_status_bar()

    # ── Construcción de la UI ─────────────────────────────────────────────────

    def _build_ui(self):
        t = self.theme

        # ── Barra lateral izquierda ──
        self.sidebar = tk.Frame(self, bg=t["sidebar"], width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._build_sidebar_header()
        self._build_sidebar_menu()
        self._build_sidebar_footer()

        # ── Área de contenido ──
        right = tk.Frame(self, bg=t["bg"])
        right.pack(side="left", fill="both", expand=True)

        # Barra superior
        self.header_bar = tk.Frame(right, bg=t["bg3"], height=48)
        self.header_bar.pack(fill="x")
        self.header_bar.pack_propagate(False)
        self._build_header(self.header_bar)

        # Contenido principal
        self.content_area = tk.Frame(right, bg=t["bg2"])
        self.content_area.pack(fill="both", expand=True)

        # Barra de estado inferior
        self.status_bar = tk.Frame(right, bg=t["bg3"], height=24)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)
        self.status_label = tk.Label(
            self.status_bar,
            text="Sistema listo",
            bg=t["bg3"], fg=t["fg2"],
            font=(t["font"], 8),
            anchor="w",
        )
        self.status_label.pack(side="left", padx=8, fill="y")

        self.clock_label = tk.Label(
            self.status_bar,
            text="",
            bg=t["bg3"], fg=t["fg2"],
            font=(t["font"], 8),
        )
        self.clock_label.pack(side="right", padx=8, fill="y")
        self._update_clock()

    def _build_sidebar_header(self):
        t = self.theme
        header = tk.Frame(self.sidebar, bg=t["sidebar"], pady=16)
        header.pack(fill="x")

        # Logo del hotel en la barra lateral
        self._sidebar_logo_frame = tk.Frame(header, bg=t["sidebar"])
        self._sidebar_logo_frame.pack()
        self._load_sidebar_logo()

        # Nombre del hotel
        self.sidebar_hotel_name = tk.Label(
            header,
            text=db.get_config("hotel_name") or "Grand Luxe Hotel",
            bg=t["sidebar"], fg=t["gold"],
            font=(t["font"], 11, "bold"),
            wraplength=180,
        )
        self.sidebar_hotel_name.pack(pady=(6, 0))

        tk.Label(
            header, text="POS — Punto de Venta",
            bg=t["sidebar"], fg=t["fg2"],
            font=(t["font"], 8),
        ).pack()

        # Separador
        tk.Frame(header, bg=t["border"], height=1).pack(fill="x", pady=(10, 0), padx=12)

    def _load_sidebar_logo(self):
        t = self.theme
        # Limpiar frame
        for w in self._sidebar_logo_frame.winfo_children():
            w.destroy()

        logo_path = db.get_config("hotel_logo")
        if logo_path and os.path.isfile(logo_path) and PIL_AVAILABLE:
            try:
                img = Image.open(logo_path)
                img.thumbnail((120, 80), _LANCZOS)
                self._sidebar_logo_img = ImageTk.PhotoImage(img)
                tk.Label(
                    self._sidebar_logo_frame,
                    image=self._sidebar_logo_img,
                    bg=t["sidebar"],
                ).pack()
                return
            except Exception:
                pass

        # Logo de texto cuando no hay imagen
        logo_canvas = tk.Canvas(
            self._sidebar_logo_frame,
            width=110, height=70,
            bg=t["sidebar"], highlightthickness=0,
        )
        logo_canvas.pack()
        logo_canvas.create_rectangle(5, 5, 105, 65, outline=t["gold"], width=2)
        logo_canvas.create_text(55, 28, text="★", font=("Helvetica", 24), fill=t["gold"])
        logo_canvas.create_text(55, 52, text="HOTEL", font=("Helvetica", 9, "bold"),
                                fill=t["gold"])

    def _build_sidebar_menu(self):
        t = self.theme
        self._sidebar_btns = {}

        for key, label in self.SECTIONS:
            btn = tk.Button(
                self.sidebar,
                text=label,
                bg=t["sidebar"], fg=t["fg"],
                activebackground=t["sidebar_sel"],
                activeforeground="#ffffff",
                relief="flat",
                cursor="hand2",
                font=(t["font"], 10),
                anchor="w",
                padx=16,
                pady=10,
                command=lambda k=key: self._switch_panel(k),
            )
            btn.pack(fill="x")
            self._sidebar_btns[key] = btn

    def _build_sidebar_footer(self):
        t = self.theme
        footer = tk.Frame(self.sidebar, bg=t["sidebar"])
        footer.pack(side="bottom", fill="x", pady=8)
        tk.Frame(footer, bg=t["border"], height=1).pack(fill="x", padx=12, pady=(0, 8))
        tk.Button(
            footer,
            text="❌  Salir",
            bg=t["sidebar"], fg=t["error"],
            activebackground=t["error"], activeforeground="#ffffff",
            relief="flat", cursor="hand2",
            font=(t["font"], 10),
            anchor="w", padx=16, pady=8,
            command=self._quit,
        ).pack(fill="x")

    def _build_header(self, parent):
        t = self.theme
        self.header_logo_label = tk.Label(parent, bg=t["bg3"])
        self.header_logo_label.pack(side="left", padx=(12, 8), pady=4)

        self.header_title = tk.Label(
            parent,
            text=db.get_config("hotel_name") or "Grand Luxe Hotel",
            bg=t["bg3"], fg=t["gold"],
            font=(t["font"], 14, "bold"),
        )
        self.header_title.pack(side="left")

        self.section_label = tk.Label(
            parent, text="",
            bg=t["bg3"], fg=t["fg2"],
            font=(t["font"], 10),
        )
        self.section_label.pack(side="left", padx=(16, 0))

        # Indicadores de estado a la derecha
        right_frame = tk.Frame(parent, bg=t["bg3"])
        right_frame.pack(side="right", padx=12)

        self.header_occupied_label = tk.Label(
            right_frame, text="",
            bg=t["bg3"], fg=t["fg2"],
            font=(t["font"], 9),
        )
        self.header_occupied_label.pack(side="right", padx=8)

        self._load_header_logo()

    def _load_header_logo(self):
        t = self.theme
        logo_path = db.get_config("hotel_logo")
        if logo_path and os.path.isfile(logo_path) and PIL_AVAILABLE:
            try:
                img = Image.open(logo_path)
                img.thumbnail((36, 36), _LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                self.header_logo_label.config(image=self._logo_img)
                return
            except Exception:
                pass
        self.header_logo_label.config(image="", text="★",
                                       fg=t["gold"],
                                       font=("Helvetica", 18))

    # ── Navegación ────────────────────────────────────────────────────────────

    def _switch_panel(self, key: str):
        t = self.theme

        # Actualizar botones de la barra lateral
        for k, btn in self._sidebar_btns.items():
            if k == key:
                btn.config(bg=t["sidebar_sel"], fg="#ffffff")
            else:
                btn.config(bg=t["sidebar"], fg=t["fg"])

        # Actualizar etiqueta de sección
        section_name = dict(self.SECTIONS).get(key, "")
        self.section_label.config(text=f"›  {section_name}")

        # Limpiar área de contenido
        for w in self.content_area.winfo_children():
            w.pack_forget()

        # Crear panel si no existe
        if key not in self._panels:
            self._panels[key] = self._create_panel(key)

        self._panels[key].pack(fill="both", expand=True)
        self._active_panel = key

    def _create_panel(self, key: str) -> tk.Frame:
        t = self.theme
        creators = {
            "rooms":      lambda: RoomsPanel(self.content_area, t, app=self),
            "restaurant": lambda: RestaurantPanel(self.content_area, t, app=self),
            "services":   lambda: ServicesPanel(self.content_area, t, app=self),
            "billing":    lambda: BillingPanel(self.content_area, t, app=self),
            "reports":    lambda: ReportsPanel(self.content_area, t, app=self),
            "settings":   lambda: SettingsPanel(self.content_area, t, app=self),
        }
        return creators[key]()

    # ── Actualización de la UI ────────────────────────────────────────────────

    def update_status_bar(self):
        rooms = db.get_all_rooms()
        occupied = sum(1 for r in rooms if r["status"] == "ocupada")
        total = len(rooms)
        self.header_occupied_label.config(
            text=f"🛏 {occupied}/{total} ocupadas"
        )

    def reload_header(self):
        """Recarga el logo y nombre del hotel en el encabezado."""
        hotel_name = db.get_config("hotel_name") or "Grand Luxe Hotel"
        self.header_title.config(text=hotel_name)
        self.sidebar_hotel_name.config(text=hotel_name)
        self._load_header_logo()
        self._load_sidebar_logo()

    def _update_clock(self):
        from datetime import datetime
        now = datetime.now().strftime("%A, %d %b %Y  %H:%M:%S")
        self.clock_label.config(text=now)
        self.after(1000, self._update_clock)

    def _quit(self):
        if messagebox.askyesno("Salir", "¿Deseas cerrar el sistema POS?"):
            self.destroy()


# ──────────────────────────────────────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────────────────────────────────────

def main():
    app = HotelPOS()
    app.mainloop()


if __name__ == "__main__":
    main()
