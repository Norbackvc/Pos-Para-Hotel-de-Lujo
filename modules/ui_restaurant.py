"""
Hotel POS - Panel de Restaurante / Bar
Gestión de órdenes del restaurante y servicio de bar.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from . import database as db
from .widgets import StyledButton, LabeledEntry, SectionTitle, StyledTreeview


class RestaurantPanel(tk.Frame):
    def __init__(self, parent, theme, app=None):
        super().__init__(parent, bg=theme["bg2"])
        self.theme = theme
        self.app = app
        self.current_order_id = None
        self.current_order_items = []
        self._build()
        self.refresh_open_orders()

    # ── Construcción ─────────────────────────────────────────────────────────

    def _build(self):
        t = self.theme

        # Barra superior
        top_bar = tk.Frame(self, bg=t["bg3"], pady=8)
        top_bar.pack(fill="x", padx=10, pady=(10, 0))
        SectionTitle(top_bar, "🍽  Restaurante & Bar", theme=t).pack(side="left", padx=10)

        btn_frame = tk.Frame(top_bar, bg=t["bg3"])
        btn_frame.pack(side="right", padx=10)
        StyledButton(btn_frame, "➕ Nueva Orden", self._new_order,
                     theme=t, style="success").pack(side="left", padx=4)
        StyledButton(btn_frame, "🔄 Actualizar", self.refresh_open_orders,
                     theme=t, style="secondary").pack(side="left", padx=4)

        # Layout principal
        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=t["bg2"], sashwidth=4, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Columna izquierda: órdenes abiertas ──
        left = tk.Frame(paned, bg=t["bg2"])
        paned.add(left, minsize=200)

        tk.Label(left, text="Órdenes Abiertas",
                 bg=t["bg2"], fg=t["gold"],
                 font=(t["font"], 11, "bold")).pack(pady=(0, 6))

        self.orders_list = tk.Listbox(
            left,
            bg=t["table_bg"], fg=t["fg"],
            selectbackground=t["table_sel"],
            font=(t["font"], 10),
            relief="flat", bd=0,
            activestyle="none",
        )
        self.orders_list.pack(fill="both", expand=True)
        self.orders_list.bind("<<ListboxSelect>>", self._on_order_select)

        # ── Columna central: menú ──
        center = tk.Frame(paned, bg=t["bg2"])
        paned.add(center, minsize=300)

        tk.Label(center, text="Menú",
                 bg=t["bg2"], fg=t["gold"],
                 font=(t["font"], 11, "bold")).pack(pady=(0, 4))

        # Filtro de categoría
        cat_row = tk.Frame(center, bg=t["bg2"])
        cat_row.pack(fill="x", pady=(0, 6))
        tk.Label(cat_row, text="Categoría:", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(side="left")
        self.cat_var = tk.StringVar(value="Todas")
        cats = ["Todas"] + db.get_menu_categories()
        self.cat_cb = ttk.Combobox(cat_row, textvariable=self.cat_var,
                                   values=cats, width=16, state="readonly")
        self.cat_cb.pack(side="left", padx=6)
        self.cat_cb.bind("<<ComboboxSelected>>", lambda e: self._load_menu())

        # Búsqueda
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(cat_row, textvariable=self.search_var,
                                bg=t["entry_bg"], fg=t["fg"],
                                insertbackground=t["fg"], relief="flat", bd=4,
                                font=(t["font"], 9), width=16)
        search_entry.pack(side="left", padx=4)
        search_entry.bind("<KeyRelease>", lambda e: self._load_menu())
        tk.Label(cat_row, text="🔍", bg=t["bg2"], fg=t["fg2"]).pack(side="left")

        # Tabla de menú
        menu_cols = ("ID", "Nombre", "Categoría", "Precio", "Descripción")
        self.menu_tree = StyledTreeview(
            center, columns=menu_cols, headings=menu_cols, theme=t
        )
        self.menu_tree.column("ID", width=40, minwidth=40)
        self.menu_tree.column("Nombre", width=160, minwidth=120)
        self.menu_tree.column("Categoría", width=100, minwidth=80)
        self.menu_tree.column("Precio", width=70, minwidth=60)
        self.menu_tree.column("Descripción", width=200, minwidth=100)
        self.menu_tree.pack(fill="both", expand=True)

        # Cantidad + agregar
        add_row = tk.Frame(center, bg=t["bg2"])
        add_row.pack(fill="x", pady=6)
        tk.Label(add_row, text="Cantidad:", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(side="left", padx=(0, 4))
        self.qty_var = tk.IntVar(value=1)
        tk.Spinbox(add_row, from_=1, to=99, textvariable=self.qty_var, width=5,
                   bg=t["entry_bg"], fg=t["fg"],
                   buttonbackground=t["bg3"]).pack(side="left")
        StyledButton(add_row, "➕ Agregar a orden", self._add_item_to_order,
                     theme=t, style="primary").pack(side="left", padx=8)

        self._load_menu()

        # ── Columna derecha: orden actual ──
        right = tk.Frame(paned, bg=t["card"])
        paned.add(right, minsize=240)

        tk.Label(right, text="Orden Actual",
                 bg=t["card"], fg=t["gold"],
                 font=(t["font"], 11, "bold")).pack(pady=(12, 4))

        self.order_label = tk.Label(right, text="Sin orden activa",
                                    bg=t["card"], fg=t["fg2"],
                                    font=(t["font"], 9))
        self.order_label.pack()

        # Items de la orden
        items_cols = ("Ítem", "Cant.", "Precio", "Subtotal")
        self.items_tree = StyledTreeview(
            right, columns=items_cols, headings=items_cols, theme=t
        )
        self.items_tree.column("Ítem", width=130, minwidth=100)
        self.items_tree.column("Cant.", width=40, minwidth=40)
        self.items_tree.column("Precio", width=65, minwidth=55)
        self.items_tree.column("Subtotal", width=70, minwidth=60)
        self.items_tree.pack(fill="both", expand=True, padx=8, pady=4)

        # Totales
        totals_frame = tk.Frame(right, bg=t["card"])
        totals_frame.pack(fill="x", padx=8)
        self.lbl_subtotal = tk.Label(totals_frame, text="Subtotal: $0.00",
                                     bg=t["card"], fg=t["fg2"],
                                     font=(t["font"], 9), anchor="e")
        self.lbl_subtotal.pack(fill="x")
        self.lbl_tax = tk.Label(totals_frame, text="IVA: $0.00",
                                bg=t["card"], fg=t["fg2"],
                                font=(t["font"], 9), anchor="e")
        self.lbl_tax.pack(fill="x")
        self.lbl_total = tk.Label(totals_frame, text="TOTAL: $0.00",
                                  bg=t["card"], fg=t["accent"],
                                  font=(t["font"], 12, "bold"), anchor="e")
        self.lbl_total.pack(fill="x", pady=(2, 6))

        # Botones de acción
        act_frame = tk.Frame(right, bg=t["card"])
        act_frame.pack(fill="x", padx=8, pady=4)
        StyledButton(act_frame, "🗑 Quitar ítem", self._remove_item,
                     theme=t, style="warning").pack(fill="x", pady=2)
        StyledButton(act_frame, "💳 Cobrar orden", self._close_order,
                     theme=t, style="success").pack(fill="x", pady=2)
        StyledButton(act_frame, "❌ Cancelar orden", self._cancel_order,
                     theme=t, style="danger").pack(fill="x", pady=2)

    # ── Menú ──────────────────────────────────────────────────────────────────

    def _load_menu(self):
        self.menu_tree.clear()
        cat = self.cat_var.get() if hasattr(self, "cat_var") else "Todas"
        query = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        items = db.get_menu_items(None if cat == "Todas" else cat)
        for item in items:
            if query and query not in item["name"].lower():
                continue
            sym = db.get_all_config().get("currency_symbol", "$")
            self.menu_tree.insert_row((
                item["id"], item["name"], item["category"],
                f"{sym}{item['price']:.2f}", item["description"],
            ))

    # ── Órdenes ───────────────────────────────────────────────────────────────

    def refresh_open_orders(self):
        self.orders_list.delete(0, "end")
        self._open_orders = db.get_open_orders()
        for order in self._open_orders:
            guest = order["guest_name"] or "Sin huésped"
            self.orders_list.insert(
                "end",
                f"#{order['id']}  {order['type']}  —  {guest}",
            )

    def _on_order_select(self, event):
        sel = self.orders_list.curselection()
        if not sel:
            return
        order = self._open_orders[sel[0]]
        self.current_order_id = order["id"]
        self.order_label.config(
            text=f"Orden #{order['id']} | {order['type']} | {order['created_at'][:16]}"
        )
        self._refresh_order_items()

    def _new_order(self):
        NewOrderDialog(self, self.theme, on_create=self._on_new_order_created)

    def _on_new_order_created(self, order_id):
        self.current_order_id = order_id
        self.refresh_open_orders()
        # Seleccionar la nueva orden
        for i, o in enumerate(self._open_orders):
            if o["id"] == order_id:
                self.orders_list.selection_clear(0, "end")
                self.orders_list.selection_set(i)
                self.orders_list.see(i)
                self._on_order_select(None)
                break

    def _add_item_to_order(self):
        if not self.current_order_id:
            messagebox.showwarning("Sin orden", "Crea o selecciona una orden primero.")
            return
        sel = self.menu_tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona un ítem del menú.")
            return
        values = self.menu_tree.item(sel[0], "values")
        item_name = values[1]
        category = values[2]
        price_sym = db.get_all_config().get("currency_symbol", "$")
        price_str = values[3].replace(price_sym, "").replace(",", "")
        price = float(price_str)
        qty = self.qty_var.get()
        db.add_order_item(self.current_order_id, item_name, category, qty, price)
        self._refresh_order_items()

    def _remove_item(self):
        sel = self.items_tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona un ítem para quitar.")
            return
        # get item ID from tag
        tags = self.items_tree.item(sel[0], "tags")
        if tags:
            db.remove_order_item(int(tags[0]))
            self._refresh_order_items()

    def _refresh_order_items(self):
        self.items_tree.clear()
        if not self.current_order_id:
            return
        sym = db.get_all_config().get("currency_symbol", "$")
        items = db.get_order_items(self.current_order_id)
        for item in items:
            iid = self.items_tree.insert(
                "", "end",
                values=(
                    item["item_name"], item["quantity"],
                    f"{sym}{item['unit_price']:.2f}",
                    f"{sym}{item['subtotal']:.2f}",
                ),
                tags=(str(item["id"]),),
            )
        order = db.get_order(self.current_order_id)
        if order:
            self.lbl_subtotal.config(text=f"Subtotal: {sym}{order['subtotal']:.2f}")
            self.lbl_tax.config(text=f"IVA: {sym}{order['tax']:.2f}")
            self.lbl_total.config(text=f"TOTAL: {sym}{order['total']:.2f}")

    def _close_order(self):
        if not self.current_order_id:
            messagebox.showwarning("Sin orden", "No hay orden activa.")
            return
        order = db.get_order(self.current_order_id)
        if order["subtotal"] == 0:
            messagebox.showwarning("Orden vacía", "La orden no tiene ítems.")
            return
        sym = db.get_all_config().get("currency_symbol", "$")
        if messagebox.askyesno(
            "Cobrar Orden",
            f"¿Cobrar orden #{self.current_order_id}?\nTotal: {sym}{order['total']:.2f}",
        ):
            db.close_order(self.current_order_id)
            messagebox.showinfo("Cobrado", f"Orden #{self.current_order_id} cobrada con éxito.")
            self.current_order_id = None
            self.order_label.config(text="Sin orden activa")
            self.items_tree.clear()
            self.lbl_subtotal.config(text="Subtotal: $0.00")
            self.lbl_tax.config(text="IVA: $0.00")
            self.lbl_total.config(text="TOTAL: $0.00")
            self.refresh_open_orders()

    def _cancel_order(self):
        if not self.current_order_id:
            return
        if messagebox.askyesno("Cancelar", f"¿Cancelar la orden #{self.current_order_id}?"):
            db.close_order(self.current_order_id)
            self.current_order_id = None
            self.order_label.config(text="Sin orden activa")
            self.items_tree.clear()
            self.refresh_open_orders()


class NewOrderDialog(tk.Toplevel):
    def __init__(self, parent, theme, on_create=None):
        super().__init__(parent)
        self.theme = theme
        self.on_create = on_create
        t = theme
        self.title("Nueva Orden")
        self.configure(bg=t["bg2"])
        self.resizable(False, False)
        self.grab_set()
        self._build()
        self._center()

    def _build(self):
        t = self.theme
        tk.Label(self, text="Nueva Orden",
                 bg=t["bg2"], fg=t["gold"],
                 font=(t["font"], 13, "bold")).pack(pady=(12, 6))

        # Tipo de orden
        tk.Label(self, text="Tipo de orden:", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(padx=20, anchor="w")
        self.type_var = tk.StringVar(value="Restaurante")
        ttk.Combobox(self, textvariable=self.type_var,
                     values=["Restaurante", "Bar", "Room Service", "Evento"],
                     width=22, state="readonly").pack(padx=20, pady=(2, 8))

        # Huésped (opcional)
        tk.Label(self, text="Huésped (opcional):", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(padx=20, anchor="w")

        self.guest_var = tk.StringVar()
        guests = db.get_all_guests()
        self._guests = guests
        guest_names = ["(Sin huésped)"] + [f"{g['name']} — {g['id_number']}" for g in guests]
        ttk.Combobox(self, textvariable=self.guest_var,
                     values=guest_names, width=32).pack(padx=20, pady=(2, 8))

        # Notas
        self.e_notes = LabeledEntry(self, "Notas", theme=t, width=30)
        self.e_notes.pack(padx=20, pady=4, fill="x")

        btn_row = tk.Frame(self, bg=t["bg2"])
        btn_row.pack(pady=10)
        StyledButton(btn_row, "✔ Crear Orden", self._create,
                     theme=t, style="success").pack(side="left", padx=6)
        StyledButton(btn_row, "✖ Cancelar", self.destroy,
                     theme=t, style="secondary").pack(side="left", padx=6)

    def _create(self):
        order_type = self.type_var.get()
        guest_id = None
        gv = self.guest_var.get()
        if gv and gv != "(Sin huésped)" and self._guests:
            idx = [f"{g['name']} — {g['id_number']}" for g in self._guests].index(gv)
            guest_id = self._guests[idx]["id"]

        order_id = db.create_order(order_type, guest_id=guest_id,
                                   notes=self.e_notes.get().strip())
        self.destroy()
        if self.on_create:
            self.on_create(order_id)

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
