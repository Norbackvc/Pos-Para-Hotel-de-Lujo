"""
Hotel POS - Panel de Facturación
Genera y gestiona facturas con logo del hotel.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    _LANCZOS = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
except ImportError:
    PIL_AVAILABLE = False
    _LANCZOS = None

from . import database as db
from .widgets import StyledButton, LabeledEntry, SectionTitle, StyledTreeview


class BillingPanel(tk.Frame):
    def __init__(self, parent, theme, app=None):
        super().__init__(parent, bg=theme["bg2"])
        self.theme = theme
        self.app = app
        self._build()
        self.refresh()

    def _build(self):
        t = self.theme

        top_bar = tk.Frame(self, bg=t["bg3"], pady=8)
        top_bar.pack(fill="x", padx=10, pady=(10, 0))
        SectionTitle(top_bar, "💳  Facturación y Cobros", theme=t).pack(side="left", padx=10)
        StyledButton(top_bar, "🔄 Actualizar", self.refresh,
                     theme=t, style="secondary").pack(side="right", padx=10)

        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=t["bg2"], sashwidth=4)
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Lista de reservas con check-out pendiente ──
        left = tk.Frame(paned, bg=t["bg2"])
        paned.add(left, minsize=320)

        tk.Label(left, text="Reservas Activas",
                 bg=t["bg2"], fg=t["gold"],
                 font=(t["font"], 11, "bold")).pack(pady=(0, 4))

        res_cols = ("ID", "Hab.", "Huésped", "Noches", "Total Hab.")
        self.res_tree = StyledTreeview(left, columns=res_cols,
                                       headings=res_cols, theme=t)
        self.res_tree.column("ID", width=40)
        self.res_tree.column("Hab.", width=55)
        self.res_tree.column("Huésped", width=160)
        self.res_tree.column("Noches", width=60)
        self.res_tree.column("Total Hab.", width=90)
        self.res_tree.pack(fill="both", expand=True)
        self.res_tree.bind("<<TreeviewSelect>>", self._on_reservation_select)

        StyledButton(left, "🧾 Generar Factura", self._generate_invoice,
                     theme=t, style="gold").pack(fill="x", pady=6)

        # ── Historial de facturas ──
        right = tk.Frame(paned, bg=t["bg2"])
        paned.add(right, minsize=360)

        tk.Label(right, text="Historial de Facturas",
                 bg=t["bg2"], fg=t["gold"],
                 font=(t["font"], 11, "bold")).pack(pady=(0, 4))

        inv_cols = ("#", "Hab.", "Huésped", "Total", "Método", "Estado", "Fecha")
        self.inv_tree = StyledTreeview(right, columns=inv_cols,
                                       headings=inv_cols, theme=t)
        self.inv_tree.column("#", width=40)
        self.inv_tree.column("Hab.", width=50)
        self.inv_tree.column("Huésped", width=130)
        self.inv_tree.column("Total", width=80)
        self.inv_tree.column("Método", width=80)
        self.inv_tree.column("Estado", width=75)
        self.inv_tree.column("Fecha", width=110)
        self.inv_tree.pack(fill="both", expand=True)

        inv_btns = tk.Frame(right, bg=t["bg2"])
        inv_btns.pack(fill="x", pady=6)
        StyledButton(inv_btns, "👁 Ver / Imprimir", self._view_invoice,
                     theme=t, style="primary").pack(side="left", padx=4)
        StyledButton(inv_btns, "✅ Marcar Pagada", self._mark_paid,
                     theme=t, style="success").pack(side="left", padx=4)

    def refresh(self):
        # Reservas activas
        self.res_tree.clear()
        reservations = db.get_active_reservations()
        self._reservations = reservations
        sym = db.get_all_config().get("currency_symbol", "$")
        for r in reservations:
            self.res_tree.insert_row((
                r["id"], r["room_number"], r["guest_name"],
                r["nights"], f"{sym}{r['total_room']:.2f}",
            ))
        # Facturas
        self.inv_tree.clear()
        invoices = db.get_all_invoices()
        self._invoices = invoices
        for inv in invoices:
            self.inv_tree.insert_row((
                inv["id"], inv["room_number"], inv["guest_name"],
                f"{sym}{inv['total']:.2f}", inv["payment_method"],
                inv["status"].upper(), inv["created_at"][:16],
            ))

    def _on_reservation_select(self, event):
        pass  # Se usa cuando se genera factura

    def _generate_invoice(self):
        sel = self.res_tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Selecciona una reserva para generar la factura.")
            return
        values = self.res_tree.item(sel[0], "values")
        res_id = int(values[0])
        reservation = db.get_reservation(res_id)
        if not reservation:
            return
        InvoiceDialog(self, self.theme, reservation, on_save=self.refresh)

    def _view_invoice(self):
        sel = self.inv_tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona una factura para ver.")
            return
        inv_id = int(self.inv_tree.item(sel[0], "values")[0])
        invoice = db.get_invoice(inv_id)
        if invoice:
            InvoiceViewDialog(self, self.theme, invoice)

    def _mark_paid(self):
        sel = self.inv_tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona una factura.")
            return
        inv_id = int(self.inv_tree.item(sel[0], "values")[0])
        invoice = db.get_invoice(inv_id)
        if invoice["status"] == "pagada":
            messagebox.showinfo("Ya pagada", "Esta factura ya está marcada como pagada.")
            return
        sym = db.get_all_config().get("currency_symbol", "$")
        if messagebox.askyesno(
            "Confirmar Pago",
            f"¿Marcar factura #{inv_id} como pagada?\nTotal: {sym}{invoice['total']:.2f}",
        ):
            db.pay_invoice(inv_id)
            messagebox.showinfo("Pagada", f"Factura #{inv_id} marcada como pagada.")
            self.refresh()


class InvoiceDialog(tk.Toplevel):
    """Diálogo para generar una nueva factura."""

    def __init__(self, parent, theme, reservation, on_save=None):
        super().__init__(parent)
        self.theme = theme
        self.reservation = reservation
        self.on_save = on_save
        t = theme
        self.title(f"Generar Factura — Hab. {reservation['room_number']}")
        self.configure(bg=t["bg2"])
        self.resizable(False, False)
        self.grab_set()
        self._build()
        self._center()

    def _build(self):
        t = self.theme
        r = self.reservation
        sym = db.get_all_config().get("currency_symbol", "$")

        tk.Label(self, text="Generar Factura",
                 bg=t["bg2"], fg=t["gold"],
                 font=(t["font"], 13, "bold")).pack(pady=(12, 4))

        # Datos del huésped
        info = tk.Frame(self, bg=t["card"])
        info.pack(fill="x", padx=16, pady=6)
        for label, value in [
            ("Huésped:", r["guest_name"]),
            ("Habitación:", f"{r['room_number']} ({r['room_type']})"),
            ("Noches:", str(r["nights"])),
            ("Total habitación:", f"{sym}{r['total_room']:.2f}"),
        ]:
            row = tk.Frame(info, bg=t["card"])
            row.pack(fill="x", padx=8, pady=2)
            tk.Label(row, text=label, bg=t["card"], fg=t["fg2"],
                     font=(t["font"], 9), width=18, anchor="w").pack(side="left")
            tk.Label(row, text=value, bg=t["card"], fg=t["fg"],
                     font=(t["font"], 9, "bold")).pack(side="left")

        # Órdenes/servicios cargados
        orders = db.get_orders_for_reservation(r["id"])
        services_total = sum(o["total"] for o in orders)

        tk.Label(self,
                 text=f"Cargos de servicios: {sym}{services_total:.2f}",
                 bg=t["bg2"], fg=t["fg"],
                 font=(t["font"], 10)).pack(padx=16, pady=4, anchor="w")

        cfg = db.get_all_config()
        tax_rate = float(cfg.get("tax_rate", "15"))
        subtotal = r["total_room"] + services_total
        tax = round(subtotal * tax_rate / 100, 2)
        total = round(subtotal + tax, 2)

        tk.Label(self,
                 text=f"Subtotal: {sym}{subtotal:.2f}   IVA ({tax_rate:.0f}%): {sym}{tax:.2f}",
                 bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(padx=16, anchor="w")
        tk.Label(self, text=f"TOTAL: {sym}{total:.2f}",
                 bg=t["bg2"], fg=t["accent"],
                 font=(t["font"], 14, "bold")).pack(padx=16, pady=4, anchor="w")

        # Método de pago
        tk.Label(self, text="Método de pago:", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(padx=16, anchor="w")
        self.payment_var = tk.StringVar(value="tarjeta")
        ttk.Combobox(
            self, textvariable=self.payment_var,
            values=["tarjeta", "efectivo", "transferencia", "cheque"],
            width=20, state="readonly",
        ).pack(padx=16, pady=(2, 8))

        btn_row = tk.Frame(self, bg=t["bg2"])
        btn_row.pack(pady=10)
        StyledButton(btn_row, "🧾 Crear Factura", self._create,
                     theme=t, style="gold").pack(side="left", padx=6)
        StyledButton(btn_row, "✖ Cancelar", self.destroy,
                     theme=t, style="secondary").pack(side="left", padx=6)

        self._services_total = services_total

    def _create(self):
        r = self.reservation
        cfg = db.get_all_config()
        inv_id = db.create_invoice(
            r["id"], r["guest_name"], r["room_number"],
            r["total_room"], self._services_total,
            float(cfg.get("tax_rate", "15")),
            self.payment_var.get(),
        )
        messagebox.showinfo("Factura Creada",
                            f"✔ Factura #{inv_id} creada con éxito.")
        self.destroy()
        if self.on_save:
            self.on_save()
        # Mostrar la factura
        invoice = db.get_invoice(inv_id)
        InvoiceViewDialog(self.master, self.theme, invoice)

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")


class InvoiceViewDialog(tk.Toplevel):
    """Vista de factura / recibo con logo del hotel."""

    def __init__(self, parent, theme, invoice):
        super().__init__(parent)
        self.theme = theme
        self.invoice = invoice
        t = theme
        self.title(f"Factura #{invoice['id']}")
        self.configure(bg="#ffffff")
        self.resizable(True, True)
        self._logo_img = None
        self._build()
        self._center()

    def _build(self):
        t = self.theme
        inv = self.invoice
        cfg = db.get_all_config()
        sym = cfg.get("currency_symbol", "$")

        # Marco del recibo (blanco para simular papel)
        receipt = tk.Frame(self, bg="#ffffff", padx=30, pady=20)
        receipt.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Encabezado con logo ──
        header = tk.Frame(receipt, bg="#ffffff")
        header.pack(fill="x", pady=(0, 10))

        # Logo
        logo_path = cfg.get("hotel_logo", "")
        if logo_path and os.path.isfile(logo_path) and PIL_AVAILABLE:
            try:
                img = Image.open(logo_path)
                img.thumbnail((100, 100), _LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                tk.Label(header, image=self._logo_img, bg="#ffffff").pack(side="left", padx=(0, 16))
            except Exception:
                pass

        hotel_info = tk.Frame(header, bg="#ffffff")
        hotel_info.pack(side="left")
        tk.Label(hotel_info, text=cfg.get("hotel_name", "Grand Luxe Hotel"),
                 bg="#ffffff", fg="#1a1a1a",
                 font=("Helvetica", 16, "bold")).pack(anchor="w")
        tk.Label(hotel_info, text=cfg.get("hotel_address", ""),
                 bg="#ffffff", fg="#555555",
                 font=("Helvetica", 9)).pack(anchor="w")
        tk.Label(hotel_info, text=cfg.get("hotel_phone", ""),
                 bg="#ffffff", fg="#555555",
                 font=("Helvetica", 9)).pack(anchor="w")
        tk.Label(hotel_info, text=cfg.get("hotel_email", ""),
                 bg="#ffffff", fg="#555555",
                 font=("Helvetica", 9)).pack(anchor="w")

        # Título factura
        tk.Frame(receipt, bg="#c9a84c", height=2).pack(fill="x", pady=8)
        title_row = tk.Frame(receipt, bg="#ffffff")
        title_row.pack(fill="x")
        tk.Label(title_row, text=f"FACTURA #{inv['id']:04d}",
                 bg="#ffffff", fg="#1a1a1a",
                 font=("Helvetica", 14, "bold")).pack(side="left")
        status_color = "#27ae60" if inv["status"] == "pagada" else "#f39c12"
        tk.Label(title_row, text=f"  [{inv['status'].upper()}]",
                 bg="#ffffff", fg=status_color,
                 font=("Helvetica", 11, "bold")).pack(side="left")
        tk.Label(title_row, text=inv["created_at"][:16],
                 bg="#ffffff", fg="#888888",
                 font=("Helvetica", 9)).pack(side="right")

        tk.Frame(receipt, bg="#c9a84c", height=1).pack(fill="x", pady=(8, 0))

        # Datos del huésped
        guest_frame = tk.Frame(receipt, bg="#f9f9f9", pady=6)
        guest_frame.pack(fill="x", pady=6)
        for label, value in [
            ("Huésped:", inv["guest_name"]),
            ("Habitación:", inv["room_number"]),
            ("Método de pago:", inv["payment_method"].upper()),
        ]:
            row = tk.Frame(guest_frame, bg="#f9f9f9")
            row.pack(fill="x", padx=8)
            tk.Label(row, text=label, bg="#f9f9f9", fg="#555555",
                     font=("Helvetica", 9), width=18, anchor="w").pack(side="left")
            tk.Label(row, text=value, bg="#f9f9f9", fg="#1a1a1a",
                     font=("Helvetica", 9, "bold")).pack(side="left")

        # Detalle de cargos
        tk.Label(receipt, text="DETALLE DE CARGOS",
                 bg="#ffffff", fg="#1a1a1a",
                 font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(8, 4))

        charges_frame = tk.Frame(receipt, bg="#ffffff")
        charges_frame.pack(fill="x")

        def charge_row(desc, amount, bold=False):
            row = tk.Frame(charges_frame, bg="#ffffff")
            row.pack(fill="x", pady=1)
            fw = "bold" if bold else "normal"
            tk.Label(row, text=desc, bg="#ffffff", fg="#1a1a1a",
                     font=("Helvetica", 10, fw), anchor="w").pack(side="left", fill="x", expand=True)
            tk.Label(row, text=f"{sym}{amount:.2f}", bg="#ffffff", fg="#1a1a1a",
                     font=("Helvetica", 10, fw)).pack(side="right")

        charge_row("Habitación", inv["room_total"])
        if inv["services_total"] > 0:
            charge_row("Servicios y cargos adicionales", inv["services_total"])

        tk.Frame(charges_frame, bg="#cccccc", height=1).pack(fill="x", pady=6)
        charge_row("Subtotal", inv["subtotal"])
        charge_row(f"IVA / Impuestos", inv["tax"])
        tk.Frame(charges_frame, bg="#c9a84c", height=2).pack(fill="x", pady=4)
        charge_row("TOTAL", inv["total"], bold=True)

        if inv["paid_at"]:
            tk.Label(receipt, text=f"✔ Pagado el {inv['paid_at'][:16]}",
                     bg="#ffffff", fg="#27ae60",
                     font=("Helvetica", 9, "bold")).pack(anchor="w", pady=6)

        tk.Frame(receipt, bg="#c9a84c", height=1).pack(fill="x", pady=8)
        tk.Label(receipt, text="¡Gracias por su preferencia! — Thank you for your stay!",
                 bg="#ffffff", fg="#888888",
                 font=("Helvetica", 9, "italic")).pack()

        # Botón cerrar
        StyledButton(self, "✖ Cerrar", self.destroy,
                     theme=self.theme, style="secondary").pack(pady=8)

    def _center(self):
        self.update_idletasks()
        w = max(self.winfo_width(), 480)
        h = max(self.winfo_height(), 600)
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
