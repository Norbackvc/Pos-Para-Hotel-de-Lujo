"""
bar.py – Módulo de Bar: menú de bebidas y cócteles, órdenes y cobro.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from modules import database as db
from modules import estilos as st


class VentanaBar(tk.Toplevel):
    """Gestión del bar: menú, órdenes rápidas y cobro."""

    MODULO = "bar"

    def __init__(self, parent, usuario: dict):
        super().__init__(parent)
        self.usuario = usuario
        self.title("Bar")
        self.configure(bg=st.OSCURO)
        self.geometry("900x660")
        self._orden: list[dict] = []
        self._build_ui()
        self._cargar_menu()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        h = tk.Frame(self, bg=st.OSCURO_MEDIO,
                     highlightthickness=1, highlightbackground=st.DORADO)
        h.pack(fill=tk.X)
        tk.Label(h, text="🍸  Bar",
                 font=("Segoe UI", 14, "bold"),
                 bg=st.OSCURO_MEDIO, fg=st.DORADO).pack(side=tk.LEFT, padx=16, pady=10)
        tk.Button(h, text="✕  Cerrar", command=self.destroy,
                  bg=st.OSCURO_MEDIO, fg=st.TEXTO_GRIS,
                  font=("Segoe UI", 9), relief="flat",
                  cursor="hand2").pack(side=tk.RIGHT, padx=12, pady=8)

        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                               bg=st.OSCURO, sashwidth=6)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        paned.add(self._panel_menu(paned),  minsize=320)
        paned.add(self._panel_orden(paned), minsize=260)

    def _panel_menu(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=st.OSCURO)

        top = tk.Frame(f, bg=st.OSCURO)
        top.pack(fill=tk.X, padx=8, pady=(8, 4))
        tk.Label(top, text="MENÚ DE BAR", font=("Segoe UI", 10, "bold"),
                 bg=st.OSCURO, fg=st.DORADO).pack(side=tk.LEFT)

        self._combo_cat = ttk.Combobox(top, state="readonly", width=16,
                                       font=("Segoe UI", 10))
        self._combo_cat.pack(side=tk.RIGHT)
        self._combo_cat.bind("<<ComboboxSelected>>", lambda _: self._filtrar())

        # Grid de productos como botones
        self._frame_grid = tk.Frame(f, bg=st.OSCURO)
        self._frame_grid.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        return f

    def _panel_orden(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=st.OSCURO)
        tk.Label(f, text="ORDEN", font=("Segoe UI", 10, "bold"),
                 bg=st.OSCURO, fg=st.DORADO).pack(anchor=tk.W, padx=8, pady=(8, 4))

        # Mesa / cliente
        ref_frame = tk.Frame(f, bg=st.OSCURO)
        ref_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        tk.Label(ref_frame, text="Mesa/Referencia:", font=("Segoe UI", 9),
                 bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(side=tk.LEFT)
        self._entry_ref = tk.Entry(ref_frame, **st.estilo_entry(), width=14)
        self._entry_ref.configure(bg=st.OSCURO_CLARO)
        self._entry_ref.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))

        cols = ("cant", "producto", "subtotal")
        self._tree_orden = ttk.Treeview(f, columns=cols, show="headings",
                                        selectmode="browse", height=16)
        self._tree_orden.heading("cant",     text="Cant")
        self._tree_orden.heading("producto", text="Producto")
        self._tree_orden.heading("subtotal", text="Subtotal")
        self._tree_orden.column("cant",     width=40,  anchor=tk.CENTER)
        self._tree_orden.column("producto", width=150)
        self._tree_orden.column("subtotal", width=80,  anchor=tk.E)
        _aplicar_estilo_tree(self._tree_orden)

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
                                      font=("Segoe UI", 10),
                                      bg=st.OSCURO_MEDIO, fg=st.TEXTO_CLARO)
        self._lbl_subtotal.pack(anchor=tk.E, padx=12, pady=2)
        self._lbl_impuesto = tk.Label(tot, text="IVA:  $0.00",
                                      font=("Segoe UI", 10),
                                      bg=st.OSCURO_MEDIO, fg=st.TEXTO_CLARO)
        self._lbl_impuesto.pack(anchor=tk.E, padx=12, pady=2)
        self._lbl_total = tk.Label(tot, text="TOTAL:  $0.00",
                                   font=("Segoe UI", 13, "bold"),
                                   bg=st.OSCURO_MEDIO, fg=st.DORADO)
        self._lbl_total.pack(anchor=tk.E, padx=12, pady=6)

        bf = tk.Frame(f, bg=st.OSCURO)
        bf.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(bf, text="🗑️  Quitar",
                  command=self._quitar,
                  **st.estilo_boton_peligro()).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(bf, text="💳  Cobrar",
                  command=self._cobrar,
                  **st.estilo_boton_exito()).pack(side=tk.RIGHT)
        return f

    # ── Datos ─────────────────────────────────────────────────────────────────

    def _cargar_menu(self):
        conn = db.get_connection()
        prods = conn.execute(
            "SELECT * FROM productos WHERE modulo=? AND activo=1 ORDER BY categoria,nombre",
            (self.MODULO,)
        ).fetchall()
        conn.close()
        self._productos = [dict(p) for p in prods]
        cats = ["Todas"] + sorted({p["categoria"] for p in self._productos})
        self._combo_cat["values"] = cats
        self._combo_cat.set("Todas")
        self._filtrar()

    def _filtrar(self):
        cat = self._combo_cat.get()
        for w in self._frame_grid.winfo_children():
            w.destroy()
        prods = [p for p in self._productos
                 if cat == "Todas" or p["categoria"] == cat]
        simbolo = db.get_config("moneda_simbolo", "$")
        cols = 3
        for i, p in enumerate(prods):
            fila = i // cols
            col  = i % cols
            btn = tk.Button(
                self._frame_grid,
                text=f"{p['nombre']}\n{simbolo}{p['precio']:.2f}",
                command=lambda pr=p: self._agregar(pr),
                bg=st.OSCURO_CLARO, fg=st.TEXTO_CLARO,
                font=("Segoe UI", 9), relief="flat",
                cursor="hand2", padx=6, pady=10,
                wraplength=110,
                activebackground=st.DORADO,
                activeforeground=st.OSCURO,
            )
            btn.grid(row=fila, column=col, padx=4, pady=4, sticky="nsew")
            self._frame_grid.columnconfigure(col, weight=1)

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _agregar(self, prod: dict):
        for item in self._orden:
            if item["producto_id"] == prod["id"]:
                item["cantidad"] += 1
                item["subtotal"]  = item["cantidad"] * item["precio_unitario"]
                self._actualizar_ui()
                return
        self._orden.append({
            "producto_id":    prod["id"],
            "nombre":         prod["nombre"],
            "cantidad":       1,
            "precio_unitario":prod["precio"],
            "subtotal":       prod["precio"],
        })
        self._actualizar_ui()

    def _quitar(self):
        sel = self._tree_orden.selection()
        if not sel:
            return
        idx = self._tree_orden.index(sel[0])
        if 0 <= idx < len(self._orden):
            item = self._orden[idx]
            if item["cantidad"] > 1:
                item["cantidad"] -= 1
                item["subtotal"]  = item["cantidad"] * item["precio_unitario"]
            else:
                self._orden.pop(idx)
        self._actualizar_ui()

    def _actualizar_ui(self):
        for row in self._tree_orden.get_children():
            self._tree_orden.delete(row)
        simbolo = db.get_config("moneda_simbolo", "$")
        for item in self._orden:
            self._tree_orden.insert("", tk.END, values=(
                item["cantidad"], item["nombre"],
                f"{simbolo}{item['subtotal']:.2f}",
            ))
        subtotal = sum(i["subtotal"] for i in self._orden)
        pct = float(db.get_config("impuesto_pct", "16")) / 100
        impuesto = subtotal * pct
        total    = subtotal + impuesto
        self._lbl_subtotal.config(text=f"Subtotal:  {simbolo}{subtotal:.2f}")
        self._lbl_impuesto.config(text=f"IVA ({int(pct*100)}%):  {simbolo}{impuesto:.2f}")
        self._lbl_total.config(   text=f"TOTAL:  {simbolo}{total:.2f}")

    def _cobrar(self):
        if not self._orden:
            messagebox.showwarning("Orden vacía",
                                   "Agregue productos antes de cobrar.", parent=self)
            return
        subtotal = sum(i["subtotal"] for i in self._orden)
        pct      = float(db.get_config("impuesto_pct", "16")) / 100
        impuesto = subtotal * pct
        total    = subtotal + impuesto
        simbolo  = db.get_config("moneda_simbolo", "$")
        ref      = self._entry_ref.get().strip() or "Bar"

        metodo = st.dialogo_metodo_pago(self, total, simbolo)
        if not metodo:
            return

        conn = db.get_connection()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO ordenes (modulo, referencia, usuario_id, estado,
                                 subtotal, impuesto, total, metodo_pago)
            VALUES (?,?,?,?,?,?,?,?)
        """, (self.MODULO, ref, self.usuario.get("id"), "cerrada",
              subtotal, impuesto, total, metodo))
        orden_id = cur.lastrowid
        for item in self._orden:
            cur.execute("""
                INSERT INTO orden_items (orden_id, producto_id, cantidad,
                                        precio_unitario, subtotal)
                VALUES (?,?,?,?,?)
            """, (orden_id, item["producto_id"], item["cantidad"],
                  item["precio_unitario"], item["subtotal"]))
        conn.commit()
        conn.close()

        messagebox.showinfo("Cobro exitoso",
                            f"Orden #{orden_id} cobrada.\nTotal: {simbolo}{total:.2f}",
                            parent=self)
        self._orden.clear()
        self._entry_ref.delete(0, tk.END)
        self._actualizar_ui()


def _aplicar_estilo_tree(tree: ttk.Treeview):
    st.aplicar_estilo_tree(tree)
