"""
Reservations management UI panel.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

import modules.database as db
from modules.models import Reservation, Guest

STATUSES = ["CONFIRMED", "CHECKED_IN", "CHECKED_OUT", "CANCELLED"]
STATUS_LABELS = {
    "CONFIRMED":   "Confirmada",
    "CHECKED_IN":  "Check-In",
    "CHECKED_OUT": "Check-Out",
    "CANCELLED":   "Cancelada",
}
STATUS_COLORS = {
    "CONFIRMED":   "#2980b9",
    "CHECKED_IN":  "#27ae60",
    "CHECKED_OUT": "#7f8c8d",
    "CANCELLED":   "#e74c3c",
}


class ReservationsPanel(ttk.Frame):
    def __init__(self, parent, settings, **kwargs):
        super().__init__(parent, **kwargs)
        self.settings = settings
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=6)
        ttk.Button(toolbar, text="➕  Nueva Reserva",  command=self._new_reservation).pack(side="left", padx=4)
        ttk.Button(toolbar, text="✏️  Editar",          command=self._edit_reservation).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🏨  Check-In",        command=lambda: self._change_status("CHECKED_IN")).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🚪  Check-Out",       command=lambda: self._change_status("CHECKED_OUT")).pack(side="left", padx=4)
        ttk.Button(toolbar, text="❌  Cancelar",        command=lambda: self._change_status("CANCELLED")).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🔄  Actualizar",      command=self.refresh).pack(side="left", padx=4)

        # Filter
        filter_frame = ttk.LabelFrame(self, text="Filtrar")
        filter_frame.pack(fill="x", padx=10, pady=4)
        self._status_filter = tk.StringVar(value="ALL")
        ttk.Radiobutton(filter_frame, text="Todas",      variable=self._status_filter, value="ALL",         command=self.refresh).pack(side="left", padx=6)
        ttk.Radiobutton(filter_frame, text="Confirmadas",variable=self._status_filter, value="CONFIRMED",   command=self.refresh).pack(side="left", padx=6)
        ttk.Radiobutton(filter_frame, text="Check-In",   variable=self._status_filter, value="CHECKED_IN",  command=self.refresh).pack(side="left", padx=6)
        ttk.Radiobutton(filter_frame, text="Check-Out",  variable=self._status_filter, value="CHECKED_OUT", command=self.refresh).pack(side="left", padx=6)
        ttk.Radiobutton(filter_frame, text="Canceladas", variable=self._status_filter, value="CANCELLED",   command=self.refresh).pack(side="left", padx=6)

        cols = ("id", "room", "guest", "check_in", "check_out", "adults", "status")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        headings = [("id","#", 50), ("room","Habitación", 100), ("guest","Huésped", 200),
                    ("check_in","Check-In", 110), ("check_out","Check-Out", 110),
                    ("adults","Adultos", 70), ("status","Estado", 130)]
        for col, text, width in headings:
            self._tree.heading(col, text=text)
            anchor = "center" if col in ("id", "adults") else "w"
            self._tree.column(col, width=width, anchor=anchor)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=4)
        vsb.pack(side="left", fill="y", pady=4)
        self._tree.bind("<Double-1>", lambda _: self._edit_reservation())

        for status, colour in STATUS_COLORS.items():
            self._tree.tag_configure(status, foreground=colour)

    def refresh(self):
        self._tree.delete(*self._tree.get_children())
        sf = self._status_filter.get()
        reservations = db.get_all_reservations(None if sf == "ALL" else sf)
        for res in reservations:
            self._tree.insert("", "end", iid=str(res.id), tags=(res.status,), values=(
                res.id, res.room_number, res.guest_name,
                res.check_in, res.check_out, res.adults,
                STATUS_LABELS.get(res.status, res.status),
            ))

    def _change_status(self, new_status: str):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selección", "Seleccione una reserva.", parent=self)
            return
        res = db.get_reservation(int(sel[0]))
        if not res:
            return
        res.status = new_status
        db.save_reservation(res)
        if new_status == "CHECKED_IN":
            db.update_room_status(res.room_id, "OCCUPIED")
        elif new_status in ("CHECKED_OUT", "CANCELLED"):
            db.update_room_status(res.room_id, "AVAILABLE")
        self.refresh()

    def _new_reservation(self):
        ReservationDialog(self, None, self.settings, on_save=self.refresh)

    def _edit_reservation(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selección", "Seleccione una reserva.", parent=self)
            return
        res = db.get_reservation(int(sel[0]))
        ReservationDialog(self, res, self.settings, on_save=self.refresh)


class ReservationDialog(tk.Toplevel):
    def __init__(self, parent, reservation, settings, on_save):
        super().__init__(parent)
        self.reservation = reservation
        self.settings = settings
        self.on_save = on_save
        self.title("Nueva Reserva" if reservation is None else f"Reserva #{reservation.id}")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        pad = {"padx": 8, "pady": 4}
        f = ttk.Frame(self, padding=10)
        f.pack(fill="both", expand=True)

        # Guest search
        ttk.Label(f, text="Buscar Huésped:").grid(row=0, column=0, sticky="e", **pad)
        self._guest_search = tk.StringVar()
        search_frame = ttk.Frame(f)
        search_frame.grid(row=0, column=1, sticky="ew", **pad)
        ttk.Entry(search_frame, textvariable=self._guest_search, width=22).pack(side="left")
        ttk.Button(search_frame, text="🔍", command=self._search_guest).pack(side="left", padx=4)
        ttk.Button(search_frame, text="➕ Nuevo", command=self._new_guest).pack(side="left")

        ttk.Label(f, text="Huésped:").grid(row=1, column=0, sticky="e", **pad)
        self._guest_var = tk.StringVar()
        self._guest_id = None
        self._guest_label = ttk.Label(f, textvariable=self._guest_var, foreground="#2980b9")
        self._guest_label.grid(row=1, column=1, sticky="w", **pad)

        # Room
        ttk.Label(f, text="Habitación:").grid(row=2, column=0, sticky="e", **pad)
        rooms = db.get_all_rooms()
        available_rooms = [r for r in rooms if r.status in ("AVAILABLE", "RESERVED")]
        self._room_options = {f"{r.number} – {r.room_type} ({self.settings.currency_symbol}{r.price_per_night:,.0f}/noche)": r.id for r in available_rooms}
        self._room_var = tk.StringVar()
        ttk.Combobox(f, textvariable=self._room_var, values=list(self._room_options.keys()), state="readonly", width=36).grid(row=2, column=1, sticky="ew", **pad)

        # Dates
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        checkout_default = (date.today() + timedelta(days=2)).isoformat()
        ttk.Label(f, text="Check-In:").grid(row=3, column=0, sticky="e", **pad)
        self._checkin = tk.StringVar(value=self.reservation.check_in if self.reservation else date.today().isoformat())
        ttk.Entry(f, textvariable=self._checkin, width=14).grid(row=3, column=1, sticky="w", **pad)

        ttk.Label(f, text="Check-Out:").grid(row=4, column=0, sticky="e", **pad)
        self._checkout = tk.StringVar(value=self.reservation.check_out if self.reservation else checkout_default)
        ttk.Entry(f, textvariable=self._checkout, width=14).grid(row=4, column=1, sticky="w", **pad)

        ttk.Label(f, text="Adultos:").grid(row=5, column=0, sticky="e", **pad)
        self._adults = tk.StringVar(value=str(self.reservation.adults) if self.reservation else "1")
        ttk.Spinbox(f, from_=1, to=10, textvariable=self._adults, width=5).grid(row=5, column=1, sticky="w", **pad)

        ttk.Label(f, text="Niños:").grid(row=6, column=0, sticky="e", **pad)
        self._children = tk.StringVar(value=str(self.reservation.children) if self.reservation else "0")
        ttk.Spinbox(f, from_=0, to=10, textvariable=self._children, width=5).grid(row=6, column=1, sticky="w", **pad)

        ttk.Label(f, text="Estado:").grid(row=7, column=0, sticky="e", **pad)
        self._status_var = tk.StringVar(value=self.reservation.status if self.reservation else "CONFIRMED")
        ttk.Combobox(f, textvariable=self._status_var, values=STATUSES, state="readonly", width=26).grid(row=7, column=1, sticky="ew", **pad)

        ttk.Label(f, text="Notas:").grid(row=8, column=0, sticky="ne", **pad)
        self._notes_text = tk.Text(f, width=30, height=3)
        self._notes_text.grid(row=8, column=1, sticky="ew", **pad)
        if self.reservation and self.reservation.notes:
            self._notes_text.insert("1.0", self.reservation.notes)

        # Pre-fill if editing
        if self.reservation:
            self._guest_id = self.reservation.guest_id
            self._guest_var.set(self.reservation.guest_name)
            # select matching room
            for label, rid in self._room_options.items():
                if rid == self.reservation.room_id:
                    self._room_var.set(label)
                    break

        btn_frame = ttk.Frame(f)
        btn_frame.grid(row=9, columnspan=2, pady=8)
        ttk.Button(btn_frame, text="Guardar", command=self._save).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=6)

    def _search_guest(self):
        query = self._guest_search.get().strip()
        if not query:
            return
        guests = db.search_guests(query)
        if not guests:
            messagebox.showinfo("Sin resultados", "No se encontraron huéspedes.", parent=self)
            return
        if len(guests) == 1:
            self._select_guest(guests[0])
            return
        GuestPickerDialog(self, guests, on_select=self._select_guest)

    def _select_guest(self, guest: Guest):
        self._guest_id = guest.id
        self._guest_var.set(guest.full_name)

    def _new_guest(self):
        from modules.ui.guests import GuestDialog
        GuestDialog(self, Guest(0, "", "", "", "PASSPORT"), on_save=self._on_guest_created)

    def _on_guest_created(self, guest: Guest):
        self._select_guest(guest)

    def _save(self):
        try:
            if not self._guest_id:
                raise ValueError("Seleccione un huésped.")
            if not self._room_var.get():
                raise ValueError("Seleccione una habitación.")
            room_id = self._room_options[self._room_var.get()]
            notes = self._notes_text.get("1.0", "end-1c")
            if self.reservation is None:
                from modules.models import Reservation
                res = Reservation(
                    id=0, room_id=room_id, guest_id=self._guest_id,
                    check_in=self._checkin.get(), check_out=self._checkout.get(),
                    status=self._status_var.get(),
                    adults=int(self._adults.get()), children=int(self._children.get()),
                    notes=notes,
                )
            else:
                res = self.reservation
                res.room_id = room_id
                res.guest_id = self._guest_id
                res.check_in = self._checkin.get()
                res.check_out = self._checkout.get()
                res.status = self._status_var.get()
                res.adults = int(self._adults.get())
                res.children = int(self._children.get())
                res.notes = notes
            db.save_reservation(res)
            self.on_save()
            self.destroy()
        except ValueError as exc:
            messagebox.showerror("Error", str(exc), parent=self)


class GuestPickerDialog(tk.Toplevel):
    def __init__(self, parent, guests, on_select):
        super().__init__(parent)
        self.title("Seleccionar Huésped")
        self.grab_set()
        self.resizable(False, False)
        self.on_select = on_select

        cols = ("id", "name", "doc")
        tree = ttk.Treeview(self, columns=cols, show="headings", height=8)
        tree.heading("id",   text="#")
        tree.heading("name", text="Nombre")
        tree.heading("doc",  text="Documento")
        tree.column("id",   width=50,  anchor="center")
        tree.column("name", width=200)
        tree.column("doc",  width=140)
        for g in guests:
            tree.insert("", "end", iid=str(g.id), values=(g.id, g.full_name, g.id_document))
        tree.pack(padx=10, pady=8)

        def select():
            sel = tree.selection()
            if sel:
                gid = int(sel[0])
                guest = next(g for g in guests if g.id == gid)
                self.on_select(guest)
                self.destroy()

        ttk.Button(self, text="Seleccionar", command=select).pack(pady=(0, 8))
