"""
Guest management UI panel.
"""
import tkinter as tk
from tkinter import ttk, messagebox

import modules.database as db
from modules.models import Guest

DOCUMENT_TYPES = ["PASSPORT", "DNI", "LICENSE", "ID_CARD", "OTHER"]


class GuestsPanel(ttk.Frame):
    def __init__(self, parent, settings, **kwargs):
        super().__init__(parent, **kwargs)
        self.settings = settings
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=6)
        ttk.Button(toolbar, text="➕  Nuevo Huésped", command=self._new_guest).pack(side="left", padx=4)
        ttk.Button(toolbar, text="✏️  Editar",         command=self._edit_guest).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🔄  Actualizar",     command=self.refresh).pack(side="left", padx=4)

        # Search bar
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=4)
        ttk.Label(search_frame, text="Buscar:").pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._do_search())
        ttk.Entry(search_frame, textvariable=self._search_var, width=30).pack(side="left", padx=6)

        cols = ("id", "name", "doc_type", "document", "email", "phone", "nationality")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        headings = [
            ("id",          "#",           50),
            ("name",        "Nombre",      200),
            ("doc_type",    "Tipo Doc.",   100),
            ("document",    "Documento",   120),
            ("email",       "Email",       180),
            ("phone",       "Teléfono",    120),
            ("nationality", "Nacionalidad",110),
        ]
        for col, text, width in headings:
            self._tree.heading(col, text=text)
            self._tree.column(col, width=width)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=4)
        vsb.pack(side="left", fill="y", pady=4)
        self._tree.bind("<Double-1>", lambda _: self._edit_guest())

    def refresh(self, guests=None):
        self._tree.delete(*self._tree.get_children())
        guests = guests or db.get_all_guests()
        for g in guests:
            self._tree.insert("", "end", iid=str(g.id), values=(
                g.id, g.full_name, g.document_type, g.id_document,
                g.email, g.phone, g.nationality,
            ))

    def _do_search(self):
        q = self._search_var.get().strip()
        if q:
            self.refresh(db.search_guests(q))
        else:
            self.refresh()

    def _new_guest(self):
        GuestDialog(self, Guest(0, "", "", "", "PASSPORT"), on_save=lambda _: self.refresh())

    def _edit_guest(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selección", "Seleccione un huésped.", parent=self)
            return
        guests = db.get_all_guests()
        guest = next((g for g in guests if str(g.id) == sel[0]), None)
        if guest:
            GuestDialog(self, guest, on_save=lambda _: self.refresh())


class GuestDialog(tk.Toplevel):
    def __init__(self, parent, guest: Guest, on_save=None):
        super().__init__(parent)
        self.guest = guest
        self.on_save = on_save
        self.title("Nuevo Huésped" if guest.id == 0 else f"Huésped: {guest.full_name}")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        pad = {"padx": 8, "pady": 4}
        f = ttk.Frame(self, padding=10)
        f.pack(fill="both", expand=True)

        fields = [
            ("Nombre:", "first_name"),
            ("Apellido:", "last_name"),
            ("Documento:", "id_document"),
            ("Email:", "email"),
            ("Teléfono:", "phone"),
            ("Nacionalidad:", "nationality"),
            ("Dirección:", "address"),
        ]
        self._vars = {}
        for row_idx, (label, key) in enumerate(fields):
            ttk.Label(f, text=label).grid(row=row_idx, column=0, sticky="e", **pad)
            var = tk.StringVar(value=str(getattr(self.guest, key, "")))
            self._vars[key] = var
            ttk.Entry(f, textvariable=var, width=30).grid(row=row_idx, column=1, sticky="ew", **pad)

        row_idx += 1
        ttk.Label(f, text="Tipo Doc.:").grid(row=row_idx, column=0, sticky="e", **pad)
        self._doc_type_var = tk.StringVar(value=self.guest.document_type)
        ttk.Combobox(f, textvariable=self._doc_type_var, values=DOCUMENT_TYPES, state="readonly", width=28).grid(row=row_idx, column=1, sticky="ew", **pad)

        row_idx += 1
        btn_frame = ttk.Frame(f)
        btn_frame.grid(row=row_idx, columnspan=2, pady=8)
        ttk.Button(btn_frame, text="Guardar",  command=self._save).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=6)

    def _save(self):
        try:
            for key, var in self._vars.items():
                setattr(self.guest, key, var.get().strip())
            self.guest.document_type = self._doc_type_var.get()
            if not self.guest.first_name or not self.guest.last_name:
                raise ValueError("Nombre y apellido son obligatorios.")
            if not self.guest.id_document:
                raise ValueError("El número de documento es obligatorio.")
            db.save_guest(self.guest)
            if self.on_save:
                self.on_save(self.guest)
            self.destroy()
        except ValueError as exc:
            messagebox.showerror("Error", str(exc), parent=self)
