"""
spa.py – Módulo de Spa: servicios, citas y cobro.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from modules import database as db
from modules import estilos as st


class VentanaSpa(tk.Toplevel):
    """Gestión de servicios de Spa y agenda de citas."""

    MODULO = "spa"

    def __init__(self, parent, usuario: dict):
        super().__init__(parent)
        self.usuario = usuario
        self.title("Spa")
        self.configure(bg=st.OSCURO)
        self.geometry("1050x680")
        self._build_ui()
        self._cargar_servicios()
        self._cargar_citas()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        h = tk.Frame(self, bg=st.OSCURO_MEDIO,
                     highlightthickness=1, highlightbackground=st.DORADO)
        h.pack(fill=tk.X)
        tk.Label(h, text="💆  Spa",
                 font=("Segoe UI", 14, "bold"),
                 bg=st.OSCURO_MEDIO, fg=st.DORADO).pack(side=tk.LEFT, padx=16, pady=10)
        tk.Button(h, text="✕  Cerrar", command=self.destroy,
                  bg=st.OSCURO_MEDIO, fg=st.TEXTO_GRIS,
                  font=("Segoe UI", 9), relief="flat",
                  cursor="hand2").pack(side=tk.RIGHT, padx=12, pady=8)

        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tab_agenda  = tk.Frame(nb, bg=st.OSCURO)
        tab_citas   = tk.Frame(nb, bg=st.OSCURO)
        tab_cobrar  = tk.Frame(nb, bg=st.OSCURO)

        nb.add(tab_agenda,  text="  Nueva Cita  ")
        nb.add(tab_citas,   text="  Agenda  ")
        nb.add(tab_cobrar,  text="  Cobrar Servicio  ")

        self._build_tab_nueva_cita(tab_agenda)
        self._build_tab_agenda(tab_citas)
        self._build_tab_cobrar(tab_cobrar)

    # ── Tab: Nueva cita ───────────────────────────────────────────────────────

    def _build_tab_nueva_cita(self, parent):
        f = tk.Frame(parent, bg=st.OSCURO)
        f.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Columna formulario
        col1 = tk.Frame(f, bg=st.OSCURO)
        col1.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        tk.Label(col1, text="NUEVA CITA", font=("Segoe UI", 12, "bold"),
                 bg=st.OSCURO, fg=st.DORADO).pack(anchor=tk.W, pady=(0, 12))

        campos = [
            ("Cliente:",    "entry_cliente"),
            ("Fecha:",      "entry_fecha"),
            ("Hora:",       "entry_hora"),
            ("Terapeuta:",  "entry_terapeuta"),
            ("Notas:",      "entry_notas"),
        ]
        self._campos_cita: dict[str, tk.Entry] = {}
        for lbl, key in campos:
            tk.Label(col1, text=lbl, font=("Segoe UI", 10),
                     bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(anchor=tk.W)
            e = tk.Entry(col1, **st.estilo_entry(), width=26)
            e.configure(bg=st.OSCURO_CLARO)
            e.pack(fill=tk.X, pady=(2, 8))
            self._campos_cita[key] = e

        self._campos_cita["entry_fecha"].insert(0, date.today().isoformat())
        self._campos_cita["entry_hora"].insert(0, "10:00")

        tk.Button(col1, text="📅  Registrar Cita",
                  command=self._registrar_cita,
                  **st.estilo_boton_exito()).pack(fill=tk.X, pady=(8, 0))

        # Columna servicios
        col2 = tk.Frame(f, bg=st.OSCURO)
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(col2, text="SERVICIO", font=("Segoe UI", 12, "bold"),
                 bg=st.OSCURO, fg=st.DORADO).pack(anchor=tk.W, pady=(0, 12))

        self._combo_cat_spa = ttk.Combobox(col2, state="readonly",
                                           width=20, font=("Segoe UI", 10))
        self._combo_cat_spa.pack(anchor=tk.W, pady=(0, 6))
        self._combo_cat_spa.bind("<<ComboboxSelected>>",
                                 lambda _: self._filtrar_servicios())

        cols = ("nombre", "duracion", "precio")
        self._tree_srv = ttk.Treeview(col2, columns=cols, show="headings",
                                      selectmode="browse")
        self._tree_srv.heading("nombre",   text="Servicio")
        self._tree_srv.heading("duracion", text="Duración")
        self._tree_srv.heading("precio",   text="Precio")
        self._tree_srv.column("nombre",   width=200)
        self._tree_srv.column("duracion", width=80, anchor=tk.CENTER)
        self._tree_srv.column("precio",   width=90, anchor=tk.E)
        _aplicar_estilo_tree(self._tree_srv)
        sb = tk.Scrollbar(col2, command=self._tree_srv.yview,
                          bg=st.OSCURO_MEDIO, troughcolor=st.OSCURO)
        self._tree_srv.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree_srv.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

    # ── Tab: Agenda ───────────────────────────────────────────────────────────

    def _build_tab_agenda(self, parent):
        top = tk.Frame(parent, bg=st.OSCURO)
        top.pack(fill=tk.X, padx=8, pady=(8, 4))
        tk.Label(top, text="Filtrar por fecha:", font=("Segoe UI", 10),
                 bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(side=tk.LEFT, padx=(0, 8))
        self._entry_filtro_fecha = tk.Entry(top, **st.estilo_entry(), width=14)
        self._entry_filtro_fecha.configure(bg=st.OSCURO_CLARO)
        self._entry_filtro_fecha.insert(0, date.today().isoformat())
        self._entry_filtro_fecha.pack(side=tk.LEFT)
        tk.Button(top, text="🔍 Buscar",
                  command=self._cargar_citas,
                  **st.estilo_boton_secundario()).pack(side=tk.LEFT, padx=6)
        tk.Button(top, text="Ver todas",
                  command=lambda: (self._entry_filtro_fecha.delete(0, tk.END),
                                   self._cargar_citas()),
                  bg=st.OSCURO_CLARO, fg=st.TEXTO_GRIS,
                  font=("Segoe UI", 9), relief="flat", cursor="hand2",
                  padx=8, pady=4).pack(side=tk.LEFT)

        cols = ("cliente", "servicio", "fecha", "hora", "terapeuta", "estado")
        self._tree_agenda = ttk.Treeview(parent, columns=cols, show="headings",
                                         selectmode="browse")
        self._tree_agenda.heading("cliente",   text="Cliente")
        self._tree_agenda.heading("servicio",  text="Servicio")
        self._tree_agenda.heading("fecha",     text="Fecha")
        self._tree_agenda.heading("hora",      text="Hora")
        self._tree_agenda.heading("terapeuta", text="Terapeuta")
        self._tree_agenda.heading("estado",    text="Estado")
        self._tree_agenda.column("cliente",   width=140)
        self._tree_agenda.column("servicio",  width=180)
        self._tree_agenda.column("fecha",     width=90, anchor=tk.CENTER)
        self._tree_agenda.column("hora",      width=60, anchor=tk.CENTER)
        self._tree_agenda.column("terapeuta", width=120)
        self._tree_agenda.column("estado",    width=90, anchor=tk.CENTER)
        _aplicar_estilo_tree(self._tree_agenda)

        sb = tk.Scrollbar(parent, command=self._tree_agenda.yview,
                          bg=st.OSCURO_MEDIO, troughcolor=st.OSCURO)
        self._tree_agenda.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree_agenda.pack(fill=tk.BOTH, expand=True, padx=(8, 0), pady=(0, 8))

        bf = tk.Frame(parent, bg=st.OSCURO)
        bf.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(bf, text="✅ Completar",
                  command=lambda: self._cambiar_estado_cita("completada"),
                  **st.estilo_boton_exito()).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(bf, text="❌ Cancelar",
                  command=lambda: self._cambiar_estado_cita("cancelada"),
                  **st.estilo_boton_peligro()).pack(side=tk.LEFT)

    # ── Tab: Cobrar servicio ──────────────────────────────────────────────────

    def _build_tab_cobrar(self, parent):
        f = tk.Frame(parent, bg=st.OSCURO)
        f.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        tk.Label(f, text="COBRAR SERVICIO DIRECTO",
                 font=("Segoe UI", 12, "bold"),
                 bg=st.OSCURO, fg=st.DORADO).pack(anchor=tk.W, pady=(0, 16))

        # Selección de servicio
        tk.Label(f, text="Seleccione servicio:", font=("Segoe UI", 10),
                 bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(anchor=tk.W)
        self._combo_srv_cobro = ttk.Combobox(f, state="readonly",
                                             width=35, font=("Segoe UI", 11))
        self._combo_srv_cobro.pack(fill=tk.X, pady=(4, 12))
        self._combo_srv_cobro.bind("<<ComboboxSelected>>",
                                   self._actualizar_precio_cobro)

        tk.Label(f, text="Cliente:", font=("Segoe UI", 10),
                 bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(anchor=tk.W)
        self._entry_cliente_cobro = tk.Entry(f, **st.estilo_entry(), width=32)
        self._entry_cliente_cobro.configure(bg=st.OSCURO_CLARO)
        self._entry_cliente_cobro.pack(fill=tk.X, pady=(4, 12))

        self._lbl_precio_cobro = tk.Label(f, text="Precio: $0.00",
                                          font=("Segoe UI", 14, "bold"),
                                          bg=st.OSCURO, fg=st.DORADO)
        self._lbl_precio_cobro.pack(pady=(8, 16))

        tk.Button(f, text="💳  Cobrar Ahora",
                  command=self._cobrar_servicio,
                  **st.estilo_boton_exito()).pack(pady=8)

    # ── Datos ─────────────────────────────────────────────────────────────────

    def _cargar_servicios(self):
        conn = db.get_connection()
        prods = conn.execute(
            "SELECT * FROM productos WHERE modulo=? AND activo=1 ORDER BY categoria,nombre",
            (self.MODULO,)
        ).fetchall()
        conn.close()
        self._servicios = [dict(p) for p in prods]

        cats = ["Todas"] + sorted({p["categoria"] for p in self._servicios})
        self._combo_cat_spa["values"] = cats
        self._combo_cat_spa.set("Todas")
        self._filtrar_servicios()

        simbolo = db.get_config("moneda_simbolo", "$")
        self._combo_srv_cobro["values"] = [
            f"{p['nombre']} – {simbolo}{p['precio']:.2f}"
            for p in self._servicios
        ]

    def _filtrar_servicios(self):
        cat = self._combo_cat_spa.get()
        for row in self._tree_srv.get_children():
            self._tree_srv.delete(row)
        simbolo = db.get_config("moneda_simbolo", "$")
        duraciones = {
            "Masajes": "60 min", "Faciales": "60 min",
            "Tratamientos": "45 min", "Paquetes": "3+ h",
        }
        for p in self._servicios:
            if cat == "Todas" or p["categoria"] == cat:
                dur = duraciones.get(p["categoria"], "60 min")
                self._tree_srv.insert("", tk.END,
                    values=(p["nombre"], dur, f"{simbolo}{p['precio']:.2f}"),
                    tags=(str(p["id"]),))

    def _cargar_citas(self):
        for row in self._tree_agenda.get_children():
            self._tree_agenda.delete(row)
        conn = db.get_connection()
        filtro_fecha = self._entry_filtro_fecha.get().strip()
        if filtro_fecha:
            rows = conn.execute("""
                SELECT c.*, p.nombre as srv_nombre
                FROM spa_citas c
                JOIN productos p ON p.id = c.servicio_id
                WHERE c.fecha = ?
                ORDER BY c.hora
            """, (filtro_fecha,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT c.*, p.nombre as srv_nombre
                FROM spa_citas c
                JOIN productos p ON p.id = c.servicio_id
                ORDER BY c.fecha, c.hora
            """).fetchall()
        conn.close()
        self._citas_data = [dict(r) for r in rows]
        colores = {"programada": st.DORADO, "completada": st.EXITO,
                   "cancelada": st.ERROR}
        for c in self._citas_data:
            tag = c["estado"]
            self._tree_agenda.insert("", tk.END, values=(
                c["cliente_nombre"], c["srv_nombre"],
                c["fecha"], c["hora"],
                c["terapeuta"], c["estado"].upper(),
            ), tags=(tag, str(c["id"])))
        for estado, color in colores.items():
            self._tree_agenda.tag_configure(estado, foreground=color)

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _registrar_cita(self):
        sel = self._tree_srv.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Seleccione un servicio.", parent=self)
            return
        tag = self._tree_srv.item(sel[0], "tags")[0]
        srv_id = int(tag)
        c = self._campos_cita
        cliente = c["entry_cliente"].get().strip()
        if not cliente:
            messagebox.showwarning("Datos incompletos",
                                   "Ingrese el nombre del cliente.", parent=self)
            return
        fecha = c["entry_fecha"].get().strip()
        hora  = c["entry_hora"].get().strip()
        if not fecha or not hora:
            messagebox.showwarning("Datos incompletos",
                                   "Ingrese fecha y hora.", parent=self)
            return
        conn = db.get_connection()
        conn.execute("""
            INSERT INTO spa_citas
                (cliente_nombre, servicio_id, fecha, hora,
                 terapeuta, estado, notas)
            VALUES (?,?,?,?,?,?,?)
        """, (cliente, srv_id, fecha, hora,
              c["entry_terapeuta"].get().strip(),
              "programada",
              c["entry_notas"].get().strip()))
        conn.commit()
        conn.close()
        messagebox.showinfo("Cita registrada",
                            f"Cita de {cliente} registrada para {fecha} a las {hora}.",
                            parent=self)
        for e in c.values():
            e.delete(0, tk.END)
        self._campos_cita["entry_fecha"].insert(0, date.today().isoformat())
        self._campos_cita["entry_hora"].insert(0, "10:00")
        self._cargar_citas()

    def _cambiar_estado_cita(self, estado: str):
        sel = self._tree_agenda.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Seleccione una cita.", parent=self)
            return
        tags = self._tree_agenda.item(sel[0], "tags")
        cita_id = int(tags[1]) if len(tags) > 1 else None
        if cita_id is None:
            return
        conn = db.get_connection()
        conn.execute("UPDATE spa_citas SET estado=? WHERE id=?",
                     (estado, cita_id))
        conn.commit()
        conn.close()
        self._cargar_citas()

    def _actualizar_precio_cobro(self, _e=None):
        idx = self._combo_srv_cobro.current()
        if idx < 0 or idx >= len(self._servicios):
            return
        srv = self._servicios[idx]
        simbolo = db.get_config("moneda_simbolo", "$")
        pct = float(db.get_config("impuesto_pct", "16")) / 100
        total = srv["precio"] * (1 + pct)
        self._lbl_precio_cobro.config(
            text=f"Precio: {simbolo}{srv['precio']:.2f}  +IVA = {simbolo}{total:.2f}")

    def _cobrar_servicio(self):
        idx = self._combo_srv_cobro.current()
        if idx < 0:
            messagebox.showwarning("Sin selección",
                                   "Seleccione un servicio.", parent=self)
            return
        srv = self._servicios[idx]
        cliente = self._entry_cliente_cobro.get().strip() or "Cliente"
        simbolo = db.get_config("moneda_simbolo", "$")
        pct = float(db.get_config("impuesto_pct", "16")) / 100
        impuesto = srv["precio"] * pct
        total    = srv["precio"] + impuesto

        metodo = st.dialogo_metodo_pago(self, total, simbolo)
        if not metodo:
            return

        conn = db.get_connection()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO ordenes (modulo, referencia, usuario_id, estado,
                                 subtotal, impuesto, total, metodo_pago)
            VALUES (?,?,?,?,?,?,?,?)
        """, (self.MODULO, cliente, self.usuario.get("id"), "cerrada",
              srv["precio"], impuesto, total, metodo))
        orden_id = cur.lastrowid
        cur.execute("""
            INSERT INTO orden_items (orden_id, producto_id, cantidad,
                                    precio_unitario, subtotal)
            VALUES (?,?,?,?,?)
        """, (orden_id, srv["id"], 1, srv["precio"], srv["precio"]))
        conn.commit()
        conn.close()

        messagebox.showinfo("Cobro exitoso",
                            f"Servicio cobrado.\n"
                            f"Cliente: {cliente}\n"
                            f"Servicio: {srv['nombre']}\n"
                            f"Total: {simbolo}{total:.2f}",
                            parent=self)
        self._entry_cliente_cobro.delete(0, tk.END)
        self._combo_srv_cobro.set("")
        self._lbl_precio_cobro.config(text="Precio: $0.00")


def _aplicar_estilo_tree(tree: ttk.Treeview):
    st.aplicar_estilo_tree(tree)
