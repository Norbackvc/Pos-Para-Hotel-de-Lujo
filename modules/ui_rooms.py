"""
Hotel POS - Panel de Habitaciones
Gestión de habitaciones, check-in y check-out.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date

from . import database as db
from .widgets import StyledButton, LabeledEntry, SectionTitle, StyledTreeview


class RoomsPanel(tk.Frame):
    def __init__(self, parent, theme, app=None):
        super().__init__(parent, bg=theme["bg2"])
        self.theme = theme
        self.app = app
        self._build()
        self.refresh()

    # ── Construcción de la UI ─────────────────────────────────────────────────

    def _build(self):
        t = self.theme

        # Barra superior
        top_bar = tk.Frame(self, bg=t["bg3"], pady=8)
        top_bar.pack(fill="x", padx=10, pady=(10, 0))

        SectionTitle(top_bar, "🛏  Gestión de Habitaciones", theme=t).pack(side="left", padx=10)

        btn_frame = tk.Frame(top_bar, bg=t["bg3"])
        btn_frame.pack(side="right", padx=10)

        StyledButton(btn_frame, "➕ Nueva Habitación", self._new_room,
                     theme=t, style="secondary").pack(side="left", padx=4)
        StyledButton(btn_frame, "🔄 Actualizar", self.refresh,
                     theme=t, style="secondary").pack(side="left", padx=4)

        # Panel principal dividido: mapa de habitaciones + detalle
        content = tk.Frame(self, bg=t["bg2"])
        content.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(content, bg=t["bg2"])
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(content, bg=t["card"], width=280)
        right.pack(side="right", fill="y", padx=(10, 0))
        right.pack_propagate(False)

        self._build_room_grid(left)
        self._build_detail(right)

    def _build_room_grid(self, parent):
        t = self.theme

        # Filtros
        filter_row = tk.Frame(parent, bg=t["bg2"])
        filter_row.pack(fill="x", pady=(0, 8))

        tk.Label(filter_row, text="Estado:", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(side="left")

        self.filter_var = tk.StringVar(value="Todos")
        statuses = ["Todos", "disponible", "ocupada", "mantenimiento"]
        cb = ttk.Combobox(filter_row, textvariable=self.filter_var,
                          values=statuses, width=14, state="readonly")
        cb.pack(side="left", padx=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # Leyenda
        legend = tk.Frame(filter_row, bg=t["bg2"])
        legend.pack(side="right")
        for label, color in [("Disponible", t["success"]),
                              ("Ocupada", t["error"]),
                              ("Mant.", t["warning"])]:
            f = tk.Frame(legend, bg=t["bg2"])
            f.pack(side="left", padx=4)
            tk.Label(f, text="●", bg=t["bg2"], fg=color, font=(t["font"], 12)).pack(side="left")
            tk.Label(f, text=label, bg=t["bg2"], fg=t["fg2"], font=(t["font"], 8)).pack(side="left")

        # Canvas con scroll para el grid
        canvas_frame = tk.Frame(parent, bg=t["bg2"])
        canvas_frame.pack(fill="both", expand=True)

        self.grid_canvas = tk.Canvas(canvas_frame, bg=t["bg2"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.grid_canvas.yview)
        self.grid_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.grid_canvas.pack(side="left", fill="both", expand=True)

        self.grid_inner = tk.Frame(self.grid_canvas, bg=t["bg2"])
        self.grid_canvas_id = self.grid_canvas.create_window(
            (0, 0), window=self.grid_inner, anchor="nw"
        )
        self.grid_inner.bind(
            "<Configure>",
            lambda e: self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all")),
        )
        self.grid_canvas.bind("<Configure>", self._on_canvas_resize)

    def _on_canvas_resize(self, event):
        self.grid_canvas.itemconfig(self.grid_canvas_id, width=event.width)

    def _build_detail(self, parent):
        t = self.theme
        tk.Label(parent, text="Detalle de Habitación",
                 bg=t["card"], fg=t["gold"],
                 font=(t["font"], 11, "bold")).pack(pady=(12, 6))

        self.detail_text = tk.Text(
            parent, bg=t["entry_bg"], fg=t["fg"],
            font=(t["font"], 10), width=28, height=18,
            relief="flat", bd=4, wrap="word", state="disabled",
        )
        self.detail_text.pack(padx=10, pady=4, fill="both")

        btn_frame = tk.Frame(parent, bg=t["card"])
        btn_frame.pack(pady=6)
        self.btn_checkin = StyledButton(btn_frame, "✔ Check-In",
                                        self._do_checkin, theme=t, style="success")
        self.btn_checkin.pack(fill="x", padx=10, pady=2)

        self.btn_checkout = StyledButton(btn_frame, "✖ Check-Out",
                                         self._do_checkout, theme=t, style="danger")
        self.btn_checkout.pack(fill="x", padx=10, pady=2)

        self.btn_maintenance = StyledButton(btn_frame, "🔧 Mantenimiento",
                                            self._toggle_maintenance,
                                            theme=t, style="warning")
        self.btn_maintenance.pack(fill="x", padx=10, pady=2)

        self.btn_edit = StyledButton(btn_frame, "✏ Editar",
                                     self._edit_room, theme=t, style="secondary")
        self.btn_edit.pack(fill="x", padx=10, pady=2)

        self.selected_room = None

    # ── Actualización ─────────────────────────────────────────────────────────

    def refresh(self):
        # Limpiar grid
        for w in self.grid_inner.winfo_children():
            w.destroy()

        rooms = db.get_all_rooms()
        status_filter = self.filter_var.get() if hasattr(self, "filter_var") else "Todos"
        if status_filter != "Todos":
            rooms = [r for r in rooms if r["status"] == status_filter]

        t = self.theme
        col, cols_per_row = 0, 4

        for room in rooms:
            status = room["status"]
            if status == "disponible":
                card_bg = t["success"]
                text_fg = "#ffffff"
            elif status == "ocupada":
                card_bg = t["error"]
                text_fg = "#ffffff"
            else:
                card_bg = t["warning"]
                text_fg = "#ffffff"

            card = tk.Frame(self.grid_inner, bg=card_bg, cursor="hand2",
                            relief="raised", bd=1)
            card.grid(row=col // cols_per_row, column=col % cols_per_row,
                      padx=6, pady=6, sticky="nsew")
            self.grid_inner.columnconfigure(col % cols_per_row, weight=1)

            tk.Label(card, text=f"Hab. {room['number']}",
                     bg=card_bg, fg=text_fg,
                     font=(t["font"], 12, "bold")).pack(pady=(8, 0))
            tk.Label(card, text=room["type"],
                     bg=card_bg, fg=text_fg,
                     font=(t["font"], 9)).pack()
            tk.Label(card, text=f"Piso {room['floor']}",
                     bg=card_bg, fg=text_fg,
                     font=(t["font"], 8)).pack()
            tk.Label(card, text=f"${room['price_night']:.0f}/noche",
                     bg=card_bg, fg=text_fg,
                     font=(t["font"], 9, "bold")).pack(pady=(0, 8))

            room_id = room["id"]
            card.bind("<Button-1>", lambda e, r=room: self._select_room(r))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, r=room: self._select_room(r))

            col += 1

        self.selected_room = None
        self._clear_detail()

    def _select_room(self, room):
        self.selected_room = room
        t = self.theme
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("end",
            f"Habitación: {room['number']}\n"
            f"Tipo: {room['type']}\n"
            f"Piso: {room['floor']}\n"
            f"Capacidad: {room['capacity']} personas\n"
            f"Precio/noche: ${room['price_night']:.2f}\n"
            f"Estado: {room['status'].upper()}\n"
        )
        if room["description"]:
            self.detail_text.insert("end", f"\n{room['description']}")
        # Si está ocupada, mostrar huésped
        if room["status"] == "ocupada":
            reservations = db.get_active_reservations()
            for res in reservations:
                if res["room_id"] == room["id"]:
                    self.detail_text.insert("end",
                        f"\n\n── Huésped ──\n"
                        f"Nombre: {res['guest_name']}\n"
                        f"Check-in: {res['checkin'][:10]}\n"
                        f"Noches: {res['nights']}\n"
                        f"Total hab.: ${res['total_room']:.2f}"
                    )
                    break
        self.detail_text.config(state="disabled")

    def _clear_detail(self):
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("end", "Selecciona una habitación\npara ver sus detalles.")
        self.detail_text.config(state="disabled")

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _do_checkin(self):
        if not self.selected_room:
            messagebox.showwarning("Sin selección", "Selecciona una habitación primero.")
            return
        if self.selected_room["status"] != "disponible":
            messagebox.showwarning("No disponible",
                                   "La habitación no está disponible para check-in.")
            return
        CheckInDialog(self, self.theme, self.selected_room, self.refresh)

    def _do_checkout(self):
        if not self.selected_room:
            messagebox.showwarning("Sin selección", "Selecciona una habitación primero.")
            return
        if self.selected_room["status"] != "ocupada":
            messagebox.showwarning("No ocupada", "La habitación no está ocupada.")
            return
        reservations = db.get_active_reservations()
        res = next((r for r in reservations if r["room_id"] == self.selected_room["id"]), None)
        if not res:
            messagebox.showerror("Error", "No se encontró la reserva activa.")
            return
        if messagebox.askyesno(
            "Confirmar Check-Out",
            f"¿Confirmar check-out de {res['guest_name']} de la hab. {res['room_number']}?",
        ):
            db.checkout_reservation(res["id"])
            messagebox.showinfo("Check-Out", "Check-out realizado con éxito.")
            self.refresh()
            if self.app:
                self.app.update_status_bar()

    def _toggle_maintenance(self):
        if not self.selected_room:
            messagebox.showwarning("Sin selección", "Selecciona una habitación primero.")
            return
        room = self.selected_room
        if room["status"] == "ocupada":
            messagebox.showwarning("Ocupada", "No se puede poner en mantenimiento una habitación ocupada.")
            return
        new_status = "disponible" if room["status"] == "mantenimiento" else "mantenimiento"
        db.update_room_status(room["id"], new_status)
        self.refresh()

    def _edit_room(self):
        if not self.selected_room:
            messagebox.showwarning("Sin selección", "Selecciona una habitación primero.")
            return
        RoomFormDialog(self, self.theme, room=self.selected_room, on_save=self.refresh)

    def _new_room(self):
        RoomFormDialog(self, self.theme, on_save=self.refresh)


# ── Diálogos ──────────────────────────────────────────────────────────────────

class CheckInDialog(tk.Toplevel):
    def __init__(self, parent, theme, room, on_save=None):
        super().__init__(parent)
        self.theme = theme
        self.room = room
        self.on_save = on_save
        t = theme

        self.title(f"Check-In — Habitación {room['number']}")
        self.configure(bg=t["bg2"])
        self.resizable(False, False)
        self.grab_set()

        self._build()
        self._center()

    def _build(self):
        t = self.theme
        pad = {"padx": 16, "pady": 6}

        tk.Label(self, text=f"Check-In — Hab. {self.room['number']} ({self.room['type']})",
                 bg=t["bg2"], fg=t["gold"],
                 font=(t["font"], 13, "bold")).pack(**pad)

        # ── Datos del huésped ──
        guest_frame = tk.LabelFrame(self, text="Datos del Huésped",
                                    bg=t["bg2"], fg=t["fg2"],
                                    font=(t["font"], 9))
        guest_frame.pack(fill="x", padx=16, pady=6)

        self.e_name = LabeledEntry(guest_frame, "Nombre completo *", theme=t, width=30)
        self.e_name.pack(fill="x", padx=8, pady=4)
        self.e_id = LabeledEntry(guest_frame, "DNI / Pasaporte *", theme=t, width=20)
        self.e_id.pack(fill="x", padx=8, pady=4)
        self.e_phone = LabeledEntry(guest_frame, "Teléfono", theme=t, width=20)
        self.e_phone.pack(fill="x", padx=8, pady=4)
        self.e_email = LabeledEntry(guest_frame, "Email", theme=t, width=30)
        self.e_email.pack(fill="x", padx=8, pady=4)
        self.e_nationality = LabeledEntry(guest_frame, "Nacionalidad", theme=t, width=20)
        self.e_nationality.pack(fill="x", padx=8, pady=4)

        # ── Datos de la reserva ──
        res_frame = tk.LabelFrame(self, text="Datos de la Estadía",
                                  bg=t["bg2"], fg=t["fg2"],
                                  font=(t["font"], 9))
        res_frame.pack(fill="x", padx=16, pady=6)

        row1 = tk.Frame(res_frame, bg=t["bg2"])
        row1.pack(fill="x", padx=8, pady=4)

        tk.Label(row1, text="Noches *:", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(side="left")
        self.e_nights = tk.Spinbox(row1, from_=1, to=365, width=6,
                                   bg=t["entry_bg"], fg=t["fg"],
                                   buttonbackground=t["bg3"])
        self.e_nights.pack(side="left", padx=6)
        self.e_nights.bind("<FocusOut>", lambda e: self._update_total())
        self.e_nights.bind("<KeyRelease>", lambda e: self._update_total())

        self.lbl_price = tk.Label(row1, text=f"${self.room['price_night']:.2f}/noche",
                                  bg=t["bg2"], fg=t["accent2"],
                                  font=(t["font"], 9))
        self.lbl_price.pack(side="left", padx=10)

        self.lbl_total = tk.Label(res_frame, text="Total: $0.00",
                                  bg=t["bg2"], fg=t["accent"],
                                  font=(t["font"], 11, "bold"))
        self.lbl_total.pack(padx=8, pady=4, anchor="w")
        self._update_total()

        self.e_notes = LabeledEntry(res_frame, "Notas / Solicitudes especiales", theme=t, width=40)
        self.e_notes.pack(fill="x", padx=8, pady=4)

        # Botones
        btn_row = tk.Frame(self, bg=t["bg2"])
        btn_row.pack(pady=10)
        StyledButton(btn_row, "✔ Confirmar Check-In", self._save,
                     theme=t, style="success", width=22).pack(side="left", padx=6)
        StyledButton(btn_row, "✖ Cancelar", self.destroy,
                     theme=t, style="danger", width=14).pack(side="left", padx=6)

    def _update_total(self):
        try:
            nights = int(self.e_nights.get())
            total = nights * self.room["price_night"]
            self.lbl_total.config(text=f"Total habitación: ${total:.2f}")
        except (ValueError, TypeError):
            pass

    def _save(self):
        name = self.e_name.get().strip()
        id_num = self.e_id.get().strip()
        if not name or not id_num:
            messagebox.showerror("Campos requeridos",
                                 "El nombre y documento del huésped son obligatorios.")
            return
        try:
            nights = int(self.e_nights.get())
            if nights < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Ingresa un número de noches válido.")
            return

        total = nights * self.room["price_night"]
        guest_id = db.add_guest(
            name, id_num,
            self.e_email.get().strip(),
            self.e_phone.get().strip(),
            self.e_nationality.get().strip(),
        )
        db.create_reservation(
            self.room["id"], guest_id,
            datetime.now().isoformat(),
            nights, total,
            self.e_notes.get().strip(),
        )
        messagebox.showinfo("Check-In", f"Check-in de {name} realizado con éxito.\nTotal: ${total:.2f}")
        self.destroy()
        if self.on_save:
            self.on_save()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")


class RoomFormDialog(tk.Toplevel):
    def __init__(self, parent, theme, room=None, on_save=None):
        super().__init__(parent)
        self.theme = theme
        self.room = room
        self.on_save = on_save
        t = theme

        title = f"Editar Habitación {room['number']}" if room else "Nueva Habitación"
        self.title(title)
        self.configure(bg=t["bg2"])
        self.resizable(False, False)
        self.grab_set()
        self._build()
        self._center()

    def _build(self):
        t = self.theme
        r = self.room

        tk.Label(self, text="Datos de la Habitación",
                 bg=t["bg2"], fg=t["gold"],
                 font=(t["font"], 13, "bold")).pack(pady=(12, 6))

        self.e_number = LabeledEntry(self, "Número *", theme=t, width=10)
        self.e_number.pack(padx=20, pady=4, fill="x")

        tk.Label(self, text="Tipo *", bg=t["bg2"], fg=t["fg2"],
                 font=(t["font"], 9)).pack(padx=20, anchor="w")
        self.type_var = tk.StringVar()
        ttk.Combobox(self, textvariable=self.type_var,
                     values=["Estándar", "Deluxe", "Suite", "Suite Presidencial", "Penthouse"],
                     width=22, state="readonly").pack(padx=20, pady=(2, 6))

        self.e_capacity = LabeledEntry(self, "Capacidad (personas) *", theme=t, width=10)
        self.e_capacity.pack(padx=20, pady=4, fill="x")
        self.e_price = LabeledEntry(self, "Precio por noche *", theme=t, width=12)
        self.e_price.pack(padx=20, pady=4, fill="x")
        self.e_floor = LabeledEntry(self, "Piso *", theme=t, width=8)
        self.e_floor.pack(padx=20, pady=4, fill="x")
        self.e_desc = LabeledEntry(self, "Descripción", theme=t, width=32)
        self.e_desc.pack(padx=20, pady=4, fill="x")

        if r:
            self.e_number.set(r["number"])
            self.type_var.set(r["type"])
            self.e_capacity.set(str(r["capacity"]))
            self.e_price.set(str(r["price_night"]))
            self.e_floor.set(str(r["floor"]))
            self.e_desc.set(r["description"] or "")

        btn_row = tk.Frame(self, bg=t["bg2"])
        btn_row.pack(pady=10)
        StyledButton(btn_row, "💾 Guardar", self._save,
                     theme=t, style="success").pack(side="left", padx=6)
        StyledButton(btn_row, "✖ Cancelar", self.destroy,
                     theme=t, style="secondary").pack(side="left", padx=6)

    def _save(self):
        number = self.e_number.get().strip()
        rtype = self.type_var.get()
        try:
            capacity = int(self.e_capacity.get())
            price = float(self.e_price.get())
            floor = int(self.e_floor.get())
        except ValueError:
            messagebox.showerror("Error", "Verifica los campos numéricos.")
            return
        if not number or not rtype:
            messagebox.showerror("Error", "Número y tipo son obligatorios.")
            return

        desc = self.e_desc.get().strip()
        if self.room:
            db.update_room(self.room["id"], number, rtype, capacity, price, floor, desc)
        else:
            try:
                db.add_room(number, rtype, capacity, price, floor, desc)
            except Exception as exc:
                messagebox.showerror("Error", str(exc))
                return

        self.destroy()
        if self.on_save:
            self.on_save()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
