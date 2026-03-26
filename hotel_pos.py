"""
Hotel POS – Main application window.
Luxury Hotel Point-of-Sale system built with Python + Tkinter + SQLite.
"""
import os
import tkinter as tk
from tkinter import ttk

import modules.database as db
from modules.ui.rooms        import RoomsPanel
from modules.ui.reservations import ReservationsPanel
from modules.ui.guests       import GuestsPanel
from modules.ui.orders       import OrdersPanel
from modules.ui.billing      import BillingPanel
from modules.ui.products     import ProductsPanel
from modules.ui.reports      import ReportsPanel
from modules.ui.settings     import SettingsPanel

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

ACCENT    = "#1a1a2e"   # dark navy – header / sidebar
ACCENT_LT = "#16213e"   # slightly lighter nav hover
GOLD      = "#c9a84c"   # luxury gold accent
BG        = "#f5f5f0"   # off-white content area
FG_LIGHT  = "#ffffff"


class HotelPOSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        db.initialize_database()
        self.settings = db.load_settings()

        self.title(f"{self.settings.hotel_name} – Sistema POS")
        self.geometry("1200x700")
        self.minsize(900, 560)
        self.configure(bg=ACCENT)

        self._apply_theme()
        self._build_ui()

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def _apply_theme(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".",              background=BG,     foreground="#222")
        style.configure("TFrame",         background=BG)
        style.configure("TLabel",         background=BG,     foreground="#222")
        style.configure("TLabelframe",    background=BG,     foreground=ACCENT)
        style.configure("TLabelframe.Label", foreground=ACCENT, font=("Helvetica", 9, "bold"))
        style.configure("TEntry",         fieldbackground="#fff", foreground="#222")
        style.configure("TCombobox",      fieldbackground="#fff", foreground="#222")
        style.configure("TSpinbox",       fieldbackground="#fff", foreground="#222")
        style.configure("TButton",        background=ACCENT, foreground=FG_LIGHT,
                        padding=(8, 4), relief="flat")
        style.map("TButton",
                  background=[("active", GOLD), ("pressed", GOLD)],
                  foreground=[("active", ACCENT)])
        style.configure("Treeview",        background="#fff",  fieldbackground="#fff",
                        rowheight=24, font=("Helvetica", 9))
        style.configure("Treeview.Heading", background=ACCENT, foreground=FG_LIGHT,
                        font=("Helvetica", 9, "bold"))
        style.map("Treeview", background=[("selected", GOLD)], foreground=[("selected", ACCENT)])
        style.configure("TNotebook",       background=ACCENT, tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab",   background=ACCENT_LT, foreground=FG_LIGHT,
                        padding=[12, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", GOLD)],
                  foreground=[("selected", ACCENT)])

    # ------------------------------------------------------------------
    # UI layout
    # ------------------------------------------------------------------
    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────
        header = tk.Frame(self, bg=ACCENT, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        self._logo_label = tk.Label(header, bg=ACCENT)
        self._logo_label.pack(side="left", padx=12)
        self._update_header_logo()

        title_frame = tk.Frame(header, bg=ACCENT)
        title_frame.pack(side="left", fill="y", padx=8)
        tk.Label(title_frame, text=self.settings.hotel_name,
                 bg=ACCENT, fg=GOLD, font=("Georgia", 18, "bold")).pack(anchor="w", pady=(10, 0))
        tk.Label(title_frame, text="Sistema de Punto de Venta",
                 bg=ACCENT, fg="#aaa", font=("Helvetica", 9)).pack(anchor="w")

        # ── Notebook (tabs) ─────────────────────────────────────────
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True, padx=0, pady=0)

        tabs = [
            ("🏨 Habitaciones",  self._make_rooms_tab),
            ("📅 Reservas",      self._make_reservations_tab),
            ("👤 Huéspedes",     self._make_guests_tab),
            ("🍽️ Pedidos",       self._make_orders_tab),
            ("🧾 Facturación",   self._make_billing_tab),
            ("📦 Productos",     self._make_products_tab),
            ("📊 Reportes",      self._make_reports_tab),
            ("⚙️ Configuración", self._make_settings_tab),
        ]
        for tab_text, factory in tabs:
            frame = ttk.Frame(self._notebook)
            self._notebook.add(frame, text=tab_text)
            factory(frame)

    # ------------------------------------------------------------------
    # Tab factories
    # ------------------------------------------------------------------
    def _make_rooms_tab(self, parent):
        RoomsPanel(parent, self.settings).pack(fill="both", expand=True)

    def _make_reservations_tab(self, parent):
        ReservationsPanel(parent, self.settings).pack(fill="both", expand=True)

    def _make_guests_tab(self, parent):
        GuestsPanel(parent, self.settings).pack(fill="both", expand=True)

    def _make_orders_tab(self, parent):
        OrdersPanel(parent, self.settings).pack(fill="both", expand=True)

    def _make_billing_tab(self, parent):
        BillingPanel(parent, self.settings).pack(fill="both", expand=True)

    def _make_products_tab(self, parent):
        ProductsPanel(parent, self.settings).pack(fill="both", expand=True)

    def _make_reports_tab(self, parent):
        ReportsPanel(parent, self.settings).pack(fill="both", expand=True)

    def _make_settings_tab(self, parent):
        SettingsPanel(
            parent, self.settings,
            on_settings_changed=self._on_settings_changed,
        ).pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _on_settings_changed(self, new_settings):
        self.settings = new_settings
        self.title(f"{self.settings.hotel_name} – Sistema POS")
        self._update_header_logo()

    def _update_header_logo(self):
        logo_path = self.settings.logo_path
        if logo_path and os.path.isfile(logo_path) and PIL_AVAILABLE:
            try:
                img = Image.open(logo_path)
                img.thumbnail((48, 48))
                self._header_logo_img = ImageTk.PhotoImage(img)
                self._logo_label.config(image=self._header_logo_img, text="")
                return
            except Exception:
                pass
        # Fallback – gold star placeholder
        self._logo_label.config(image="", text="★", fg=GOLD,
                                font=("Georgia", 28, "bold"))
        self._header_logo_img = None


def main():
    app = HotelPOSApp()
    app.mainloop()


if __name__ == "__main__":
    main()
