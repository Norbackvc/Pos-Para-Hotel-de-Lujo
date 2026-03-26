"""
Billing / Invoice UI panel.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import modules.database as db
from modules.models import Invoice

PAYMENT_METHODS = ["CASH", "CREDIT_CARD", "DEBIT_CARD", "TRANSFER", "ROOM_CHARGE"]
PAYMENT_METHOD_LABELS = {
    "CASH":        "Efectivo",
    "CREDIT_CARD": "Tarjeta Crédito",
    "DEBIT_CARD":  "Tarjeta Débito",
    "TRANSFER":    "Transferencia",
    "ROOM_CHARGE": "Cargo a Habitación",
}


class BillingPanel(ttk.Frame):
    def __init__(self, parent, settings, **kwargs):
        super().__init__(parent, **kwargs)
        self.settings = settings
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=6)
        ttk.Button(toolbar, text="➕  Nueva Factura",  command=self._new_invoice).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🖨️  Imprimir/Ver",   command=self._print_invoice).pack(side="left", padx=4)
        ttk.Button(toolbar, text="✅  Marcar Pagada",  command=lambda: self._mark_paid()).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🔄  Actualizar",     command=self.refresh).pack(side="left", padx=4)

        cols = ("id", "folio", "guest", "room", "total", "method", "status", "date")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        headings = [
            ("id",     "#",          50),
            ("folio",  "Folio",     130),
            ("guest",  "Huésped",   180),
            ("room",   "Hab.",       70),
            ("total",  "Total",     100),
            ("method", "Método",    130),
            ("status", "Estado",    100),
            ("date",   "Fecha",     150),
        ]
        for col, text, width in headings:
            self._tree.heading(col, text=text)
            anchor = "e" if col == "total" else ("center" if col == "id" else "w")
            self._tree.column(col, width=width, anchor=anchor)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=4)
        vsb.pack(side="left", fill="y", pady=4)
        self._tree.bind("<Double-1>", lambda _: self._print_invoice())

        self._tree.tag_configure("PAID",      foreground="#27ae60")
        self._tree.tag_configure("PENDING",   foreground="#e67e22")
        self._tree.tag_configure("CANCELLED", foreground="#e74c3c")

    def refresh(self):
        self._tree.delete(*self._tree.get_children())
        sym = self.settings.currency_symbol
        for inv in db.get_invoices():
            self._tree.insert("", "end", iid=str(inv.id), tags=(inv.payment_status,), values=(
                inv.id, inv.folio_number, inv.guest_name, inv.room_number,
                f"{sym}{inv.total:,.2f}",
                PAYMENT_METHOD_LABELS.get(inv.payment_method, inv.payment_method),
                inv.payment_status,
                inv.created_at[:16],
            ))

    def _mark_paid(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selección", "Seleccione una factura.", parent=self)
            return
        inv = db.get_invoice(int(sel[0]))
        if inv:
            inv.payment_status = "PAID"
            db.save_invoice(inv)
            self.refresh()

    def _new_invoice(self):
        InvoiceDialog(self, self.settings, on_save=self.refresh)

    def _print_invoice(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selección", "Seleccione una factura.", parent=self)
            return
        inv = db.get_invoice(int(sel[0]))
        if inv:
            InvoicePreview(self, inv, self.settings)


class InvoiceDialog(tk.Toplevel):
    def __init__(self, parent, settings, on_save):
        super().__init__(parent)
        self.settings = settings
        self.on_save = on_save
        self.title("Nueva Factura")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        pad = {"padx": 8, "pady": 4}
        f = ttk.Frame(self, padding=10)
        f.pack(fill="both", expand=True)

        # Reservation selection
        ttk.Label(f, text="Reserva:").grid(row=0, column=0, sticky="e", **pad)
        reservations = db.get_all_reservations("CHECKED_IN") + db.get_all_reservations("CONFIRMED")
        self._res_options = {f"#{r.id} – {r.guest_name} (Hab. {r.room_number})": r.id for r in reservations}
        self._res_var = tk.StringVar()
        ttk.Combobox(f, textvariable=self._res_var, values=list(self._res_options.keys()), state="readonly", width=40).grid(row=0, column=1, sticky="ew", **pad)
        self._res_var.trace_add("write", lambda *_: self._update_total())

        # Open orders for the reservation
        ttk.Label(f, text="Cargos adicionales:").grid(row=1, column=0, sticky="ne", **pad)
        self._charges_listbox = tk.Listbox(f, height=5, selectmode="multiple", width=50)
        self._charges_listbox.grid(row=1, column=1, sticky="ew", **pad)
        self._charges_listbox.bind("<<ListboxSelect>>", lambda _: self._update_total())
        self._orders = []
        self._res_var.trace_add("write", lambda *_: self._load_orders())

        # Discount
        ttk.Label(f, text="Descuento:").grid(row=2, column=0, sticky="e", **pad)
        self._discount_var = tk.StringVar(value="0.00")
        ttk.Entry(f, textvariable=self._discount_var, width=12).grid(row=2, column=1, sticky="w", **pad)
        self._discount_var.trace_add("write", lambda *_: self._update_total())

        # Payment method
        ttk.Label(f, text="Método de Pago:").grid(row=3, column=0, sticky="e", **pad)
        self._payment_var = tk.StringVar(value="CASH")
        ttk.Combobox(f, textvariable=self._payment_var, values=PAYMENT_METHODS, state="readonly", width=26).grid(row=3, column=1, sticky="w", **pad)

        # Summary labels
        sym = self.settings.currency_symbol
        self._subtotal_var = tk.StringVar(value=f"{sym}0.00")
        self._tax_var      = tk.StringVar(value=f"{sym}0.00")
        self._total_var    = tk.StringVar(value=f"{sym}0.00")
        for label_text, var, row_n in [
            ("Subtotal:", self._subtotal_var, 4),
            (f"IVA ({self.settings.tax_rate:.0f}%):", self._tax_var, 5),
            ("Total:", self._total_var, 6),
        ]:
            ttk.Label(f, text=label_text).grid(row=row_n, column=0, sticky="e", **pad)
            ttk.Label(f, textvariable=var, font=("", 10, "bold")).grid(row=row_n, column=1, sticky="w", **pad)

        # Notes
        ttk.Label(f, text="Notas:").grid(row=7, column=0, sticky="ne", **pad)
        self._notes_text = tk.Text(f, width=40, height=3)
        self._notes_text.grid(row=7, column=1, sticky="ew", **pad)

        btn_frame = ttk.Frame(f)
        btn_frame.grid(row=8, columnspan=2, pady=8)
        ttk.Button(btn_frame, text="Generar Factura", command=self._save).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancelar",        command=self.destroy).pack(side="left", padx=6)

    def _load_orders(self):
        self._charges_listbox.delete(0, "end")
        self._orders = []
        label = self._res_var.get()
        if not label or label not in self._res_options:
            return
        res_id = self._res_options[label]
        orders = db.get_orders(status="OPEN", reservation_id=res_id)
        sym = self.settings.currency_symbol
        for order in orders:
            self._orders.append(order)
            self._charges_listbox.insert("end", f"#{order.id} {order.order_type} – {sym}{order.total:,.2f}")
        self._update_total()

    def _update_total(self):
        label = self._res_var.get()
        if not label or label not in self._res_options:
            return
        res_id = self._res_options[label]
        res = db.get_reservation(res_id)
        if not res:
            return
        # Nights
        try:
            ci = datetime.fromisoformat(res.check_in)
            co = datetime.fromisoformat(res.check_out)
            nights = max((co - ci).days, 1)
        except Exception:
            nights = 1
        room_charge = res.price_per_night * nights
        # Selected order charges
        selected = self._charges_listbox.curselection()
        order_charge = sum(self._orders[i].total for i in selected)
        try:
            discount = float(self._discount_var.get() or 0)
        except ValueError:
            discount = 0.0
        subtotal = room_charge + order_charge - discount
        tax = subtotal * self.settings.tax_rate / 100
        total = subtotal + tax
        sym = self.settings.currency_symbol
        self._subtotal_var.set(f"{sym}{subtotal:,.2f}")
        self._tax_var.set(f"{sym}{tax:,.2f}")
        self._total_var.set(f"{sym}{total:,.2f}")
        self._cached = {"subtotal": subtotal, "tax": tax, "total": total, "res": res, "orders": [self._orders[i] for i in selected]}

    def _save(self):
        try:
            if not hasattr(self, "_cached"):
                raise ValueError("Seleccione una reserva.")
            c = self._cached
            try:
                discount = float(self._discount_var.get() or 0)
            except ValueError:
                discount = 0.0
            invoice = Invoice(
                id=0, reservation_id=c["res"].id, folio_number="",
                subtotal=c["subtotal"], tax_rate=self.settings.tax_rate,
                tax_amount=c["tax"], discount=discount, total=c["total"],
                payment_method=self._payment_var.get(), payment_status="PENDING",
                notes=self._notes_text.get("1.0", "end-1c"),
                created_at=datetime.now().isoformat(),
            )
            db.save_invoice(invoice)
            # Close included orders
            for order in c["orders"]:
                order.status = "CLOSED"
                db.save_order(order)
            self.on_save()
            self.destroy()
        except (ValueError, AttributeError) as exc:
            messagebox.showerror("Error", str(exc), parent=self)


class InvoicePreview(tk.Toplevel):
    """A simple text-based invoice preview / print window."""

    def __init__(self, parent, invoice: Invoice, settings):
        super().__init__(parent)
        self.title(f"Factura {invoice.folio_number}")
        self.geometry("480x580")
        self.resizable(False, False)
        self.grab_set()

        sym = settings.currency_symbol
        lines = [
            "=" * 52,
            settings.hotel_name.center(52),
            settings.address.center(52),
            f"Tel: {settings.phone}   Email: {settings.email}".center(52),
            "=" * 52,
            f"Folio: {invoice.folio_number}",
            f"Fecha: {invoice.created_at[:16]}",
            f"Huésped: {invoice.guest_name}",
            f"Habitación: {invoice.room_number}",
            "-" * 52,
            f"Subtotal:          {sym}{invoice.subtotal:>12,.2f}",
            f"IVA ({invoice.tax_rate:.0f}%):          {sym}{invoice.tax_amount:>12,.2f}",
            f"Descuento:         {sym}{invoice.discount:>12,.2f}",
            "=" * 52,
            f"TOTAL:             {sym}{invoice.total:>12,.2f}",
            "=" * 52,
            f"Método de pago: {PAYMENT_METHOD_LABELS.get(invoice.payment_method, invoice.payment_method)}",
            f"Estado: {invoice.payment_status}",
            "",
            settings.invoice_footer.center(52),
            "=" * 52,
        ]
        text = tk.Text(self, font=("Courier", 10), wrap="none")
        text.insert("1.0", "\n".join(lines))
        text.config(state="disabled")
        text.pack(fill="both", expand=True, padx=8, pady=8)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=6)
        ttk.Button(btn_frame, text="Imprimir", command=self._print).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cerrar",   command=self.destroy).pack(side="left", padx=6)
        self._text_widget = text
        self._invoice = invoice
        self._settings = settings

    def _print(self):
        """Export invoice to a text file and open it."""
        import os
        import sys
        import tempfile
        path = os.path.join(tempfile.gettempdir(), f"factura_{self._invoice.folio_number}.txt")
        content = self._text_widget.get("1.0", "end")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", path], start_new_session=True)
            else:
                import subprocess
                subprocess.Popen(["xdg-open", path], start_new_session=True)
        except Exception:
            pass
        messagebox.showinfo("Factura guardada", f"Guardada en:\n{path}", parent=self)
