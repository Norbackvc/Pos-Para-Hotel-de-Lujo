"""
Products catalogue management UI panel.
"""
import tkinter as tk
from tkinter import ttk, messagebox

import modules.database as db
from modules.models import Product

CATEGORIES = ["FOOD", "BEVERAGE", "SPA", "LAUNDRY", "MINIBAR", "OTHER"]
CATEGORY_LABELS = {
    "FOOD":     "Alimentos",
    "BEVERAGE": "Bebidas",
    "SPA":      "Spa",
    "LAUNDRY":  "Lavandería",
    "MINIBAR":  "Minibar",
    "OTHER":    "Otro",
}


class ProductsPanel(ttk.Frame):
    def __init__(self, parent, settings, **kwargs):
        super().__init__(parent, **kwargs)
        self.settings = settings
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=6)
        ttk.Button(toolbar, text="➕  Nuevo Producto", command=self._new_product).pack(side="left", padx=4)
        ttk.Button(toolbar, text="✏️  Editar",          command=self._edit_product).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🔄  Actualizar",      command=self.refresh).pack(side="left", padx=4)

        filter_frame = ttk.LabelFrame(self, text="Categoría")
        filter_frame.pack(fill="x", padx=10, pady=4)
        self._cat_filter = tk.StringVar(value="ALL")
        ttk.Radiobutton(filter_frame, text="Todos", variable=self._cat_filter, value="ALL", command=self.refresh).pack(side="left", padx=6)
        for cat, label in CATEGORY_LABELS.items():
            ttk.Radiobutton(filter_frame, text=label, variable=self._cat_filter, value=cat, command=self.refresh).pack(side="left", padx=6)

        cols = ("id", "name", "category", "price", "stock", "unit")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        headings = [
            ("id",       "#",         50),
            ("name",     "Nombre",   200),
            ("category", "Categoría",120),
            ("price",    "Precio",   100),
            ("stock",    "Stock",     70),
            ("unit",     "Unidad",    80),
        ]
        for col, text, width in headings:
            self._tree.heading(col, text=text)
            anchor = "e" if col == "price" else ("center" if col in ("id", "stock") else "w")
            self._tree.column(col, width=width, anchor=anchor)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=4)
        vsb.pack(side="left", fill="y", pady=4)
        self._tree.bind("<Double-1>", lambda _: self._edit_product())

    def refresh(self):
        self._tree.delete(*self._tree.get_children())
        cat = self._cat_filter.get()
        products = db.get_all_products(None if cat == "ALL" else cat)
        sym = self.settings.currency_symbol
        for p in products:
            self._tree.insert("", "end", iid=str(p.id), values=(
                p.id, p.name, CATEGORY_LABELS.get(p.category, p.category),
                f"{sym}{p.price:,.2f}", p.stock, p.unit,
            ))

    def _new_product(self):
        ProductDialog(self, Product(0, "", "FOOD", 0.0), self.settings, on_save=self.refresh)

    def _edit_product(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selección", "Seleccione un producto.", parent=self)
            return
        products = db.get_all_products()
        product = next((p for p in products if str(p.id) == sel[0]), None)
        if product:
            ProductDialog(self, product, self.settings, on_save=self.refresh)


class ProductDialog(tk.Toplevel):
    def __init__(self, parent, product: Product, settings, on_save):
        super().__init__(parent)
        self.product = product
        self.settings = settings
        self.on_save = on_save
        self.title("Nuevo Producto" if product.id == 0 else f"Producto: {product.name}")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        pad = {"padx": 8, "pady": 4}
        f = ttk.Frame(self, padding=10)
        f.pack(fill="both", expand=True)

        fields = [
            ("Nombre:", "name"),
            ("Precio:", "price"),
            ("Stock:", "stock"),
            ("Unidad:", "unit"),
            ("Descripción:", "description"),
        ]
        self._vars = {}
        for row_idx, (label, key) in enumerate(fields):
            ttk.Label(f, text=label).grid(row=row_idx, column=0, sticky="e", **pad)
            var = tk.StringVar(value=str(getattr(self.product, key, "")))
            self._vars[key] = var
            ttk.Entry(f, textvariable=var, width=28).grid(row=row_idx, column=1, sticky="ew", **pad)

        row_idx += 1
        ttk.Label(f, text="Categoría:").grid(row=row_idx, column=0, sticky="e", **pad)
        self._cat_var = tk.StringVar(value=self.product.category)
        ttk.Combobox(f, textvariable=self._cat_var, values=CATEGORIES, state="readonly", width=26).grid(row=row_idx, column=1, sticky="ew", **pad)

        row_idx += 1
        self._active_var = tk.BooleanVar(value=self.product.active)
        ttk.Checkbutton(f, text="Activo", variable=self._active_var).grid(row=row_idx, column=1, sticky="w", **pad)

        row_idx += 1
        btn_frame = ttk.Frame(f)
        btn_frame.grid(row=row_idx, columnspan=2, pady=8)
        ttk.Button(btn_frame, text="Guardar",  command=self._save).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=6)

    def _save(self):
        try:
            self.product.name = self._vars["name"].get().strip()
            self.product.price = float(self._vars["price"].get())
            self.product.stock = int(self._vars["stock"].get() or 0)
            self.product.unit = self._vars["unit"].get().strip() or "unit"
            self.product.description = self._vars["description"].get().strip()
            self.product.category = self._cat_var.get()
            self.product.active = self._active_var.get()
            if not self.product.name:
                raise ValueError("El nombre es obligatorio.")
            db.save_product(self.product)
            self.on_save()
            self.destroy()
        except ValueError as exc:
            messagebox.showerror("Error", str(exc), parent=self)
