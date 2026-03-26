"""
reportes.py – Módulo de Reportes: ingresos por módulo, rango de fechas y resumen.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

from modules import database as db
from modules import estilos as st


class VentanaReportes(tk.Toplevel):
    """Reportes de ventas, habitaciones y actividad del sistema."""

    def __init__(self, parent, usuario: dict):
        super().__init__(parent)
        self.usuario = usuario
        self.title("Reportes")
        self.configure(bg=st.OSCURO)
        self.geometry("1000x680")
        self._build_ui()
        self._generar_reporte()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        h = tk.Frame(self, bg=st.OSCURO_MEDIO,
                     highlightthickness=1, highlightbackground=st.DORADO)
        h.pack(fill=tk.X)
        tk.Label(h, text="📋  Reportes",
                 font=("Segoe UI", 14, "bold"),
                 bg=st.OSCURO_MEDIO, fg=st.DORADO).pack(side=tk.LEFT, padx=16, pady=10)
        tk.Button(h, text="✕  Cerrar", command=self.destroy,
                  bg=st.OSCURO_MEDIO, fg=st.TEXTO_GRIS,
                  font=("Segoe UI", 9), relief="flat",
                  cursor="hand2").pack(side=tk.RIGHT, padx=12, pady=8)

        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tab_ventas = tk.Frame(nb, bg=st.OSCURO)
        tab_hab    = tk.Frame(nb, bg=st.OSCURO)
        tab_items  = tk.Frame(nb, bg=st.OSCURO)

        nb.add(tab_ventas, text="  Ventas por Módulo  ")
        nb.add(tab_hab,    text="  Ocupación  ")
        nb.add(tab_items,  text="  Top Productos  ")

        self._build_tab_ventas(tab_ventas)
        self._build_tab_habitaciones(tab_hab)
        self._build_tab_items(tab_items)

    # ── Tab ventas ─────────────────────────────────────────────────────────────

    def _build_tab_ventas(self, parent):
        # Filtros
        filtros = tk.Frame(parent, bg=st.OSCURO)
        filtros.pack(fill=tk.X, padx=12, pady=8)

        tk.Label(filtros, text="Desde:", font=("Segoe UI", 10),
                 bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(side=tk.LEFT, padx=(0, 4))
        self._entry_desde = tk.Entry(filtros, **st.estilo_entry(), width=12)
        self._entry_desde.configure(bg=st.OSCURO_CLARO)
        hoy = date.today()
        primer_mes = hoy.replace(day=1).isoformat()
        self._entry_desde.insert(0, primer_mes)
        self._entry_desde.pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(filtros, text="Hasta:", font=("Segoe UI", 10),
                 bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(side=tk.LEFT, padx=(0, 4))
        self._entry_hasta = tk.Entry(filtros, **st.estilo_entry(), width=12)
        self._entry_hasta.configure(bg=st.OSCURO_CLARO)
        self._entry_hasta.insert(0, hoy.isoformat())
        self._entry_hasta.pack(side=tk.LEFT, padx=(0, 12))

        tk.Button(filtros, text="🔍 Generar",
                  command=self._generar_reporte,
                  **st.estilo_boton_secundario()).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(filtros, text="Hoy",
                  command=self._filtro_hoy,
                  bg=st.OSCURO_CLARO, fg=st.TEXTO_GRIS,
                  font=("Segoe UI", 9), relief="flat",
                  cursor="hand2", padx=8, pady=4).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(filtros, text="Este mes",
                  command=self._filtro_mes,
                  bg=st.OSCURO_CLARO, fg=st.TEXTO_GRIS,
                  font=("Segoe UI", 9), relief="flat",
                  cursor="hand2", padx=8, pady=4).pack(side=tk.LEFT)

        # Tarjetas resumen
        self._frame_resumen = tk.Frame(parent, bg=st.OSCURO)
        self._frame_resumen.pack(fill=tk.X, padx=12, pady=4)

        # Tabla de ventas por módulo
        cols = ("modulo", "ordenes", "subtotal", "impuesto", "total")
        self._tree_ventas = ttk.Treeview(parent, columns=cols, show="headings",
                                         selectmode="none")
        self._tree_ventas.heading("modulo",   text="Módulo")
        self._tree_ventas.heading("ordenes",  text="Órdenes")
        self._tree_ventas.heading("subtotal", text="Subtotal")
        self._tree_ventas.heading("impuesto", text="IVA")
        self._tree_ventas.heading("total",    text="Total")
        self._tree_ventas.column("modulo",   width=150)
        self._tree_ventas.column("ordenes",  width=70,  anchor=tk.CENTER)
        self._tree_ventas.column("subtotal", width=120, anchor=tk.E)
        self._tree_ventas.column("impuesto", width=110, anchor=tk.E)
        self._tree_ventas.column("total",    width=120, anchor=tk.E)
        _aplicar_estilo_tree(self._tree_ventas)

        sb = tk.Scrollbar(parent, command=self._tree_ventas.yview,
                          bg=st.OSCURO_MEDIO, troughcolor=st.OSCURO)
        self._tree_ventas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12))
        self._tree_ventas.pack(fill=tk.BOTH, expand=True,
                               padx=(12, 0), pady=(0, 8))

        # Fila total
        self._lbl_gran_total = tk.Label(parent, text="",
                                        font=("Segoe UI", 12, "bold"),
                                        bg=st.OSCURO, fg=st.DORADO)
        self._lbl_gran_total.pack(anchor=tk.E, padx=20, pady=4)

    # ── Tab habitaciones ──────────────────────────────────────────────────────

    def _build_tab_habitaciones(self, parent):
        cols = ("numero", "tipo", "cliente", "entrada", "salida", "total", "estado")
        self._tree_hab = ttk.Treeview(parent, columns=cols, show="headings",
                                      selectmode="none")
        self._tree_hab.heading("numero",  text="Hab.")
        self._tree_hab.heading("tipo",    text="Tipo")
        self._tree_hab.heading("cliente", text="Cliente")
        self._tree_hab.heading("entrada", text="Entrada")
        self._tree_hab.heading("salida",  text="Salida")
        self._tree_hab.heading("total",   text="Total")
        self._tree_hab.heading("estado",  text="Estado")
        self._tree_hab.column("numero",  width=55,  anchor=tk.CENTER)
        self._tree_hab.column("tipo",    width=120)
        self._tree_hab.column("cliente", width=160)
        self._tree_hab.column("entrada", width=90,  anchor=tk.CENTER)
        self._tree_hab.column("salida",  width=90,  anchor=tk.CENTER)
        self._tree_hab.column("total",   width=100, anchor=tk.E)
        self._tree_hab.column("estado",  width=90,  anchor=tk.CENTER)
        _aplicar_estilo_tree(self._tree_hab)

        sb = tk.Scrollbar(parent, command=self._tree_hab.yview,
                          bg=st.OSCURO_MEDIO, troughcolor=st.OSCURO)
        self._tree_hab.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12))
        self._tree_hab.pack(fill=tk.BOTH, expand=True, padx=(12, 0), pady=12)

        self._lbl_hab_resumen = tk.Label(parent, text="",
                                         font=("Segoe UI", 10),
                                         bg=st.OSCURO, fg=st.TEXTO_GRIS)
        self._lbl_hab_resumen.pack(anchor=tk.W, padx=14, pady=4)

    # ── Tab top productos ─────────────────────────────────────────────────────

    def _build_tab_items(self, parent):
        top = tk.Frame(parent, bg=st.OSCURO)
        top.pack(fill=tk.X, padx=12, pady=8)
        tk.Label(top, text="Módulo:", font=("Segoe UI", 10),
                 bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(side=tk.LEFT, padx=(0, 4))
        self._combo_modulo_items = ttk.Combobox(
            top, values=["Todos", "restaurante", "bar", "spa"],
            state="readonly", width=14, font=("Segoe UI", 10))
        self._combo_modulo_items.set("Todos")
        self._combo_modulo_items.pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(top, text="🔍 Consultar",
                  command=self._cargar_top_items,
                  **st.estilo_boton_secundario()).pack(side=tk.LEFT)

        cols = ("pos", "producto", "modulo", "cantidad", "total")
        self._tree_items = ttk.Treeview(parent, columns=cols, show="headings",
                                        selectmode="none")
        self._tree_items.heading("pos",      text="#")
        self._tree_items.heading("producto", text="Producto")
        self._tree_items.heading("modulo",   text="Módulo")
        self._tree_items.heading("cantidad", text="Vendidos")
        self._tree_items.heading("total",    text="Total")
        self._tree_items.column("pos",      width=35,  anchor=tk.CENTER)
        self._tree_items.column("producto", width=230)
        self._tree_items.column("modulo",   width=100, anchor=tk.CENTER)
        self._tree_items.column("cantidad", width=80,  anchor=tk.CENTER)
        self._tree_items.column("total",    width=120, anchor=tk.E)
        _aplicar_estilo_tree(self._tree_items)

        sb = tk.Scrollbar(parent, command=self._tree_items.yview,
                          bg=st.OSCURO_MEDIO, troughcolor=st.OSCURO)
        self._tree_items.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12))
        self._tree_items.pack(fill=tk.BOTH, expand=True, padx=(12, 0), pady=(0, 8))
        self._cargar_top_items()

    # ── Generación de datos ───────────────────────────────────────────────────

    def _generar_reporte(self):
        desde = self._entry_desde.get().strip()
        hasta = self._entry_hasta.get().strip()
        simbolo = db.get_config("moneda_simbolo", "$")

        conn = db.get_connection()
        rows = conn.execute("""
            SELECT modulo,
                   COUNT(*) as ordenes,
                   SUM(subtotal) as subtotal,
                   SUM(impuesto) as impuesto,
                   SUM(total) as total
            FROM ordenes
            WHERE estado='cerrada'
              AND date(fecha) BETWEEN ? AND ?
            GROUP BY modulo
            ORDER BY total DESC
        """, (desde, hasta)).fetchall()
        conn.close()

        for row in self._tree_ventas.get_children():
            self._tree_ventas.delete(row)
        for w in self._frame_resumen.winfo_children():
            w.destroy()

        gran_total = 0.0
        modulos_iconos = {
            "restaurante": "🍽️", "bar": "🍸", "spa": "💆",
            "habitaciones": "🛏️",
        }
        for r in rows:
            mod  = r["modulo"]
            icon = modulos_iconos.get(mod, "📦")
            self._tree_ventas.insert("", tk.END, values=(
                f"{icon} {mod.capitalize()}",
                r["ordenes"],
                f"{simbolo}{r['subtotal']:.2f}",
                f"{simbolo}{r['impuesto']:.2f}",
                f"{simbolo}{r['total']:.2f}",
            ))
            gran_total += r["total"] or 0

            # Tarjeta
            card = tk.Frame(self._frame_resumen, bg=st.OSCURO_MEDIO,
                            highlightthickness=1, highlightbackground=st.DORADO,
                            padx=14, pady=8)
            card.pack(side=tk.LEFT, padx=(0, 10), pady=4)
            tk.Label(card, text=f"{icon} {mod.capitalize()}",
                     font=("Segoe UI", 9), bg=st.OSCURO_MEDIO,
                     fg=st.TEXTO_GRIS).pack()
            tk.Label(card, text=f"{simbolo}{(r['total'] or 0):.2f}",
                     font=("Segoe UI", 13, "bold"),
                     bg=st.OSCURO_MEDIO, fg=st.DORADO).pack()

        self._lbl_gran_total.config(
            text=f"GRAN TOTAL ({desde} → {hasta}):  {simbolo}{gran_total:.2f}")

        self._cargar_reporte_habitaciones(desde, hasta, simbolo)

    def _cargar_reporte_habitaciones(self, desde: str, hasta: str, simbolo: str):
        for row in self._tree_hab.get_children():
            self._tree_hab.delete(row)
        conn = db.get_connection()
        rows = conn.execute("""
            SELECT r.*, h.numero as num_hab, h.tipo
            FROM reservaciones r
            JOIN habitaciones h ON h.id = r.habitacion_id
            WHERE date(r.fecha_entrada) BETWEEN ? AND ?
            ORDER BY r.fecha_entrada
        """, (desde, hasta)).fetchall()
        conn.close()
        total_ingresos = 0.0
        for r in rows:
            self._tree_hab.insert("", tk.END, values=(
                r["num_hab"], r["tipo"], r["cliente_nombre"],
                r["fecha_entrada"], r["fecha_salida"],
                f"{simbolo}{r['precio_total']:.2f}",
                r["estado"].upper(),
            ))
            total_ingresos += r["precio_total"] or 0
        self._lbl_hab_resumen.config(
            text=f"Total reservaciones: {len(rows)}  |  "
                 f"Ingresos: {simbolo}{total_ingresos:.2f}")

    def _cargar_top_items(self):
        for row in self._tree_items.get_children():
            self._tree_items.delete(row)
        mod = self._combo_modulo_items.get()
        simbolo = db.get_config("moneda_simbolo", "$")
        conn = db.get_connection()
        if mod == "Todos":
            rows = conn.execute("""
                SELECT p.nombre, p.modulo,
                       SUM(oi.cantidad) as cantidad,
                       SUM(oi.subtotal) as total
                FROM orden_items oi
                JOIN productos p ON p.id = oi.producto_id
                GROUP BY p.id
                ORDER BY cantidad DESC
                LIMIT 20
            """).fetchall()
        else:
            rows = conn.execute("""
                SELECT p.nombre, p.modulo,
                       SUM(oi.cantidad) as cantidad,
                       SUM(oi.subtotal) as total
                FROM orden_items oi
                JOIN productos p ON p.id = oi.producto_id
                WHERE p.modulo = ?
                GROUP BY p.id
                ORDER BY cantidad DESC
                LIMIT 20
            """, (mod,)).fetchall()
        conn.close()
        for i, r in enumerate(rows, 1):
            self._tree_items.insert("", tk.END, values=(
                i, r["nombre"], r["modulo"].capitalize(),
                r["cantidad"] or 0,
                f"{simbolo}{(r['total'] or 0):.2f}",
            ))

    def _filtro_hoy(self):
        hoy = date.today().isoformat()
        self._entry_desde.delete(0, tk.END)
        self._entry_desde.insert(0, hoy)
        self._entry_hasta.delete(0, tk.END)
        self._entry_hasta.insert(0, hoy)
        self._generar_reporte()

    def _filtro_mes(self):
        hoy = date.today()
        self._entry_desde.delete(0, tk.END)
        self._entry_desde.insert(0, hoy.replace(day=1).isoformat())
        self._entry_hasta.delete(0, tk.END)
        self._entry_hasta.insert(0, hoy.isoformat())
        self._generar_reporte()


def _aplicar_estilo_tree(tree: ttk.Treeview):
    st.aplicar_estilo_tree(tree)
