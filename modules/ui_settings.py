"""
Hotel POS - Panel de Configuración
Ajustes del hotel: nombre, logo, impuesto, moneda, tema.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    _LANCZOS = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
except ImportError:
    PIL_AVAILABLE = False
    _LANCZOS = None

from . import database as db
from .widgets import StyledButton, LabeledEntry, SectionTitle


class SettingsPanel(tk.Frame):
    def __init__(self, parent, theme, app=None):
        super().__init__(parent, bg=theme["bg2"])
        self.theme = theme
        self.app = app
        self._logo_img = None
        self._build()
        self._load()

    def _build(self):
        t = self.theme

        top_bar = tk.Frame(self, bg=t["bg3"], pady=8)
        top_bar.pack(fill="x", padx=10, pady=(10, 0))
        SectionTitle(top_bar, "⚙  Configuración del Hotel", theme=t).pack(side="left", padx=10)

        # Scroll
        canvas = tk.Canvas(self, bg=t["bg2"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=t["bg2"])
        self.inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._build_hotel_info()
        self._build_logo_section()
        self._build_billing_settings()
        self._build_theme_settings()
        self._build_menu_manager()

        # Botón guardar
        StyledButton(self.inner, "💾 Guardar Configuración", self._save,
                     theme=t, style="gold", width=30).pack(pady=16)

    def _build_hotel_info(self):
        t = self.theme
        frame = tk.LabelFrame(self.inner, text="Información del Hotel",
                              bg=t["bg2"], fg=t["gold"],
                              font=(t["font"], 10, "bold"), padx=12, pady=8)
        frame.pack(fill="x", padx=16, pady=(16, 8))

        self.e_name = LabeledEntry(frame, "Nombre del Hotel", theme=t, width=36)
        self.e_name.pack(fill="x", pady=4)
        self.e_address = LabeledEntry(frame, "Dirección", theme=t, width=50)
        self.e_address.pack(fill="x", pady=4)

        row = tk.Frame(frame, bg=t["bg2"])
        row.pack(fill="x", pady=4)
        self.e_phone = LabeledEntry(row, "Teléfono", theme=t, width=20)
        self.e_phone.pack(side="left", padx=(0, 12))
        self.e_email = LabeledEntry(row, "Email", theme=t, width=30)
        self.e_email.pack(side="left")

    def _build_logo_section(self):
        t = self.theme
        frame = tk.LabelFrame(self.inner, text="Logo del Hotel",
                              bg=t["bg2"], fg=t["gold"],
                              font=(t["font"], 10, "bold"), padx=12, pady=8)
        frame.pack(fill="x", padx=16, pady=8)

        desc = tk.Label(frame,
                        text="El logo aparecerá en el encabezado del sistema y en las facturas.",
                        bg=t["bg2"], fg=t["fg2"],
                        font=(t["font"], 9))
        desc.pack(anchor="w", pady=(0, 8))

        logo_content = tk.Frame(frame, bg=t["bg2"])
        logo_content.pack(fill="x")

        # Vista previa del logo
        self.logo_preview = tk.Label(
            logo_content,
            text="Sin logo\n(haz clic en Seleccionar)",
            bg=t["entry_bg"], fg=t["fg2"],
            font=(t["font"], 9),
            width=16, height=6,
            relief="flat",
        )
        self.logo_preview.pack(side="left", padx=(0, 16))

        right_col = tk.Frame(logo_content, bg=t["bg2"])
        right_col.pack(side="left", fill="both", expand=True)

        self.e_logo = LabeledEntry(right_col, "Ruta del logo", theme=t, width=44)
        self.e_logo.pack(fill="x", pady=(0, 8))

        btn_row = tk.Frame(right_col, bg=t["bg2"])
        btn_row.pack(fill="x")
        StyledButton(btn_row, "📁 Seleccionar Logo",
                     self._browse_logo, theme=t, style="secondary").pack(side="left", padx=(0, 8))
        StyledButton(btn_row, "🗑 Quitar Logo",
                     self._clear_logo, theme=t, style="warning").pack(side="left")

        tk.Label(right_col,
                 text="Formatos soportados: PNG, JPG, GIF, BMP\nRecomendado: PNG transparente, máx. 300×300 px",
                 bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 8),
                 justify="left").pack(anchor="w", pady=(8, 0))

    def _build_billing_settings(self):
        t = self.theme
        frame = tk.LabelFrame(self.inner, text="Configuración de Facturación",
                              bg=t["bg2"], fg=t["gold"],
                              font=(t["font"], 10, "bold"), padx=12, pady=8)
        frame.pack(fill="x", padx=16, pady=8)

        row = tk.Frame(frame, bg=t["bg2"])
        row.pack(fill="x", pady=4)

        self.e_currency = LabeledEntry(row, "Moneda (ej: USD, EUR, MXN)", theme=t, width=10)
        self.e_currency.pack(side="left", padx=(0, 12))
        self.e_currency_symbol = LabeledEntry(row, "Símbolo (ej: $, €)", theme=t, width=6)
        self.e_currency_symbol.pack(side="left", padx=(0, 12))
        self.e_tax = LabeledEntry(row, "IVA / Impuesto (%)", theme=t, width=8)
        self.e_tax.pack(side="left")

    def _build_theme_settings(self):
        t = self.theme
        frame = tk.LabelFrame(self.inner, text="Apariencia",
                              bg=t["bg2"], fg=t["gold"],
                              font=(t["font"], 10, "bold"), padx=12, pady=8)
        frame.pack(fill="x", padx=16, pady=8)

        row = tk.Frame(frame, bg=t["bg2"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text="Tema:", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(side="left")
        self.theme_var = tk.StringVar(value="dark")
        ttk.Combobox(row, textvariable=self.theme_var,
                     values=["dark", "light"],
                     width=12, state="readonly").pack(side="left", padx=8)
        tk.Label(row, text="(El cambio de tema requiere reiniciar la aplicación)",
                 bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 8, "italic")).pack(side="left")

    def _build_menu_manager(self):
        t = self.theme
        frame = tk.LabelFrame(self.inner, text="Gestión del Menú",
                              bg=t["bg2"], fg=t["gold"],
                              font=(t["font"], 10, "bold"), padx=12, pady=8)
        frame.pack(fill="x", padx=16, pady=8)

        tk.Label(frame,
                 text="Agrega, edita o elimina ítems del menú del restaurante.",
                 bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(anchor="w", pady=(0, 8))

        # Nueva entrada de menú
        row1 = tk.Frame(frame, bg=t["bg2"])
        row1.pack(fill="x", pady=4)
        self.me_name = LabeledEntry(row1, "Nombre del ítem", theme=t, width=24)
        self.me_name.pack(side="left", padx=(0, 8))

        col_frame = tk.Frame(row1, bg=t["bg2"])
        col_frame.pack(side="left")
        tk.Label(col_frame, text="Categoría", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(anchor="w")
        self.me_cat = tk.StringVar()
        ttk.Combobox(
            col_frame, textvariable=self.me_cat,
            values=["Desayunos", "Entradas", "Principales", "Postres", "Bebidas", "Bar", "Otro"],
            width=16,
        ).pack(pady=(2, 0))

        row2 = tk.Frame(frame, bg=t["bg2"])
        row2.pack(fill="x", pady=4)
        self.me_price = LabeledEntry(row2, "Precio", theme=t, width=10)
        self.me_price.pack(side="left", padx=(0, 8))
        self.me_desc = LabeledEntry(row2, "Descripción", theme=t, width=36)
        self.me_desc.pack(side="left")

        StyledButton(frame, "➕ Agregar al Menú", self._add_menu_item,
                     theme=t, style="primary").pack(anchor="w", pady=6)

        # Lista del menú actual
        from .widgets import StyledTreeview
        cols = ("ID", "Nombre", "Categoría", "Precio", "Disponible")
        self.menu_tree = StyledTreeview(frame, columns=cols, headings=cols, theme=t)
        self.menu_tree.column("ID", width=40)
        self.menu_tree.column("Nombre", width=180)
        self.menu_tree.column("Categoría", width=100)
        self.menu_tree.column("Precio", width=80)
        self.menu_tree.column("Disponible", width=80)
        self.menu_tree.pack(fill="x", pady=4)

        del_row = tk.Frame(frame, bg=t["bg2"])
        del_row.pack(fill="x", pady=4)
        StyledButton(del_row, "🔄 Refrescar lista", self._refresh_menu,
                     theme=t, style="secondary").pack(side="left", padx=4)
        StyledButton(del_row, "🗑 Eliminar seleccionado", self._delete_menu_item,
                     theme=t, style="danger").pack(side="left", padx=4)

        self._refresh_menu()

    # ── Carga y guardado ──────────────────────────────────────────────────────

    def _load(self):
        cfg = db.get_all_config()
        self.e_name.set(cfg.get("hotel_name", ""))
        self.e_address.set(cfg.get("hotel_address", ""))
        self.e_phone.set(cfg.get("hotel_phone", ""))
        self.e_email.set(cfg.get("hotel_email", ""))
        self.e_currency.set(cfg.get("currency", "USD"))
        self.e_currency_symbol.set(cfg.get("currency_symbol", "$"))
        self.e_tax.set(cfg.get("tax_rate", "15"))
        self.theme_var.set(cfg.get("theme", "dark"))

        logo_path = cfg.get("hotel_logo", "")
        self.e_logo.set(logo_path)
        self._preview_logo(logo_path)

    def _save(self):
        # Validar impuesto
        try:
            float(self.e_tax.get())
        except ValueError:
            messagebox.showerror("Error", "El impuesto debe ser un número.")
            return

        db.set_config("hotel_name", self.e_name.get().strip())
        db.set_config("hotel_address", self.e_address.get().strip())
        db.set_config("hotel_phone", self.e_phone.get().strip())
        db.set_config("hotel_email", self.e_email.get().strip())
        db.set_config("hotel_logo", self.e_logo.get().strip())
        db.set_config("currency", self.e_currency.get().strip())
        db.set_config("currency_symbol", self.e_currency_symbol.get().strip())
        db.set_config("tax_rate", self.e_tax.get().strip())
        db.set_config("theme", self.theme_var.get())

        messagebox.showinfo("Guardado", "✔ Configuración guardada con éxito.")
        # Actualizar encabezado del app
        if self.app:
            self.app.reload_header()

    def _browse_logo(self):
        filetypes = [
            ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp *.ico"),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("Todos los archivos", "*.*"),
        ]
        path = filedialog.askopenfilename(
            title="Seleccionar logo del hotel",
            filetypes=filetypes,
        )
        if path:
            self.e_logo.set(path)
            self._preview_logo(path)

    def _clear_logo(self):
        self.e_logo.set("")
        self.logo_preview.config(image="", text="Sin logo\n(haz clic en Seleccionar)")
        self._logo_img = None

    def _preview_logo(self, path: str):
        if not path or not os.path.isfile(path):
            self.logo_preview.config(image="", text="Sin logo\n(haz clic en Seleccionar)")
            return
        if not PIL_AVAILABLE:
            self.logo_preview.config(text=f"Logo: {os.path.basename(path)}\n(Pillow no instalado)")
            return
        try:
            img = Image.open(path)
            img.thumbnail((120, 80), _LANCZOS)
            self._logo_img = ImageTk.PhotoImage(img)
            self.logo_preview.config(image=self._logo_img, text="")
        except Exception as e:
            self.logo_preview.config(image="", text=f"Error: {e}")

    def _add_menu_item(self):
        name = self.me_name.get().strip()
        cat = self.me_cat.get().strip()
        if not name or not cat:
            messagebox.showwarning("Faltan datos", "Nombre y categoría son requeridos.")
            return
        try:
            price = float(self.me_price.get())
        except ValueError:
            messagebox.showerror("Error", "Precio inválido.")
            return
        desc = self.me_desc.get().strip()
        db.add_menu_item(name, cat, price, desc)
        self.me_name.clear()
        self.me_price.clear()
        self.me_desc.clear()
        self._refresh_menu()

    def _refresh_menu(self):
        self.menu_tree.clear()
        sym = db.get_all_config().get("currency_symbol", "$")
        for item in db.get_menu_items():
            self.menu_tree.insert_row((
                item["id"], item["name"], item["category"],
                f"{sym}{item['price']:.2f}",
                "Sí" if item["available"] else "No",
            ))

    def _delete_menu_item(self):
        sel = self.menu_tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona un ítem del menú.")
            return
        name = self.menu_tree.item(sel[0], "values")[1]
        if messagebox.askyesno("Eliminar", f"¿Eliminar '{name}' del menú?"):
            item_id = int(self.menu_tree.item(sel[0], "values")[0])
            db.delete_menu_item(item_id)
            self._refresh_menu()
