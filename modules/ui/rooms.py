"""
Rooms management UI panel.
"""
import tkinter as tk
from tkinter import ttk, messagebox

import modules.database as db
from modules.models import Room

ROOM_TYPES = ["SINGLE", "DOUBLE", "SUITE", "PRESIDENTIAL"]
ROOM_STATUSES = ["AVAILABLE", "OCCUPIED", "MAINTENANCE", "RESERVED"]

STATUS_COLORS = {
    "AVAILABLE":   "#27ae60",
    "OCCUPIED":    "#e74c3c",
    "MAINTENANCE": "#f39c12",
    "RESERVED":    "#2980b9",
}

STATUS_LABELS = {
    "AVAILABLE":   "Disponible",
    "OCCUPIED":    "Ocupada",
    "MAINTENANCE": "Mantenimiento",
    "RESERVED":    "Reservada",
}

TYPE_LABELS = {
    "SINGLE":      "Individual",
    "DOUBLE":      "Doble",
    "SUITE":       "Suite",
    "PRESIDENTIAL":"Presidencial",
}


class RoomsPanel(ttk.Frame):
    def __init__(self, parent, settings, **kwargs):
        super().__init__(parent, **kwargs)
        self.settings = settings
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=6)
        ttk.Button(toolbar, text="➕  Nueva Habitación", command=self._new_room).pack(side="left", padx=4)
        ttk.Button(toolbar, text="✏️  Editar",           command=self._edit_room).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🔄  Actualizar",        command=self.refresh).pack(side="left", padx=4)

        # Filter
        filter_frame = ttk.LabelFrame(self, text="Filtrar por estado")
        filter_frame.pack(fill="x", padx=10, pady=4)
        self._status_filter = tk.StringVar(value="ALL")
        ttk.Radiobutton(filter_frame, text="Todos",         variable=self._status_filter, value="ALL",          command=self.refresh).pack(side="left", padx=6)
        ttk.Radiobutton(filter_frame, text="Disponibles",   variable=self._status_filter, value="AVAILABLE",    command=self.refresh).pack(side="left", padx=6)
        ttk.Radiobutton(filter_frame, text="Ocupadas",      variable=self._status_filter, value="OCCUPIED",     command=self.refresh).pack(side="left", padx=6)
        ttk.Radiobutton(filter_frame, text="Reservadas",    variable=self._status_filter, value="RESERVED",     command=self.refresh).pack(side="left", padx=6)
        ttk.Radiobutton(filter_frame, text="Mantenimiento", variable=self._status_filter, value="MAINTENANCE",  command=self.refresh).pack(side="left", padx=6)

        # Table
        cols = ("number", "type", "floor", "price", "status")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        self._tree.heading("number", text="Habitación")
        self._tree.heading("type",   text="Tipo")
        self._tree.heading("floor",  text="Piso")
        self._tree.heading("price",  text="Precio/Noche")
        self._tree.heading("status", text="Estado")
        self._tree.column("number", width=100, anchor="center")
        self._tree.column("type",   width=140)
        self._tree.column("floor",  width=60,  anchor="center")
        self._tree.column("price",  width=120, anchor="e")
        self._tree.column("status", width=140)
        vsb = ttk.Scrollbar(self, orient="vertical",   command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=4)
        vsb.pack(side="left", fill="y", pady=4)
        self._tree.bind("<Double-1>", lambda _: self._edit_room())

        # Status colour tags
        for status, colour in STATUS_COLORS.items():
            self._tree.tag_configure(status, foreground=colour)

    def refresh(self):
        self._tree.delete(*self._tree.get_children())
        rooms = db.get_all_rooms()
        sf = self._status_filter.get()
        sym = self.settings.currency_symbol
        for room in rooms:
            if sf != "ALL" and room.status != sf:
                continue
            self._tree.insert("", "end", iid=str(room.id), tags=(room.status,), values=(
                room.number,
                TYPE_LABELS.get(room.room_type, room.room_type),
                room.floor,
                f"{sym}{room.price_per_night:,.2f}",
                STATUS_LABELS.get(room.status, room.status),
            ))

    def _new_room(self):
        RoomDialog(self, Room(0, "", "SINGLE", 0.0, "AVAILABLE", 1), self.settings, on_save=self.refresh)

    def _edit_room(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selección", "Seleccione una habitación primero.", parent=self)
            return
        room = db.get_room(int(sel[0]))
        if room:
            RoomDialog(self, room, self.settings, on_save=self.refresh)


class RoomDialog(tk.Toplevel):
    def __init__(self, parent, room: Room, settings, on_save):
        super().__init__(parent)
        self.room = room
        self.settings = settings
        self.on_save = on_save
        self.title("Nueva Habitación" if room.id == 0 else f"Habitación {room.number}")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        pad = {"padx": 8, "pady": 4}
        f = ttk.Frame(self, padding=10)
        f.pack(fill="both", expand=True)

        fields = [
            ("Número:", "number"),
            ("Piso:", "floor"),
            ("Precio/Noche:", "price"),
            ("Descripción:", "description"),
            ("Amenidades:", "amenities"),
        ]
        self._vars = {}
        for row_idx, (label, key) in enumerate(fields):
            ttk.Label(f, text=label).grid(row=row_idx, column=0, sticky="e", **pad)
            var = tk.StringVar(value=str(getattr(self.room, key if key != "price" else "price_per_night", "")))
            self._vars[key] = var
            ttk.Entry(f, textvariable=var, width=28).grid(row=row_idx, column=1, sticky="ew", **pad)

        row_idx += 1
        ttk.Label(f, text="Tipo:").grid(row=row_idx, column=0, sticky="e", **pad)
        self._type_var = tk.StringVar(value=self.room.room_type)
        ttk.Combobox(f, textvariable=self._type_var, values=ROOM_TYPES, state="readonly", width=26).grid(row=row_idx, column=1, sticky="ew", **pad)

        row_idx += 1
        ttk.Label(f, text="Estado:").grid(row=row_idx, column=0, sticky="e", **pad)
        self._status_var = tk.StringVar(value=self.room.status)
        ttk.Combobox(f, textvariable=self._status_var, values=ROOM_STATUSES, state="readonly", width=26).grid(row=row_idx, column=1, sticky="ew", **pad)

        row_idx += 1
        btn_frame = ttk.Frame(f)
        btn_frame.grid(row=row_idx, columnspan=2, pady=8)
        ttk.Button(btn_frame, text="Guardar", command=self._save).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=6)

    def _save(self):
        try:
            self.room.number = self._vars["number"].get().strip()
            self.room.floor = int(self._vars["floor"].get())
            self.room.price_per_night = float(self._vars["price"].get())
            self.room.description = self._vars["description"].get().strip()
            self.room.amenities = self._vars["amenities"].get().strip()
            self.room.room_type = self._type_var.get()
            self.room.status = self._status_var.get()
            if not self.room.number:
                raise ValueError("El número de habitación es obligatorio.")
            db.save_room(self.room)
            self.on_save()
            self.destroy()
        except ValueError as exc:
            messagebox.showerror("Error", str(exc), parent=self)
