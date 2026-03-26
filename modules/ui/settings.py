"""
Settings UI panel – hotel configuration and logo upload.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import modules.database as db
from modules.models import HotelSettings

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class SettingsPanel(ttk.Frame):
    def __init__(self, parent, settings: HotelSettings, on_settings_changed=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.settings = settings
        self.on_settings_changed = on_settings_changed
        self._logo_image = None
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        canvas = tk.Canvas(self, borderwidth=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = ttk.Frame(canvas, padding=16)
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        pad = {"padx": 8, "pady": 4}

        # ── Hotel Info ──────────────────────────────────────────────
        info_frame = ttk.LabelFrame(inner, text="Información del Hotel", padding=8)
        info_frame.pack(fill="x", pady=6)

        info_fields = [
            ("Nombre del Hotel:",  "hotel_name"),
            ("Dirección:",         "address"),
            ("Teléfono:",          "phone"),
            ("Email:",             "email"),
            ("Sitio Web:",         "website"),
            ("Hora Check-In:",     "check_in_time"),
            ("Hora Check-Out:",    "check_out_time"),
            ("Pie de Factura:",    "invoice_footer"),
        ]
        self._vars: dict = {}
        for row_idx, (label, key) in enumerate(info_fields):
            ttk.Label(info_frame, text=label).grid(row=row_idx, column=0, sticky="e", **pad)
            var = tk.StringVar()
            self._vars[key] = var
            ttk.Entry(info_frame, textvariable=var, width=40).grid(row=row_idx, column=1, sticky="ew", **pad)

        # ── Financial ───────────────────────────────────────────────
        fin_frame = ttk.LabelFrame(inner, text="Configuración Financiera", padding=8)
        fin_frame.pack(fill="x", pady=6)

        ttk.Label(fin_frame, text="Moneda:").grid(row=0, column=0, sticky="e", **pad)
        self._vars["currency"] = tk.StringVar()
        ttk.Entry(fin_frame, textvariable=self._vars["currency"], width=10).grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(fin_frame, text="Símbolo:").grid(row=0, column=2, sticky="e", **pad)
        self._vars["currency_symbol"] = tk.StringVar()
        ttk.Entry(fin_frame, textvariable=self._vars["currency_symbol"], width=6).grid(row=0, column=3, sticky="w", **pad)

        ttk.Label(fin_frame, text="IVA (%):").grid(row=1, column=0, sticky="e", **pad)
        self._vars["tax_rate"] = tk.StringVar()
        ttk.Entry(fin_frame, textvariable=self._vars["tax_rate"], width=10).grid(row=1, column=1, sticky="w", **pad)

        # ── Logo ────────────────────────────────────────────────────
        logo_frame = ttk.LabelFrame(inner, text="Logo del Hotel", padding=8)
        logo_frame.pack(fill="x", pady=6)

        self._logo_path_var = tk.StringVar()
        ttk.Entry(logo_frame, textvariable=self._logo_path_var, width=50, state="readonly").pack(side="left", padx=(0, 6))
        ttk.Button(logo_frame, text="📂 Seleccionar Logo", command=self._choose_logo).pack(side="left", padx=4)
        ttk.Button(logo_frame, text="🗑️ Quitar Logo",      command=self._remove_logo).pack(side="left", padx=4)

        self._logo_preview = ttk.Label(inner)
        self._logo_preview.pack(pady=6)

        # ── Save ────────────────────────────────────────────────────
        ttk.Button(inner, text="💾  Guardar Configuración", command=self._save).pack(pady=10)

    def _load_values(self):
        s = self.settings
        mapping = {
            "hotel_name":    s.hotel_name,
            "address":       s.address,
            "phone":         s.phone,
            "email":         s.email,
            "website":       s.website,
            "check_in_time": s.check_in_time,
            "check_out_time":s.check_out_time,
            "invoice_footer":s.invoice_footer,
            "currency":      s.currency,
            "currency_symbol":s.currency_symbol,
            "tax_rate":      str(s.tax_rate),
        }
        for key, value in mapping.items():
            self._vars[key].set(value)
        self._logo_path_var.set(s.logo_path or "")
        self._update_logo_preview(s.logo_path)

    def _choose_logo(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Seleccionar Logo",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Todos", "*.*")],
        )
        if path:
            self._logo_path_var.set(path)
            self._update_logo_preview(path)

    def _remove_logo(self):
        self._logo_path_var.set("")
        self._update_logo_preview("")

    def _update_logo_preview(self, path: str):
        if not path or not os.path.isfile(path):
            self._logo_preview.config(image="", text="Sin logo")
            self._logo_image = None
            return
        if PIL_AVAILABLE:
            try:
                img = Image.open(path)
                img.thumbnail((200, 100))
                self._logo_image = ImageTk.PhotoImage(img)
                self._logo_preview.config(image=self._logo_image, text="")
                return
            except Exception:
                pass
        # Fallback: show file path only
        self._logo_preview.config(image="", text=os.path.basename(path))
        self._logo_image = None

    def _save(self):
        try:
            self.settings.hotel_name     = self._vars["hotel_name"].get().strip()
            self.settings.address        = self._vars["address"].get().strip()
            self.settings.phone          = self._vars["phone"].get().strip()
            self.settings.email          = self._vars["email"].get().strip()
            self.settings.website        = self._vars["website"].get().strip()
            self.settings.check_in_time  = self._vars["check_in_time"].get().strip()
            self.settings.check_out_time = self._vars["check_out_time"].get().strip()
            self.settings.invoice_footer = self._vars["invoice_footer"].get().strip()
            self.settings.currency       = self._vars["currency"].get().strip()
            self.settings.currency_symbol= self._vars["currency_symbol"].get().strip()
            self.settings.tax_rate       = float(self._vars["tax_rate"].get())
            self.settings.logo_path      = self._logo_path_var.get().strip()
            db.save_settings(self.settings)
            if self.on_settings_changed:
                self.on_settings_changed(self.settings)
            messagebox.showinfo("Guardado", "Configuración guardada correctamente.", parent=self)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc), parent=self)
