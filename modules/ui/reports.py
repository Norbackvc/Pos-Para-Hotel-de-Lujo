"""
Reports UI panel.
"""
import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta

import modules.database as db


class ReportsPanel(ttk.Frame):
    def __init__(self, parent, settings, **kwargs):
        super().__init__(parent, **kwargs)
        self.settings = settings
        self._build_ui()
        self._load_reports()

    def _build_ui(self):
        # Date range
        range_frame = ttk.LabelFrame(self, text="Rango de Fechas")
        range_frame.pack(fill="x", padx=10, pady=8)

        ttk.Label(range_frame, text="Desde:").pack(side="left", padx=6)
        self._from_var = tk.StringVar(value=(date.today() - timedelta(days=30)).isoformat())
        ttk.Entry(range_frame, textvariable=self._from_var, width=12).pack(side="left", padx=4)

        ttk.Label(range_frame, text="Hasta:").pack(side="left", padx=6)
        self._to_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(range_frame, textvariable=self._to_var, width=12).pack(side="left", padx=4)

        ttk.Button(range_frame, text="📊  Actualizar Reportes", command=self._load_reports).pack(side="left", padx=10)

        # Two-column layout
        columns_frame = ttk.Frame(self)
        columns_frame.pack(fill="both", expand=True, padx=10, pady=6)

        # ── Occupancy ──────────────────────────────────────────────
        occ_frame = ttk.LabelFrame(columns_frame, text="Ocupación Actual")
        occ_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self._occ_text = tk.Text(occ_frame, height=12, state="disabled", font=("Courier", 10))
        self._occ_text.pack(fill="both", expand=True, padx=6, pady=6)

        # ── Revenue ────────────────────────────────────────────────
        rev_frame = ttk.LabelFrame(columns_frame, text="Ingresos del Período")
        rev_frame.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self._rev_text = tk.Text(rev_frame, height=12, state="disabled", font=("Courier", 10))
        self._rev_text.pack(fill="both", expand=True, padx=6, pady=6)

        # ── Recent invoices table ──────────────────────────────────
        inv_frame = ttk.LabelFrame(self, text="Últimas Facturas Pagadas")
        inv_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        cols = ("folio", "guest", "room", "total", "method", "date")
        self._inv_tree = ttk.Treeview(inv_frame, columns=cols, show="headings", height=7)
        headings = [
            ("folio",  "Folio",    130),
            ("guest",  "Huésped",  180),
            ("room",   "Hab.",      70),
            ("total",  "Total",    100),
            ("method", "Método",   130),
            ("date",   "Fecha",    150),
        ]
        for col, text, width in headings:
            self._inv_tree.heading(col, text=text)
            self._inv_tree.column(col, width=width, anchor="e" if col == "total" else "w")
        vsb = ttk.Scrollbar(inv_frame, orient="vertical", command=self._inv_tree.yview)
        self._inv_tree.configure(yscrollcommand=vsb.set)
        self._inv_tree.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        vsb.pack(side="left", fill="y", pady=6)

    def _load_reports(self):
        sym = self.settings.currency_symbol
        start = self._from_var.get()
        end   = self._to_var.get()

        # Occupancy
        occ = db.report_occupancy()
        occ_lines = [
            f"Total habitaciones : {occ['total']:>4}",
            f"Disponibles        : {occ['available']:>4}",
            f"Ocupadas           : {occ['occupied']:>4}",
            f"Reservadas         : {occ['reserved']:>4}",
            f"Mantenimiento      : {occ['maintenance']:>4}",
            "",
            f"Tasa de ocupación  : {occ['occupancy_rate']:>4}%",
        ]
        self._set_text(self._occ_text, "\n".join(occ_lines))

        # Revenue
        rev = db.report_revenue(start, end)
        rev_lines = [
            f"Ingresos totales : {sym}{rev['total']:>12,.2f}",
            f"Facturas pagadas : {rev['count']:>4}",
            "",
            "── Por método de pago ──",
        ]
        for method, amount in rev["by_method"].items():
            rev_lines.append(f"  {method:<18}: {sym}{amount:>10,.2f}")
        self._set_text(self._rev_text, "\n".join(rev_lines))

        # Recent invoices
        self._inv_tree.delete(*self._inv_tree.get_children())
        from modules.ui.billing import PAYMENT_METHOD_LABELS
        for inv in db.get_invoices():
            if inv.payment_status != "PAID":
                continue
            self._inv_tree.insert("", "end", values=(
                inv.folio_number, inv.guest_name, inv.room_number,
                f"{sym}{inv.total:,.2f}",
                PAYMENT_METHOD_LABELS.get(inv.payment_method, inv.payment_method),
                inv.created_at[:16],
            ))

    @staticmethod
    def _set_text(widget: tk.Text, content: str):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.config(state="disabled")
