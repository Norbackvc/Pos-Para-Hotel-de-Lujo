"""
Hotel POS - Panel de Servicios del Hotel
Spa, lavandería, transporte, servicios de habitación, etc.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from . import database as db
from .widgets import StyledButton, LabeledEntry, SectionTitle, StyledTreeview


class ServicesPanel(tk.Frame):
    def __init__(self, parent, theme, app=None):
        super().__init__(parent, bg=theme["bg2"])
        self.theme = theme
        self.app = app
        self._build()

    def _build(self):
        t = self.theme

        # Barra superior
        top_bar = tk.Frame(self, bg=t["bg3"], pady=8)
        top_bar.pack(fill="x", padx=10, pady=(10, 0))
        SectionTitle(top_bar, "✨  Servicios del Hotel", theme=t).pack(side="left", padx=10)

        btn_frame = tk.Frame(top_bar, bg=t["bg3"])
        btn_frame.pack(side="right", padx=10)
        StyledButton(btn_frame, "➕ Nuevo Servicio", self._new_service,
                     theme=t, style="secondary").pack(side="left", padx=4)
        StyledButton(btn_frame, "🔄 Actualizar", self._refresh,
                     theme=t, style="secondary").pack(side="left", padx=4)

        # Layout
        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=t["bg2"], sashwidth=4)
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Catálogo de servicios ──
        left = tk.Frame(paned, bg=t["bg2"])
        paned.add(left, minsize=350)

        tk.Label(left, text="Catálogo de Servicios",
                 bg=t["bg2"], fg=t["gold"],
                 font=(t["font"], 11, "bold")).pack(pady=(0, 6))

        # Filtro categoría
        cat_row = tk.Frame(left, bg=t["bg2"])
        cat_row.pack(fill="x", pady=(0, 6))
        tk.Label(cat_row, text="Categoría:", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(side="left")
        self.cat_var = tk.StringVar(value="Todas")
        cats = ["Todas"] + db.get_service_categories()
        self.cat_cb = ttk.Combobox(cat_row, textvariable=self.cat_var,
                                   values=cats, width=16, state="readonly")
        self.cat_cb.pack(side="left", padx=6)
        self.cat_cb.bind("<<ComboboxSelected>>", lambda e: self._load_services())

        cols = ("ID", "Servicio", "Categoría", "Precio", "Descripción")
        self.svc_tree = StyledTreeview(left, columns=cols, headings=cols, theme=t)
        self.svc_tree.column("ID", width=40)
        self.svc_tree.column("Servicio", width=180)
        self.svc_tree.column("Categoría", width=100)
        self.svc_tree.column("Precio", width=80)
        self.svc_tree.column("Descripción", width=200)
        self.svc_tree.pack(fill="both", expand=True)

        btn_row = tk.Frame(left, bg=t["bg2"])
        btn_row.pack(fill="x", pady=6)
        StyledButton(btn_row, "✏ Editar", self._edit_service,
                     theme=t, style="secondary").pack(side="left", padx=4)
        StyledButton(btn_row, "🗑 Eliminar", self._delete_service,
                     theme=t, style="danger").pack(side="left", padx=4)

        self._load_services()

        # ── Registrar servicio a huésped ──
        right = tk.Frame(paned, bg=t["card"])
        paned.add(right, minsize=260)

        tk.Label(right, text="Registrar Servicio",
                 bg=t["card"], fg=t["gold"],
                 font=(t["font"], 11, "bold")).pack(pady=(12, 4))

        tk.Label(right, text="Reserva activa:",
                 bg=t["card"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(padx=12, anchor="w")
        self.res_var = tk.StringVar()
        self.res_cb = ttk.Combobox(right, textvariable=self.res_var, width=32)
        self.res_cb.pack(padx=12, pady=(2, 8), fill="x")
        self._load_reservations()

        tk.Label(right, text="Cantidad:", bg=t["card"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(padx=12, anchor="w")
        self.qty_var = tk.IntVar(value=1)
        tk.Spinbox(right, from_=1, to=99, textvariable=self.qty_var, width=6,
                   bg=t["entry_bg"], fg=t["fg"],
                   buttonbackground=t["bg3"]).pack(padx=12, pady=(2, 8), anchor="w")

        self.e_notes = LabeledEntry(right, "Notas del servicio", theme=t, width=28)
        self.e_notes.pack(padx=12, pady=4, fill="x")

        StyledButton(right, "➕ Registrar Servicio al Huésped",
                     self._register_service_to_guest,
                     theme=t, style="gold").pack(padx=12, pady=8, fill="x")

        # Historial de servicios registrados
        tk.Label(right, text="Servicios Registrados Hoy",
                 bg=t["card"], fg=t["gold"],
                 font=(t["font"], 10, "bold")).pack(pady=(6, 2))

        hist_cols = ("Hab.", "Servicio", "Cant.", "Total")
        self.hist_tree = StyledTreeview(right, columns=hist_cols,
                                        headings=hist_cols, theme=t)
        self.hist_tree.column("Hab.", width=50)
        self.hist_tree.column("Servicio", width=130)
        self.hist_tree.column("Cant.", width=40)
        self.hist_tree.column("Total", width=70)
        self.hist_tree.pack(fill="both", expand=True, padx=8, pady=4)

    def _load_services(self):
        self.svc_tree.clear()
        cat = self.cat_var.get() if hasattr(self, "cat_var") else "Todas"
        sym = db.get_all_config().get("currency_symbol", "$")
        items = db.get_services(None if cat == "Todas" else cat)
        for item in items:
            self.svc_tree.insert_row((
                item["id"], item["name"], item["category"],
                f"{sym}{item['price']:.2f}", item["description"],
            ))

    def _load_reservations(self):
        reservations = db.get_active_reservations()
        self._reservations = reservations
        vals = [f"Hab. {r['room_number']} — {r['guest_name']}" for r in reservations]
        self.res_cb["values"] = vals if vals else ["(Sin reservas activas)"]
        if vals:
            self.res_var.set(vals[0])

    def _refresh(self):
        cats = ["Todas"] + db.get_service_categories()
        self.cat_cb["values"] = cats
        self._load_services()
        self._load_reservations()

    def _new_service(self):
        ServiceFormDialog(self, self.theme, on_save=self._refresh)

    def _edit_service(self):
        sel = self.svc_tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona un servicio.")
            return
        svc_id = int(self.svc_tree.item(sel[0], "values")[0])
        services = db.get_services()
        svc = next((s for s in services if s["id"] == svc_id), None)
        if svc:
            ServiceFormDialog(self, self.theme, service=svc, on_save=self._refresh)

    def _delete_service(self):
        sel = self.svc_tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona un servicio.")
            return
        name = self.svc_tree.item(sel[0], "values")[1]
        if messagebox.askyesno("Eliminar", f"¿Eliminar el servicio '{name}'?"):
            svc_id = int(self.svc_tree.item(sel[0], "values")[0])
            db.delete_service(svc_id)
            self._refresh()

    def _register_service_to_guest(self):
        sel = self.svc_tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona un servicio del catálogo.")
            return
        if not self._reservations:
            messagebox.showwarning("Sin reservas", "No hay reservas activas.")
            return
        rv = self.res_var.get()
        res_idx = [f"Hab. {r['room_number']} — {r['guest_name']}"
                   for r in self._reservations].index(rv)
        reservation = self._reservations[res_idx]

        values = self.svc_tree.item(sel[0], "values")
        svc_name = values[1]
        svc_cat = values[2]
        svc_price_str = values[3].replace("$", "").replace(",", "")
        svc_price = float(svc_price_str)
        qty = self.qty_var.get()
        notes = self.e_notes.get().strip()

        # Crear orden de servicio ligada a la reserva
        order_id = db.create_order(
            svc_cat, reservation_id=reservation["id"],
            guest_id=reservation["guest_id"],
            notes=notes,
        )
        db.add_order_item(order_id, svc_name, svc_cat, qty, svc_price)
        db.close_order(order_id)

        sym = db.get_all_config().get("currency_symbol", "$")
        total = qty * svc_price
        messagebox.showinfo(
            "Servicio Registrado",
            f"✔ {svc_name} x{qty}\n"
            f"Hab. {reservation['room_number']} — {reservation['guest_name']}\n"
            f"Total: {sym}{total:.2f}",
        )
        # Agregar al historial
        self.hist_tree.insert_row((
            reservation["room_number"],
            svc_name, qty,
            f"{sym}{total:.2f}",
        ))
        self.e_notes.clear()


class ServiceFormDialog(tk.Toplevel):
    def __init__(self, parent, theme, service=None, on_save=None):
        super().__init__(parent)
        self.theme = theme
        self.service = service
        self.on_save = on_save
        t = theme
        self.title("Editar Servicio" if service else "Nuevo Servicio")
        self.configure(bg=t["bg2"])
        self.resizable(False, False)
        self.grab_set()
        self._build()
        self._center()

    def _build(self):
        t = self.theme
        s = self.service

        tk.Label(self, text="Datos del Servicio",
                 bg=t["bg2"], fg=t["gold"],
                 font=(t["font"], 13, "bold")).pack(pady=(12, 6))

        self.e_name = LabeledEntry(self, "Nombre *", theme=t, width=30)
        self.e_name.pack(padx=20, pady=4, fill="x")

        tk.Label(self, text="Categoría *", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(padx=20, anchor="w")
        self.cat_var = tk.StringVar()
        ttk.Combobox(
            self, textvariable=self.cat_var,
            values=["Spa", "Lavandería", "Transporte", "Habitación",
                    "Eventos", "Otro"],
            width=22,
        ).pack(padx=20, pady=(2, 6))

        self.e_price = LabeledEntry(self, "Precio *", theme=t, width=12)
        self.e_price.pack(padx=20, pady=4, fill="x")
        self.e_desc = LabeledEntry(self, "Descripción", theme=t, width=34)
        self.e_desc.pack(padx=20, pady=4, fill="x")

        if s:
            self.e_name.set(s["name"])
            self.cat_var.set(s["category"])
            self.e_price.set(str(s["price"]))
            self.e_desc.set(s["description"] or "")

        self.avail_var = tk.BooleanVar(value=True if not s else bool(s["available"]))
        tk.Checkbutton(self, text="Disponible", variable=self.avail_var,
                       bg=t["bg2"], fg=t["fg"],
                       selectcolor=t["entry_bg"],
                       font=(t["font"], 9)).pack(padx=20, anchor="w")

        btn_row = tk.Frame(self, bg=t["bg2"])
        btn_row.pack(pady=10)
        StyledButton(btn_row, "💾 Guardar", self._save,
                     theme=t, style="success").pack(side="left", padx=6)
        StyledButton(btn_row, "✖ Cancelar", self.destroy,
                     theme=t, style="secondary").pack(side="left", padx=6)

    def _save(self):
        name = self.e_name.get().strip()
        cat = self.cat_var.get().strip()
        if not name or not cat:
            messagebox.showerror("Error", "Nombre y categoría son obligatorios.")
            return
        try:
            price = float(self.e_price.get())
        except ValueError:
            messagebox.showerror("Error", "Precio inválido.")
            return
        desc = self.e_desc.get().strip()
        avail = int(self.avail_var.get())
        if self.service:
            db.update_service(self.service["id"], name, cat, price, desc, avail)
        else:
            db.add_service(name, cat, price, desc)
        self.destroy()
        if self.on_save:
            self.on_save()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
