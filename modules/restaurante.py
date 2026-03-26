"""
restaurante.py – Módulo de Restaurante: mesas, menú, órdenes y cobro.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

from modules import database as db
from modules import estilos as st


class VentanaRestaurante(tk.Toplevel):
    """Gestión del restaurante: selección de mesa, toma de orden y cobro."""

    MODULO = "restaurante"

    def __init__(self, parent, usuario: dict):
        super().__init__(parent)
        self.usuario = usuario
        self.title("Restaurante")
        self.configure(bg=st.OSCURO)
        self.geometry("1100x700")
        self._orden_actual: list[dict] = []
        self._mesa_sel: dict | None = None
        self._orden_id: int | None = None
        self._build_ui()
        self._cargar_mesas()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                               bg=st.OSCURO, sashwidth=6,
                               sashrelief="flat", sashpad=2)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._panel_mesas   = self._crear_panel_mesas(paned)
        self._panel_menu    = self._crear_panel_menu(paned)
        self._panel_orden   = self._crear_panel_orden(paned)

        paned.add(self._panel_mesas,  minsize=160)
        paned.add(self._panel_menu,   minsize=300)
        paned.add(self._panel_orden,  minsize=280)

    def _build_header(self):
        h = tk.Frame(self, bg=st.OSCURO_MEDIO,
                     highlightthickness=1, highlightbackground=st.DORADO)
        h.pack(fill=tk.X)
        tk.Label(h, text="🍽️  Restaurante",
                 font=("Segoe UI", 14, "bold"),
                 bg=st.OSCURO_MEDIO, fg=st.DORADO).pack(side=tk.LEFT, padx=16, pady=10)
        tk.Button(h, text="✕  Cerrar", command=self.destroy,
                  bg=st.OSCURO_MEDIO, fg=st.TEXTO_GRIS,
                  font=("Segoe UI", 9), relief="flat",
                  cursor="hand2").pack(side=tk.RIGHT, padx=12, pady=8)

    # Panel mesas
    def _crear_panel_mesas(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=st.OSCURO)
        tk.Label(f, text="MESAS", font=("Segoe UI", 10, "bold"),
                 bg=st.OSCURO, fg=st.DORADO).pack(anchor=tk.W, padx=8, pady=(8, 4))

        self._lista_mesas = tk.Listbox(f, **st.estilo_listbox(), width=16)
        sb = tk.Scrollbar(f, command=self._lista_mesas.yview,
                          bg=st.OSCURO_MEDIO, troughcolor=st.OSCURO)
        self._lista_mesas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._lista_mesas.pack(fill=tk.BOTH, expand=True, padx=(8, 0), pady=(0, 8))
        self._lista_mesas.bind("<<ListboxSelect>>", self._al_seleccionar_mesa)

        self._lbl_mesa_info = tk.Label(f, text="", font=("Segoe UI", 8),
                                       bg=st.OSCURO, fg=st.TEXTO_GRIS,
                                       wraplength=150, justify=tk.LEFT)
        self._lbl_mesa_info.pack(padx=8, pady=2)
        return f

    # Panel menú
    def _crear_panel_menu(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=st.OSCURO)
        top = tk.Frame(f, bg=st.OSCURO)
        top.pack(fill=tk.X, padx=8, pady=(8, 4))
        tk.Label(top, text="MENÚ", font=("Segoe UI", 10, "bold"),
                 bg=st.OSCURO, fg=st.DORADO).pack(side=tk.LEFT)

        self._combo_cat = ttk.Combobox(top, state="readonly", width=18,
                                       font=("Segoe UI", 10))
        self._combo_cat.pack(side=tk.RIGHT)
        self._combo_cat.bind("<<ComboboxSelected>>", lambda _: self._filtrar_menu())

        cols = ("nombre", "precio")
        self._tree_menu = ttk.Treeview(f, columns=cols, show="headings",
                                       selectmode="browse")
        self._tree_menu.heading("nombre", text="Producto")
        self._tree_menu.heading("precio", text="Precio")
        self._tree_menu.column("nombre", width=220)
        self._tree_menu.column("precio", width=80, anchor=tk.E)
        self._aplicar_estilo_tree(self._tree_menu)

        sb = tk.Scrollbar(f, command=self._tree_menu.yview,
                          bg=st.OSCURO_MEDIO, troughcolor=st.OSCURO)
        self._tree_menu.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree_menu.pack(fill=tk.BOTH, expand=True, padx=(8, 0), pady=(0, 4))
        self._tree_menu.bind("<Double-1>", self._agregar_al_orden)

        tk.Button(f, text="➕  Agregar al orden",
                  command=self._agregar_al_orden,
                  **st.estilo_boton_secundario()).pack(padx=8, pady=8, fill=tk.X)
        self._cargar_menu()
        return f

    # Panel orden
    def _crear_panel_orden(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=st.OSCURO)
        tk.Label(f, text="ORDEN ACTUAL", font=("Segoe UI", 10, "bold"),
                 bg=st.OSCURO, fg=st.DORADO).pack(anchor=tk.W, padx=8, pady=(8, 4))

        cols = ("cant", "producto", "precio", "subtotal")
        self._tree_orden = ttk.Treeview(f, columns=cols, show="headings",
                                        selectmode="browse", height=16)
        self._tree_orden.heading("cant",     text="Cant")
        self._tree_orden.heading("producto", text="Producto")
        self._tree_orden.heading("precio",   text="P.U.")
        self._tree_orden.heading("subtotal", text="Subtotal")
        self._tree_orden.column("cant",     width=40,  anchor=tk.CENTER)
        self._tree_orden.column("producto", width=160)
        self._tree_orden.column("precio",   width=70,  anchor=tk.E)
        self._tree_orden.column("subtotal", width=80,  anchor=tk.E)
        self._aplicar_estilo_tree(self._tree_orden)

        sb = tk.Scrollbar(f, command=self._tree_orden.yview,
                          bg=st.OSCURO_MEDIO, troughcolor=st.OSCURO)
        self._tree_orden.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree_orden.pack(fill=tk.BOTH, expand=True, padx=(8, 0), pady=(0, 4))

        # Totales
        tot = tk.Frame(f, bg=st.OSCURO_MEDIO,
                       highlightthickness=1, highlightbackground=st.DORADO)
        tot.pack(fill=tk.X, padx=8, pady=4)
        self._lbl_subtotal = tk.Label(tot, text="Subtotal:  $0.00",
                                      font=("Segoe UI", 10), bg=st.OSCURO_MEDIO, fg=st.TEXTO_CLARO)
        self._lbl_subtotal.pack(anchor=tk.E, padx=12, pady=2)
        self._lbl_impuesto = tk.Label(tot, text="IVA (16%):  $0.00",
                                      font=("Segoe UI", 10), bg=st.OSCURO_MEDIO, fg=st.TEXTO_CLARO)
        self._lbl_impuesto.pack(anchor=tk.E, padx=12, pady=2)
        self._lbl_total = tk.Label(tot, text="TOTAL:  $0.00",
                                   font=("Segoe UI", 13, "bold"),
                                   bg=st.OSCURO_MEDIO, fg=st.DORADO)
        self._lbl_total.pack(anchor=tk.E, padx=12, pady=6)

        # Botones
        btnframe = tk.Frame(f, bg=st.OSCURO)
        btnframe.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(btnframe, text="🗑️  Quitar",
                  command=self._quitar_item,
                  **st.estilo_boton_peligro()).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(btnframe, text="💳  Cobrar",
                  command=self._cobrar,
                  **st.estilo_boton_exito()).pack(side=tk.RIGHT)
        return f

    # ── Carga de datos ────────────────────────────────────────────────────────

    def _cargar_mesas(self):
        self._lista_mesas.delete(0, tk.END)
        conn = db.get_connection()
        mesas = conn.execute("SELECT * FROM mesas ORDER BY numero").fetchall()
        conn.close()
        self._mesas_data = [dict(m) for m in mesas]
        for m in self._mesas_data:
            estado = m["estado"]
            icono  = "🟢" if estado == "libre" else "🔴"
            self._lista_mesas.insert(tk.END, f"{icono} {m['numero']} ({m['ubicacion']})")

    def _cargar_menu(self):
        conn = db.get_connection()
        prods = conn.execute(
            "SELECT * FROM productos WHERE modulo=? AND activo=1 ORDER BY categoria,nombre",
            (self.MODULO,)
        ).fetchall()
        conn.close()
        self._productos_data = [dict(p) for p in prods]
        cats = ["Todas"] + sorted({p["categoria"] for p in self._productos_data})
        self._combo_cat["values"] = cats
        self._combo_cat.set("Todas")
        self._filtrar_menu()

    def _filtrar_menu(self):
        cat = self._combo_cat.get()
        for row in self._tree_menu.get_children():
            self._tree_menu.delete(row)
        simbolo = db.get_config("moneda_simbolo", "$")
        for p in self._productos_data:
            if cat == "Todas" or p["categoria"] == cat:
                self._tree_menu.insert("", tk.END,
                    values=(p["nombre"], f"{simbolo}{p['precio']:.2f}"),
                    tags=(str(p["id"]),))

    # ── Eventos ───────────────────────────────────────────────────────────────

    def _al_seleccionar_mesa(self, _e=None):
        sel = self._lista_mesas.curselection()
        if not sel:
            return
        self._mesa_sel = self._mesas_data[sel[0]]
        info = (f"Mesa {self._mesa_sel['numero']}\n"
                f"Capacidad: {self._mesa_sel['capacidad']}\n"
                f"Ubicación: {self._mesa_sel['ubicacion']}\n"
                f"Estado: {self._mesa_sel['estado']}")
        self._lbl_mesa_info.config(text=info)
        # Inicializar orden vacía
        self._orden_actual = []
        self._orden_id = None
        self._actualizar_orden_ui()

    def _agregar_al_orden(self, _e=None):
        if not self._mesa_sel:
            messagebox.showwarning("Mesa no seleccionada",
                                   "Por favor seleccione una mesa primero.", parent=self)
            return
        sel = self._tree_menu.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Seleccione un producto del menú.", parent=self)
            return
        tag = self._tree_menu.item(sel[0], "tags")
        pid = int(tag[0])
        prod = next((p for p in self._productos_data if p["id"] == pid), None)
        if not prod:
            return
        # Verificar si ya está en la orden
        for item in self._orden_actual:
            if item["producto_id"] == pid:
                item["cantidad"] += 1
                item["subtotal"] = item["cantidad"] * item["precio_unitario"]
                self._actualizar_orden_ui()
                return
        self._orden_actual.append({
            "producto_id":    pid,
            "nombre":         prod["nombre"],
            "cantidad":       1,
            "precio_unitario":prod["precio"],
            "subtotal":       prod["precio"],
            "notas":          "",
        })
        self._actualizar_orden_ui()

    def _quitar_item(self):
        sel = self._tree_orden.selection()
        if not sel:
            return
        idx = self._tree_orden.index(sel[0])
        if 0 <= idx < len(self._orden_actual):
            self._orden_actual.pop(idx)
        self._actualizar_orden_ui()

    def _actualizar_orden_ui(self):
        for row in self._tree_orden.get_children():
            self._tree_orden.delete(row)
        simbolo = db.get_config("moneda_simbolo", "$")
        for item in self._orden_actual:
            self._tree_orden.insert("", tk.END, values=(
                item["cantidad"],
                item["nombre"],
                f"{simbolo}{item['precio_unitario']:.2f}",
                f"{simbolo}{item['subtotal']:.2f}",
            ))
        subtotal = sum(i["subtotal"] for i in self._orden_actual)
        impuesto_pct = float(db.get_config("impuesto_pct", "16")) / 100
        impuesto = subtotal * impuesto_pct
        total    = subtotal + impuesto
        self._lbl_subtotal.config(text=f"Subtotal:  {simbolo}{subtotal:.2f}")
        self._lbl_impuesto.config(text=f"IVA ({int(impuesto_pct*100)}%):  {simbolo}{impuesto:.2f}")
        self._lbl_total.config(   text=f"TOTAL:  {simbolo}{total:.2f}")

    def _cobrar(self):
        if not self._orden_actual:
            messagebox.showwarning("Orden vacía",
                                   "Agregue productos antes de cobrar.", parent=self)
            return
        if not self._mesa_sel:
            messagebox.showwarning("Mesa no seleccionada",
                                   "Seleccione una mesa.", parent=self)
            return

        subtotal = sum(i["subtotal"] for i in self._orden_actual)
        impuesto_pct = float(db.get_config("impuesto_pct", "16")) / 100
        impuesto = subtotal * impuesto_pct
        total    = subtotal + impuesto
        simbolo  = db.get_config("moneda_simbolo", "$")

        metodo = st.dialogo_metodo_pago(self, total, simbolo)
        if not metodo:
            return

        conn = db.get_connection()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO ordenes (modulo, referencia, usuario_id, estado,
                                 subtotal, impuesto, total, metodo_pago)
            VALUES (?,?,?,?,?,?,?,?)
        """, (self.MODULO, f"Mesa {self._mesa_sel['numero']}",
              self.usuario.get("id"), "cerrada",
              subtotal, impuesto, total, metodo))
        orden_id = cur.lastrowid
        for item in self._orden_actual:
            cur.execute("""
                INSERT INTO orden_items (orden_id, producto_id, cantidad,
                                        precio_unitario, subtotal)
                VALUES (?,?,?,?,?)
            """, (orden_id, item["producto_id"], item["cantidad"],
                  item["precio_unitario"], item["subtotal"]))
        conn.commit()
        conn.close()

        messagebox.showinfo("Cobro exitoso",
                            f"Orden #{orden_id} cobrada.\n"
                            f"Mesa: {self._mesa_sel['numero']}\n"
                            f"Total: {simbolo}{total:.2f}\n"
                            f"Método: {metodo}",
                            parent=self)
        self._orden_actual = []
        self._orden_id = None
        self._actualizar_orden_ui()
        self._cargar_mesas()

    # ── Utilitarios ───────────────────────────────────────────────────────────

    @staticmethod
    def _aplicar_estilo_tree(tree: ttk.Treeview):
        st.aplicar_estilo_tree(tree)
