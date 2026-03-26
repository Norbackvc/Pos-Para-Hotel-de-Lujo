"""
Hotel POS - Panel de Reportes
Estadísticas, reportes diarios y análisis de ingresos.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta

from . import database as db
from .widgets import StyledButton, SectionTitle, StyledTreeview


class ReportsPanel(tk.Frame):
    def __init__(self, parent, theme, app=None):
        super().__init__(parent, bg=theme["bg2"])
        self.theme = theme
        self.app = app
        self._build()
        self._load_today()

    def _build(self):
        t = self.theme

        top_bar = tk.Frame(self, bg=t["bg3"], pady=8)
        top_bar.pack(fill="x", padx=10, pady=(10, 0))
        SectionTitle(top_bar, "📊  Reportes y Estadísticas", theme=t).pack(side="left", padx=10)

        # Navegación de tabs
        tab_frame = tk.Frame(self, bg=t["bg2"])
        tab_frame.pack(fill="x", padx=10, pady=(6, 0))

        self._tab_buttons = {}
        tabs = [
            ("today", "📅 Hoy"),
            ("period", "📆 Por período"),
            ("rooms", "🏨 Ocupación"),
            ("guests", "👥 Huéspedes"),
        ]
        for key, label in tabs:
            btn = StyledButton(tab_frame, label,
                               command=lambda k=key: self._switch_tab(k),
                               theme=t, style="secondary")
            btn.pack(side="left", padx=2)
            self._tab_buttons[key] = btn

        # Contenedor de tabs
        self.tab_container = tk.Frame(self, bg=t["bg2"])
        self.tab_container.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_today_tab()
        self._build_period_tab()
        self._build_rooms_tab()
        self._build_guests_tab()

        self._current_tab = None
        self._switch_tab("today")

    # ── Construcción de tabs ──────────────────────────────────────────────────

    def _build_today_tab(self):
        t = self.theme
        self._today_frame = tk.Frame(self.tab_container, bg=t["bg2"])

        # KPIs
        kpi_row = tk.Frame(self._today_frame, bg=t["bg2"])
        kpi_row.pack(fill="x", pady=(0, 16))

        self._kpi_labels = {}
        kpis = [
            ("revenue", "💰 Ingresos Hoy", "$0.00"),
            ("invoices", "🧾 Facturas", "0"),
            ("checkins", "✅ Check-ins", "0"),
            ("checkouts", "🚪 Check-outs", "0"),
            ("occupied", "🛏 Habitaciones\nOcupadas", "0 / 0"),
        ]
        for key, label, default in kpis:
            card = tk.Frame(kpi_row, bg=t["card"], padx=16, pady=12, relief="flat")
            card.pack(side="left", padx=6, fill="both", expand=True)
            tk.Label(card, text=label, bg=t["card"], fg=t["fg2"],
                     font=(t["font"], 9)).pack()
            lbl = tk.Label(card, text=default, bg=t["card"], fg=t["accent"],
                           font=(t["font"], 16, "bold"))
            lbl.pack(pady=(4, 0))
            self._kpi_labels[key] = lbl

        btn_row = tk.Frame(self._today_frame, bg=t["bg2"])
        btn_row.pack(fill="x", pady=4)
        StyledButton(btn_row, "🔄 Actualizar", self._load_today,
                     theme=t, style="secondary").pack(side="left", padx=4)

        # Facturas del día
        tk.Label(self._today_frame, text="Facturas del Día",
                 bg=t["bg2"], fg=t["gold"],
                 font=(t["font"], 11, "bold")).pack(anchor="w", pady=(10, 4))

        cols = ("#", "Hab.", "Huésped", "Total", "Método", "Estado", "Hora")
        self.today_tree = StyledTreeview(self._today_frame,
                                         columns=cols, headings=cols, theme=t)
        self.today_tree.column("#", width=40)
        self.today_tree.column("Hab.", width=50)
        self.today_tree.column("Huésped", width=160)
        self.today_tree.column("Total", width=90)
        self.today_tree.column("Método", width=90)
        self.today_tree.column("Estado", width=75)
        self.today_tree.column("Hora", width=80)
        self.today_tree.pack(fill="both", expand=True)

    def _build_period_tab(self):
        t = self.theme
        self._period_frame = tk.Frame(self.tab_container, bg=t["bg2"])

        date_row = tk.Frame(self._period_frame, bg=t["bg2"])
        date_row.pack(fill="x", pady=(0, 8))

        today = date.today()
        first_of_month = today.replace(day=1)

        tk.Label(date_row, text="Desde:", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(side="left")
        self.e_start = tk.Entry(date_row, bg=t["entry_bg"], fg=t["fg"],
                                insertbackground=t["fg"], relief="flat", bd=4,
                                font=(t["font"], 10), width=12)
        self.e_start.insert(0, str(first_of_month))
        self.e_start.pack(side="left", padx=6)

        tk.Label(date_row, text="Hasta:", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(side="left")
        self.e_end = tk.Entry(date_row, bg=t["entry_bg"], fg=t["fg"],
                              insertbackground=t["fg"], relief="flat", bd=4,
                              font=(t["font"], 10), width=12)
        self.e_end.insert(0, str(today))
        self.e_end.pack(side="left", padx=6)

        StyledButton(date_row, "🔍 Buscar", self._load_period,
                     theme=t, style="primary").pack(side="left", padx=8)

        self.period_summary = tk.Label(self._period_frame,
                                       text="Selecciona un período y haz clic en Buscar.",
                                       bg=t["bg2"], fg=t["fg2"],
                                       font=(t["font"], 10))
        self.period_summary.pack(anchor="w", pady=4)

        cols = ("#", "Hab.", "Huésped", "Total", "Método", "Fecha")
        self.period_tree = StyledTreeview(self._period_frame,
                                          columns=cols, headings=cols, theme=t)
        for col, w in zip(cols, [40, 50, 170, 90, 90, 130]):
            self.period_tree.column(col, width=w)
        self.period_tree.pack(fill="both", expand=True)

    def _build_rooms_tab(self):
        t = self.theme
        self._rooms_frame = tk.Frame(self.tab_container, bg=t["bg2"])

        tk.Label(self._rooms_frame, text="Estado de Habitaciones",
                 bg=t["bg2"], fg=t["gold"],
                 font=(t["font"], 11, "bold")).pack(anchor="w", pady=(0, 8))

        StyledButton(self._rooms_frame, "🔄 Actualizar", self._load_rooms,
                     theme=t, style="secondary").pack(anchor="w", pady=4)

        cols = ("Hab.", "Tipo", "Piso", "Estado", "Precio/Noche", "Huésped actual")
        self.rooms_report_tree = StyledTreeview(self._rooms_frame,
                                                 columns=cols, headings=cols, theme=t)
        for col, w in zip(cols, [60, 120, 50, 100, 100, 180]):
            self.rooms_report_tree.column(col, width=w)
        self.rooms_report_tree.pack(fill="both", expand=True)

    def _build_guests_tab(self):
        t = self.theme
        self._guests_frame = tk.Frame(self.tab_container, bg=t["bg2"])

        top = tk.Frame(self._guests_frame, bg=t["bg2"])
        top.pack(fill="x", pady=(0, 8))

        tk.Label(top, text="Buscar:", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(side="left")
        self.guest_search_var = tk.StringVar()
        se = tk.Entry(top, textvariable=self.guest_search_var,
                      bg=t["entry_bg"], fg=t["fg"],
                      insertbackground=t["fg"], relief="flat", bd=4,
                      font=(t["font"], 10), width=24)
        se.pack(side="left", padx=6)
        se.bind("<KeyRelease>", lambda e: self._load_guests())
        StyledButton(top, "🔄 Todos", self._load_guests,
                     theme=t, style="secondary").pack(side="left", padx=4)

        cols = ("ID", "Nombre", "Documento", "Teléfono", "Email", "Nac.", "Registro")
        self.guests_tree = StyledTreeview(self._guests_frame,
                                          columns=cols, headings=cols, theme=t)
        for col, w in zip(cols, [40, 180, 100, 110, 170, 90, 110]):
            self.guests_tree.column(col, width=w)
        self.guests_tree.pack(fill="both", expand=True)

    # ── Carga de datos ────────────────────────────────────────────────────────

    def _switch_tab(self, tab_key):
        frames = {
            "today": self._today_frame,
            "period": self._period_frame,
            "rooms": self._rooms_frame,
            "guests": self._guests_frame,
        }
        t = self.theme
        for key, frame in frames.items():
            if key == tab_key:
                frame.pack(fill="both", expand=True)
                self._tab_buttons[key].config(bg=t["accent"])
            else:
                frame.pack_forget()
                self._tab_buttons[key].config(bg=t["button2_bg"])

        self._current_tab = tab_key
        if tab_key == "today":
            self._load_today()
        elif tab_key == "rooms":
            self._load_rooms()
        elif tab_key == "guests":
            self._load_guests()

    def _load_today(self):
        today_str = date.today().isoformat()
        summary = db.get_daily_summary(today_str)
        sym = db.get_all_config().get("currency_symbol", "$")

        self._kpi_labels["revenue"].config(
            text=f"{sym}{summary['revenue']:.2f}"
        )
        self._kpi_labels["invoices"].config(text=str(summary["invoices_count"]))
        self._kpi_labels["checkins"].config(text=str(summary["checkins"]))
        self._kpi_labels["checkouts"].config(text=str(summary["checkouts"]))
        self._kpi_labels["occupied"].config(
            text=f"{summary['occupied_rooms']} / {summary['total_rooms']}"
        )

        # Facturas del día
        self.today_tree.clear()
        invoices = db.get_revenue_by_period(today_str, today_str)
        for inv in invoices:
            self.today_tree.insert_row((
                inv["id"], inv["room_number"], inv["guest_name"],
                f"{sym}{inv['total']:.2f}", inv["payment_method"],
                inv["status"].upper(), inv["created_at"][11:16],
            ))

    def _load_period(self):
        start = self.e_start.get().strip()
        end = self.e_end.get().strip()
        try:
            datetime.strptime(start, "%Y-%m-%d")
            datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido. Usa YYYY-MM-DD.")
            return

        self.period_tree.clear()
        invoices = db.get_revenue_by_period(start, end)
        sym = db.get_all_config().get("currency_symbol", "$")
        total = sum(i["total"] for i in invoices)
        self.period_summary.config(
            text=f"{len(invoices)} facturas   |   Total: {sym}{total:.2f}"
        )
        for inv in invoices:
            self.period_tree.insert_row((
                inv["id"], inv["room_number"], inv["guest_name"],
                f"{sym}{inv['total']:.2f}", inv["payment_method"],
                inv["created_at"][:16],
            ))

    def _load_rooms(self):
        self.rooms_report_tree.clear()
        rooms = db.get_all_rooms()
        reservations = db.get_active_reservations()
        sym = db.get_all_config().get("currency_symbol", "$")
        res_by_room = {r["room_id"]: r["guest_name"] for r in reservations}
        for room in rooms:
            guest = res_by_room.get(room["id"], "—")
            self.rooms_report_tree.insert_row((
                room["number"], room["type"], room["floor"],
                room["status"].upper(),
                f"{sym}{room['price_night']:.2f}",
                guest,
            ))

    def _load_guests(self):
        self.guests_tree.clear()
        query = self.guest_search_var.get().strip() if hasattr(self, "guest_search_var") else ""
        guests = db.search_guests(query) if query else db.get_all_guests()
        for g in guests:
            self.guests_tree.insert_row((
                g["id"], g["name"], g["id_number"],
                g["phone"], g["email"], g["nationality"],
                g["created_at"][:10],
            ))
