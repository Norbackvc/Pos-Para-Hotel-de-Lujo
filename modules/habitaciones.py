"""
habitaciones.py – Módulo de Habitaciones: listado, check-in, check-out y estado.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta

from modules import database as db
from modules import estilos as st


class VentanaHabitaciones(tk.Toplevel):
    """Gestión de habitaciones y reservaciones."""

    def __init__(self, parent, usuario: dict):
        super().__init__(parent)
        self.usuario = usuario
        self.title("Habitaciones")
        self.configure(bg=st.OSCURO)
        self.geometry("1100x700")
        self._build_ui()
        self._cargar_habitaciones()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        h = tk.Frame(self, bg=st.OSCURO_MEDIO,
                     highlightthickness=1, highlightbackground=st.DORADO)
        h.pack(fill=tk.X)
        tk.Label(h, text="🛏️  Habitaciones",
                 font=("Segoe UI", 14, "bold"),
                 bg=st.OSCURO_MEDIO, fg=st.DORADO).pack(side=tk.LEFT, padx=16, pady=10)
        tk.Button(h, text="✕  Cerrar", command=self.destroy,
                  bg=st.OSCURO_MEDIO, fg=st.TEXTO_GRIS,
                  font=("Segoe UI", 9), relief="flat",
                  cursor="hand2").pack(side=tk.RIGHT, padx=12, pady=8)

        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                               bg=st.OSCURO, sashwidth=6)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        izq = self._panel_lista(paned)
        der = self._panel_detalle(paned)
        paned.add(izq, minsize=300)
        paned.add(der, minsize=380)

    def _panel_lista(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=st.OSCURO)

        top = tk.Frame(f, bg=st.OSCURO)
        top.pack(fill=tk.X, padx=8, pady=(8, 4))
        tk.Label(top, text="HABITACIONES", font=("Segoe UI", 10, "bold"),
                 bg=st.OSCURO, fg=st.DORADO).pack(side=tk.LEFT)

        # Filtro de estado
        self._filtro_var = tk.StringVar(value="Todas")
        combo = ttk.Combobox(top, textvariable=self._filtro_var,
                             values=["Todas", "disponible", "ocupada", "mantenimiento"],
                             state="readonly", width=14, font=("Segoe UI", 10))
        combo.pack(side=tk.RIGHT)
        combo.bind("<<ComboboxSelected>>", lambda _: self._cargar_habitaciones())

        cols = ("numero", "tipo", "precio", "capacidad", "estado")
        self._tree = ttk.Treeview(f, columns=cols, show="headings",
                                  selectmode="browse")
        self._tree.heading("numero",    text="Núm.")
        self._tree.heading("tipo",      text="Tipo")
        self._tree.heading("precio",    text="Precio/noche")
        self._tree.heading("capacidad", text="Cap.")
        self._tree.heading("estado",    text="Estado")
        self._tree.column("numero",    width=55,  anchor=tk.CENTER)
        self._tree.column("tipo",      width=130)
        self._tree.column("precio",    width=110, anchor=tk.E)
        self._tree.column("capacidad", width=45,  anchor=tk.CENTER)
        self._tree.column("estado",    width=100, anchor=tk.CENTER)
        _aplicar_estilo_tree(self._tree)

        sb = tk.Scrollbar(f, command=self._tree.yview,
                          bg=st.OSCURO_MEDIO, troughcolor=st.OSCURO)
        self._tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(fill=tk.BOTH, expand=True, padx=(8, 0), pady=(0, 8))
        self._tree.bind("<<TreeviewSelect>>", self._al_seleccionar)

        # Botones de estado rápido
        bf = tk.Frame(f, bg=st.OSCURO)
        bf.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(bf, text="🔧 Mantenimiento",
                  command=lambda: self._cambiar_estado("mantenimiento"),
                  bg=st.OSCURO_CLARO, fg=st.ADVERTENCIA,
                  font=("Segoe UI", 9, "bold"), relief="flat",
                  cursor="hand2", padx=8, pady=6).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(bf, text="✅ Disponible",
                  command=lambda: self._cambiar_estado("disponible"),
                  **st.estilo_boton_exito()).pack(side=tk.LEFT)
        return f

    def _panel_detalle(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=st.OSCURO)

        nb = ttk.Notebook(f)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Tab Check-in
        tab_checkin = tk.Frame(nb, bg=st.OSCURO)
        nb.add(tab_checkin, text="Check-in")
        self._build_tab_checkin(tab_checkin)

        # Tab Reservaciones activas
        tab_res = tk.Frame(nb, bg=st.OSCURO)
        nb.add(tab_res, text="Reservaciones")
        self._build_tab_reservaciones(tab_res)

        return f

    def _build_tab_checkin(self, parent):
        form = tk.Frame(parent, bg=st.OSCURO)
        form.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        self._lbl_hab_sel = tk.Label(form, text="Seleccione una habitación",
                                     font=("Segoe UI", 11, "bold"),
                                     bg=st.OSCURO, fg=st.DORADO)
        self._lbl_hab_sel.grid(row=0, column=0, columnspan=2,
                               sticky=tk.W, pady=(0, 12))

        campos = [
            ("Cliente:",         "entry_cliente"),
            ("Email:",           "entry_email"),
            ("Fecha entrada:",   "entry_entrada"),
            ("Fecha salida:",    "entry_salida"),
            ("Adultos:",         "entry_adultos"),
            ("Niños:",           "entry_ninos"),
            ("Notas:",           "entry_notas"),
        ]
        self._campos_checkin: dict[str, tk.Entry] = {}
        for i, (lbl, key) in enumerate(campos, start=1):
            tk.Label(form, text=lbl, font=("Segoe UI", 10),
                     bg=st.OSCURO, fg=st.TEXTO_GRIS).grid(
                row=i, column=0, sticky=tk.W, pady=4, padx=(0, 8))
            e = tk.Entry(form, **st.estilo_entry(), width=28)
            e.configure(bg=st.OSCURO_CLARO)
            e.grid(row=i, column=1, sticky=tk.EW, pady=4)
            self._campos_checkin[key] = e
            form.columnconfigure(1, weight=1)

        hoy  = date.today().isoformat()
        manana = (date.today() + timedelta(days=1)).isoformat()
        self._campos_checkin["entry_entrada"].insert(0, hoy)
        self._campos_checkin["entry_salida"].insert(0, manana)
        self._campos_checkin["entry_adultos"].insert(0, "2")
        self._campos_checkin["entry_ninos"].insert(0, "0")

        self._lbl_precio_total = tk.Label(form, text="Total estimado: $0.00",
                                          font=("Segoe UI", 11, "bold"),
                                          bg=st.OSCURO, fg=st.DORADO)
        self._lbl_precio_total.grid(row=len(campos)+1, column=0,
                                    columnspan=2, pady=(8, 4))

        tk.Button(form, text="✅  Registrar Check-in",
                  command=self._registrar_checkin,
                  **st.estilo_boton_exito()).grid(
            row=len(campos)+2, column=0, columnspan=2,
            sticky=tk.EW, pady=(8, 0))

        # Actualizar total al cambiar fechas
        for key in ("entry_entrada", "entry_salida"):
            self._campos_checkin[key].bind("<FocusOut>", lambda _: self._actualizar_precio())

    def _build_tab_reservaciones(self, parent):
        cols = ("cliente", "habitacion", "entrada", "salida", "total", "estado")
        self._tree_res = ttk.Treeview(parent, columns=cols, show="headings",
                                      selectmode="browse")
        self._tree_res.heading("cliente",    text="Cliente")
        self._tree_res.heading("habitacion", text="Hab.")
        self._tree_res.heading("entrada",    text="Entrada")
        self._tree_res.heading("salida",     text="Salida")
        self._tree_res.heading("total",      text="Total")
        self._tree_res.heading("estado",     text="Estado")
        self._tree_res.column("cliente",    width=140)
        self._tree_res.column("habitacion", width=50, anchor=tk.CENTER)
        self._tree_res.column("entrada",    width=90, anchor=tk.CENTER)
        self._tree_res.column("salida",     width=90, anchor=tk.CENTER)
        self._tree_res.column("total",      width=90, anchor=tk.E)
        self._tree_res.column("estado",     width=90, anchor=tk.CENTER)
        _aplicar_estilo_tree(self._tree_res)

        sb = tk.Scrollbar(parent, command=self._tree_res.yview,
                          bg=st.OSCURO_MEDIO, troughcolor=st.OSCURO)
        self._tree_res.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree_res.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        bf = tk.Frame(parent, bg=st.OSCURO)
        bf.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(bf, text="🚪 Check-out",
                  command=self._checkout,
                  **st.estilo_boton_peligro()).pack(side=tk.LEFT)
        tk.Button(bf, text="🔄 Actualizar",
                  command=self._cargar_reservaciones,
                  **st.estilo_boton_secundario()).pack(side=tk.RIGHT)

        self._cargar_reservaciones()

    # ── Datos ─────────────────────────────────────────────────────────────────

    def _cargar_habitaciones(self):
        for row in self._tree.get_children():
            self._tree.delete(row)
        conn = db.get_connection()
        filtro = self._filtro_var.get()
        if filtro == "Todas":
            habs = conn.execute(
                "SELECT * FROM habitaciones ORDER BY numero"
            ).fetchall()
        else:
            habs = conn.execute(
                "SELECT * FROM habitaciones WHERE estado=? ORDER BY numero",
                (filtro,)
            ).fetchall()
        conn.close()
        self._habs_data = [dict(h) for h in habs]
        simbolo = db.get_config("moneda_simbolo", "$")
        colores = {"disponible": st.EXITO, "ocupada": st.ERROR,
                   "mantenimiento": st.ADVERTENCIA}
        for h in self._habs_data:
            tag = h["estado"]
            self._tree.insert("", tk.END,
                values=(h["numero"], h["tipo"],
                        f"{simbolo}{h['precio_noche']:.2f}",
                        h["capacidad"], h["estado"].upper()),
                tags=(tag,))
        for estado, color in colores.items():
            self._tree.tag_configure(estado, foreground=color)

    def _cargar_reservaciones(self):
        for row in self._tree_res.get_children():
            self._tree_res.delete(row)
        conn = db.get_connection()
        rows = conn.execute("""
            SELECT r.*, h.numero as num_hab
            FROM reservaciones r
            JOIN habitaciones h ON h.id = r.habitacion_id
            WHERE r.estado = 'activa'
            ORDER BY r.fecha_entrada
        """).fetchall()
        conn.close()
        simbolo = db.get_config("moneda_simbolo", "$")
        self._reservaciones_data = [dict(r) for r in rows]
        for r in self._reservaciones_data:
            self._tree_res.insert("", tk.END, values=(
                r["cliente_nombre"], r["num_hab"],
                r["fecha_entrada"], r["fecha_salida"],
                f"{simbolo}{r['precio_total']:.2f}",
                r["estado"].upper(),
            ), tags=(str(r["id"]),))

    def _al_seleccionar(self, _e=None):
        sel = self._tree.selection()
        if not sel:
            return
        idx = self._tree.index(sel[0])
        if idx >= len(self._habs_data):
            return
        hab = self._habs_data[idx]
        simbolo = db.get_config("moneda_simbolo", "$")
        self._lbl_hab_sel.config(
            text=f"Hab. {hab['numero']} – {hab['tipo']}  |  "
                 f"{simbolo}{hab['precio_noche']:.2f}/noche  |  {hab['estado'].upper()}"
        )
        self._actualizar_precio(hab)

    def _actualizar_precio(self, hab: dict | None = None):
        if hab is None:
            sel = self._tree.selection()
            if not sel:
                return
            idx = self._tree.index(sel[0])
            if idx >= len(self._habs_data):
                return
            hab = self._habs_data[idx]
        try:
            entrada = date.fromisoformat(
                self._campos_checkin["entry_entrada"].get().strip())
            salida  = date.fromisoformat(
                self._campos_checkin["entry_salida"].get().strip())
            noches = (salida - entrada).days
            if noches <= 0:
                raise ValueError
            total = noches * hab["precio_noche"]
            simbolo = db.get_config("moneda_simbolo", "$")
            self._lbl_precio_total.config(
                text=f"Total estimado ({noches} noche{'s' if noches != 1 else ''}): "
                     f"{simbolo}{total:.2f}")
        except (ValueError, KeyError):
            self._lbl_precio_total.config(text="Total estimado: —")

    def _registrar_checkin(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Seleccione una habitación primero.", parent=self)
            return
        idx  = self._tree.index(sel[0])
        hab  = self._habs_data[idx]

        if hab["estado"] != "disponible":
            messagebox.showwarning("No disponible",
                                   f"La habitación {hab['numero']} "
                                   f"está {hab['estado']}.", parent=self)
            return

        c = self._campos_checkin
        cliente = c["entry_cliente"].get().strip()
        if not cliente:
            messagebox.showwarning("Datos incompletos",
                                   "Ingrese el nombre del cliente.", parent=self)
            return
        try:
            entrada = date.fromisoformat(c["entry_entrada"].get().strip())
            salida  = date.fromisoformat(c["entry_salida"].get().strip())
            noches  = (salida - entrada).days
            if noches <= 0:
                raise ValueError("Fechas inválidas")
        except ValueError as exc:
            messagebox.showerror("Fechas inválidas",
                                 str(exc) or "Use el formato AAAA-MM-DD.", parent=self)
            return

        total = noches * hab["precio_noche"]
        conn  = db.get_connection()
        conn.execute("""
            INSERT INTO reservaciones
                (habitacion_id, cliente_nombre, cliente_email,
                 fecha_entrada, fecha_salida, adultos, ninos,
                 precio_total, estado, notas)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (hab["id"], cliente,
              c["entry_email"].get().strip(),
              entrada.isoformat(), salida.isoformat(),
              int(c["entry_adultos"].get() or 1),
              int(c["entry_ninos"].get() or 0),
              total, "activa",
              c["entry_notas"].get().strip()))
        conn.execute("UPDATE habitaciones SET estado='ocupada' WHERE id=?",
                     (hab["id"],))
        conn.commit()
        conn.close()

        simbolo = db.get_config("moneda_simbolo", "$")
        messagebox.showinfo("Check-in registrado",
                            f"Check-in exitoso.\n"
                            f"Cliente: {cliente}\n"
                            f"Hab. {hab['numero']}  –  {noches} noche(s)\n"
                            f"Total: {simbolo}{total:.2f}",
                            parent=self)
        self._cargar_habitaciones()
        self._cargar_reservaciones()

    def _checkout(self):
        sel = self._tree_res.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Seleccione una reservación para hacer check-out.",
                                   parent=self)
            return
        tag = self._tree_res.item(sel[0], "tags")[0]
        res_id = int(tag)
        res = next((r for r in self._reservaciones_data if r["id"] == res_id), None)
        if not res:
            return
        simbolo = db.get_config("moneda_simbolo", "$")
        if not messagebox.askyesno("Confirmar Check-out",
                                   f"¿Confirmar check-out de {res['cliente_nombre']}?\n"
                                   f"Total: {simbolo}{res['precio_total']:.2f}",
                                   parent=self):
            return
        conn = db.get_connection()
        conn.execute("UPDATE reservaciones SET estado='completada' WHERE id=?",
                     (res_id,))
        conn.execute("UPDATE habitaciones SET estado='disponible' WHERE id=?",
                     (res["habitacion_id"],))
        conn.commit()
        conn.close()
        messagebox.showinfo("Check-out",
                            f"Check-out de {res['cliente_nombre']} realizado.",
                            parent=self)
        self._cargar_habitaciones()
        self._cargar_reservaciones()

    def _cambiar_estado(self, estado: str):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Seleccione una habitación.", parent=self)
            return
        idx = self._tree.index(sel[0])
        hab = self._habs_data[idx]
        conn = db.get_connection()
        conn.execute("UPDATE habitaciones SET estado=? WHERE id=?",
                     (estado, hab["id"]))
        conn.commit()
        conn.close()
        self._cargar_habitaciones()


def _aplicar_estilo_tree(tree: ttk.Treeview):
    st.aplicar_estilo_tree(tree)
