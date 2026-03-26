"""
Orders (room service, restaurant, bar, spa, laundry) UI panel.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import modules.database as db
from modules.models import Order, OrderItem

ORDER_TYPES = ["ROOM_SERVICE", "RESTAURANT", "BAR", "SPA", "LAUNDRY"]
ORDER_TYPE_LABELS = {
    "ROOM_SERVICE": "Room Service",
    "RESTAURANT":   "Restaurante",
    "BAR":          "Bar",
    "SPA":          "Spa",
    "LAUNDRY":      "Lavandería",
}
CATEGORIES = ["ALL", "FOOD", "BEVERAGE", "SPA", "LAUNDRY", "MINIBAR", "OTHER"]


class OrdersPanel(ttk.Frame):
    def __init__(self, parent, settings, **kwargs):
        super().__init__(parent, **kwargs)
        self.settings = settings
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=6)
        ttk.Button(toolbar, text="➕  Nuevo Pedido",  command=self._new_order).pack(side="left", padx=4)
        ttk.Button(toolbar, text="✏️  Ver/Editar",    command=self._edit_order).pack(side="left", padx=4)
        ttk.Button(toolbar, text="✅  Cerrar Pedido", command=lambda: self._set_status("CLOSED")).pack(side="left", padx=4)
        ttk.Button(toolbar, text="❌  Cancelar",      command=lambda: self._set_status("CANCELLED")).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🔄  Actualizar",    command=self.refresh).pack(side="left", padx=4)

        filter_frame = ttk.LabelFrame(self, text="Filtrar")
        filter_frame.pack(fill="x", padx=10, pady=4)
        self._status_filter = tk.StringVar(value="OPEN")
        ttk.Radiobutton(filter_frame, text="Abiertos",   variable=self._status_filter, value="OPEN",      command=self.refresh).pack(side="left", padx=6)
        ttk.Radiobutton(filter_frame, text="Cerrados",   variable=self._status_filter, value="CLOSED",    command=self.refresh).pack(side="left", padx=6)
        ttk.Radiobutton(filter_frame, text="Cancelados", variable=self._status_filter, value="CANCELLED", command=self.refresh).pack(side="left", padx=6)
        ttk.Radiobutton(filter_frame, text="Todos",      variable=self._status_filter, value="ALL",       command=self.refresh).pack(side="left", padx=6)

        cols = ("id", "type", "room", "guest", "total", "status", "date")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        headings = [
            ("id",     "#",       60),
            ("type",   "Tipo",    130),
            ("room",   "Hab.",    80),
            ("guest",  "Huésped", 180),
            ("total",  "Total",   100),
            ("status", "Estado",  100),
            ("date",   "Fecha",   150),
        ]
        for col, text, width in headings:
            self._tree.heading(col, text=text)
            anchor = "e" if col == "total" else ("center" if col == "id" else "w")
            self._tree.column(col, width=width, anchor=anchor)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=4)
        vsb.pack(side="left", fill="y", pady=4)
        self._tree.bind("<Double-1>", lambda _: self._edit_order())

    def refresh(self):
        self._tree.delete(*self._tree.get_children())
        sf = self._status_filter.get()
        orders = db.get_orders(None if sf == "ALL" else sf)
        sym = self.settings.currency_symbol
        for order in orders:
            self._tree.insert("", "end", iid=str(order.id), values=(
                order.id,
                ORDER_TYPE_LABELS.get(order.order_type, order.order_type),
                order.room_number,
                order.guest_name,
                f"{sym}{order.total:,.2f}",
                order.status,
                order.created_at[:16],
            ))

    def _set_status(self, status: str):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selección", "Seleccione un pedido.", parent=self)
            return
        order = db.get_order(int(sel[0]))
        if order:
            order.status = status
            db.save_order(order)
            self.refresh()

    def _new_order(self):
        OrderDialog(self, None, self.settings, on_save=self.refresh)

    def _edit_order(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selección", "Seleccione un pedido.", parent=self)
            return
        order = db.get_order(int(sel[0]))
        OrderDialog(self, order, self.settings, on_save=self.refresh)


class OrderDialog(tk.Toplevel):
    def __init__(self, parent, order, settings, on_save):
        super().__init__(parent)
        self.order = order
        self.settings = settings
        self.on_save = on_save
        self.title("Nuevo Pedido" if order is None else f"Pedido #{order.id}")
        self.geometry("800x540")
        self.grab_set()
        self._items: list = list(order.items) if order else []
        self._build()

    def _build(self):
        sym = self.settings.currency_symbol
        main = ttk.Frame(self, padding=8)
        main.pack(fill="both", expand=True)

        # Top row – order metadata
        meta_frame = ttk.LabelFrame(main, text="Datos del Pedido")
        meta_frame.pack(fill="x", pady=4)

        ttk.Label(meta_frame, text="Tipo:").grid(row=0, column=0, padx=6, pady=4, sticky="e")
        self._type_var = tk.StringVar(value=self.order.order_type if self.order else "ROOM_SERVICE")
        ttk.Combobox(meta_frame, textvariable=self._type_var, values=ORDER_TYPES, state="readonly", width=18).grid(row=0, column=1, padx=6, pady=4, sticky="w")

        # Link to reservation (optional)
        ttk.Label(meta_frame, text="Habitación:").grid(row=0, column=2, padx=6, pady=4, sticky="e")
        rooms = [r for r in db.get_all_rooms() if r.status in ("OCCUPIED", "RESERVED")]
        self._room_options = {"—": None}
        self._room_options.update({r.number: r.id for r in rooms})
        self._room_var = tk.StringVar(value=self.order.room_number if self.order and self.order.room_number else "—")
        ttk.Combobox(meta_frame, textvariable=self._room_var, values=list(self._room_options.keys()), state="readonly", width=10).grid(row=0, column=3, padx=6, pady=4, sticky="w")

        ttk.Label(meta_frame, text="Notas:").grid(row=0, column=4, padx=6, pady=4, sticky="e")
        self._notes = tk.StringVar(value=self.order.notes if self.order else "")
        ttk.Entry(meta_frame, textvariable=self._notes, width=24).grid(row=0, column=5, padx=6, pady=4, sticky="ew")

        # Product catalogue
        left = ttk.LabelFrame(main, text="Productos")
        left.pack(side="left", fill="both", expand=True, padx=(0, 4))

        ttk.Label(left, text="Categoría:").pack(anchor="w", padx=6, pady=(6, 0))
        self._cat_var = tk.StringVar(value="ALL")
        ttk.Combobox(left, textvariable=self._cat_var, values=CATEGORIES, state="readonly", width=18).pack(anchor="w", padx=6)
        self._cat_var.trace_add("write", lambda *_: self._load_products())

        prod_cols = ("name", "cat", "price")
        self._prod_tree = ttk.Treeview(left, columns=prod_cols, show="headings", height=12)
        self._prod_tree.heading("name",  text="Nombre")
        self._prod_tree.heading("cat",   text="Categoría")
        self._prod_tree.heading("price", text="Precio")
        self._prod_tree.column("name",  width=160)
        self._prod_tree.column("cat",   width=90)
        self._prod_tree.column("price", width=80, anchor="e")
        self._prod_tree.pack(fill="both", expand=True, padx=6, pady=4)

        qty_frame = ttk.Frame(left)
        qty_frame.pack(padx=6, pady=4, fill="x")
        ttk.Label(qty_frame, text="Cantidad:").pack(side="left")
        self._qty_var = tk.StringVar(value="1")
        ttk.Spinbox(qty_frame, from_=1, to=99, textvariable=self._qty_var, width=5).pack(side="left", padx=4)
        ttk.Button(qty_frame, text="➕ Agregar", command=self._add_item).pack(side="left", padx=4)

        # Order items
        right = ttk.LabelFrame(main, text="Artículos del Pedido")
        right.pack(side="left", fill="both", expand=True, padx=(4, 0))

        item_cols = ("name", "qty", "price", "subtotal")
        self._item_tree = ttk.Treeview(right, columns=item_cols, show="headings", height=14)
        self._item_tree.heading("name",    text="Producto")
        self._item_tree.heading("qty",     text="Cant.")
        self._item_tree.heading("price",   text="Precio")
        self._item_tree.heading("subtotal",text="Subtotal")
        self._item_tree.column("name",    width=160)
        self._item_tree.column("qty",     width=50, anchor="center")
        self._item_tree.column("price",   width=80, anchor="e")
        self._item_tree.column("subtotal",width=90, anchor="e")
        self._item_tree.pack(fill="both", expand=True, padx=6, pady=4)
        ttk.Button(right, text="🗑️ Quitar seleccionado", command=self._remove_item).pack(pady=(0, 4))

        self._total_label = ttk.Label(right, text=f"Total: {sym}0.00", font=("", 12, "bold"))
        self._total_label.pack(pady=4)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=6)
        ttk.Button(btn_frame, text="💾 Guardar Pedido", command=self._save).pack(side="right", padx=6)
        ttk.Button(btn_frame, text="Cancelar",           command=self.destroy).pack(side="right", padx=4)

        self._load_products()
        self._refresh_items()

    def _load_products(self):
        self._prod_tree.delete(*self._prod_tree.get_children())
        cat = self._cat_var.get()
        products = db.get_all_products(None if cat == "ALL" else cat)
        sym = self.settings.currency_symbol
        self._products = {str(p.id): p for p in products}
        for p in products:
            self._prod_tree.insert("", "end", iid=str(p.id), values=(
                p.name, p.category, f"{sym}{p.price:,.2f}"
            ))

    def _add_item(self):
        sel = self._prod_tree.selection()
        if not sel:
            messagebox.showinfo("Selección", "Seleccione un producto.", parent=self)
            return
        product = self._products.get(sel[0])
        if not product:
            return
        try:
            qty = int(self._qty_var.get())
        except ValueError:
            qty = 1
        # If same product already in list, increase quantity
        for item in self._items:
            if item.product_id == product.id:
                item.quantity += qty
                item.subtotal = item.quantity * item.unit_price
                self._refresh_items()
                return
        self._items.append(OrderItem(
            id=0, order_id=0, product_id=product.id, quantity=qty,
            unit_price=product.price, subtotal=qty * product.price,
            product_name=product.name,
        ))
        self._refresh_items()

    def _remove_item(self):
        sel = self._item_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        self._items.pop(idx)
        self._refresh_items()

    def _refresh_items(self):
        self._item_tree.delete(*self._item_tree.get_children())
        sym = self.settings.currency_symbol
        total = 0.0
        for idx, item in enumerate(self._items):
            self._item_tree.insert("", "end", iid=str(idx), values=(
                item.product_name, item.quantity,
                f"{sym}{item.unit_price:,.2f}", f"{sym}{item.subtotal:,.2f}",
            ))
            total += item.subtotal
        self._total_label.config(text=f"Total: {sym}{total:,.2f}")

    def _save(self):
        room_id = self._room_options.get(self._room_var.get())
        total = sum(i.subtotal for i in self._items)
        if self.order is None:
            order = Order(
                id=0, reservation_id=None, room_id=room_id,
                order_type=self._type_var.get(), status="OPEN",
                total=total, notes=self._notes.get(),
                created_at=datetime.now().isoformat(),
                items=self._items,
            )
        else:
            self.order.room_id = room_id
            self.order.order_type = self._type_var.get()
            self.order.total = total
            self.order.notes = self._notes.get()
            self.order.items = self._items
            order = self.order
        db.save_order(order)
        self.on_save()
        self.destroy()
