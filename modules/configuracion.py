"""
configuracion.py – Módulo de Configuración: parámetros del sistema y gestión de usuarios.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from modules import database as db
from modules import estilos as st


class VentanaConfiguracion(tk.Toplevel):
    """Configuración del sistema: datos del hotel, impuestos y usuarios."""

    def __init__(self, parent, usuario: dict):
        super().__init__(parent)
        self.usuario = usuario
        self.title("Configuración")
        self.configure(bg=st.OSCURO)
        self.geometry("820x620")
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        h = tk.Frame(self, bg=st.OSCURO_MEDIO,
                     highlightthickness=1, highlightbackground=st.DORADO)
        h.pack(fill=tk.X)
        tk.Label(h, text="⚙️  Configuración",
                 font=("Segoe UI", 14, "bold"),
                 bg=st.OSCURO_MEDIO, fg=st.DORADO).pack(side=tk.LEFT, padx=16, pady=10)
        tk.Button(h, text="✕  Cerrar", command=self.destroy,
                  bg=st.OSCURO_MEDIO, fg=st.TEXTO_GRIS,
                  font=("Segoe UI", 9), relief="flat",
                  cursor="hand2").pack(side=tk.RIGHT, padx=12, pady=8)

        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tab_hotel   = tk.Frame(nb, bg=st.OSCURO)
        tab_usuarios= tk.Frame(nb, bg=st.OSCURO)
        tab_productos= tk.Frame(nb, bg=st.OSCURO)

        nb.add(tab_hotel,    text="  Hotel  ")
        nb.add(tab_usuarios, text="  Usuarios  ")
        nb.add(tab_productos,text="  Productos  ")

        self._build_tab_hotel(tab_hotel)
        self._build_tab_usuarios(tab_usuarios)
        self._build_tab_productos(tab_productos)

    # ── Tab Hotel ─────────────────────────────────────────────────────────────

    def _build_tab_hotel(self, parent):
        f = tk.Frame(parent, bg=st.OSCURO, padx=30, pady=20)
        f.pack(fill=tk.BOTH, expand=True)

        tk.Label(f, text="DATOS DEL HOTEL", font=("Segoe UI", 12, "bold"),
                 bg=st.OSCURO, fg=st.DORADO).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 16))

        campos_config = [
            ("Nombre del Hotel:",  "hotel_nombre"),
            ("Slogan / Subtítulo:", "hotel_slogan"),
            ("IVA / Impuesto (%):", "impuesto_pct"),
            ("Símbolo de moneda:",  "moneda_simbolo"),
        ]
        self._entries_config: dict[str, tk.Entry] = {}
        for i, (lbl, clave) in enumerate(campos_config, start=1):
            tk.Label(f, text=lbl, font=("Segoe UI", 10),
                     bg=st.OSCURO, fg=st.TEXTO_GRIS).grid(
                row=i, column=0, sticky=tk.W, pady=6, padx=(0, 16))
            e = tk.Entry(f, **st.estilo_entry(), width=32)
            e.configure(bg=st.OSCURO_CLARO)
            e.insert(0, db.get_config(clave, ""))
            e.grid(row=i, column=1, sticky=tk.EW, pady=6)
            self._entries_config[clave] = e
            f.columnconfigure(1, weight=1)

        self._lbl_msg_config = tk.Label(f, text="",
                                        font=("Segoe UI", 9),
                                        bg=st.OSCURO, fg=st.EXITO)
        self._lbl_msg_config.grid(row=len(campos_config)+1, column=0,
                                   columnspan=2, pady=(8, 0))

        tk.Button(f, text="💾  Guardar Configuración",
                  command=self._guardar_config,
                  **st.estilo_boton_primario()).grid(
            row=len(campos_config)+2, column=0, columnspan=2,
            sticky=tk.W, pady=(8, 0))

    # ── Tab Usuarios ──────────────────────────────────────────────────────────

    def _build_tab_usuarios(self, parent):
        # Solo admin puede gestionar usuarios
        es_admin = self.usuario.get("rol") == "admin"

        cols = ("usuario", "nombre", "rol", "activo")
        self._tree_usr = ttk.Treeview(parent, columns=cols, show="headings",
                                      selectmode="browse")
        self._tree_usr.heading("usuario", text="Usuario")
        self._tree_usr.heading("nombre",  text="Nombre")
        self._tree_usr.heading("rol",     text="Rol")
        self._tree_usr.heading("activo",  text="Activo")
        self._tree_usr.column("usuario", width=120)
        self._tree_usr.column("nombre",  width=160)
        self._tree_usr.column("rol",     width=100, anchor=tk.CENTER)
        self._tree_usr.column("activo",  width=70,  anchor=tk.CENTER)
        _aplicar_estilo_tree(self._tree_usr)

        sb = tk.Scrollbar(parent, command=self._tree_usr.yview,
                          bg=st.OSCURO_MEDIO, troughcolor=st.OSCURO)
        self._tree_usr.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12))
        self._tree_usr.pack(fill=tk.BOTH, expand=True, padx=(12, 0), pady=(8, 4))

        if es_admin:
            bf = tk.Frame(parent, bg=st.OSCURO)
            bf.pack(fill=tk.X, padx=12, pady=4)
            tk.Button(bf, text="➕ Nuevo Usuario",
                      command=self._nuevo_usuario,
                      **st.estilo_boton_exito()).pack(side=tk.LEFT, padx=(0, 6))
            tk.Button(bf, text="🔑 Cambiar Contraseña",
                      command=self._cambiar_contrasena,
                      **st.estilo_boton_secundario()).pack(side=tk.LEFT, padx=(0, 6))
            tk.Button(bf, text="🚫 Deshabilitar",
                      command=self._toggle_usuario,
                      **st.estilo_boton_peligro()).pack(side=tk.LEFT)
        else:
            tk.Label(parent,
                     text="Solo el administrador puede gestionar usuarios.",
                     font=("Segoe UI", 10), bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(
                pady=8, padx=12, anchor=tk.W)

        self._cargar_usuarios()

    # ── Tab Productos ─────────────────────────────────────────────────────────

    def _build_tab_productos(self, parent):
        top = tk.Frame(parent, bg=st.OSCURO)
        top.pack(fill=tk.X, padx=12, pady=(8, 4))
        tk.Label(top, text="Módulo:", font=("Segoe UI", 10),
                 bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(side=tk.LEFT, padx=(0, 4))
        self._combo_mod_prod = ttk.Combobox(
            top, values=["Todos", "restaurante", "bar", "spa"],
            state="readonly", width=14, font=("Segoe UI", 10))
        self._combo_mod_prod.set("Todos")
        self._combo_mod_prod.pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(top, text="🔍 Filtrar",
                  command=self._cargar_productos,
                  **st.estilo_boton_secundario()).pack(side=tk.LEFT, padx=(0, 6))

        cols = ("nombre", "categoria", "modulo", "precio", "activo")
        self._tree_prod = ttk.Treeview(parent, columns=cols, show="headings",
                                       selectmode="browse")
        self._tree_prod.heading("nombre",    text="Nombre")
        self._tree_prod.heading("categoria", text="Categoría")
        self._tree_prod.heading("modulo",    text="Módulo")
        self._tree_prod.heading("precio",    text="Precio")
        self._tree_prod.heading("activo",    text="Activo")
        self._tree_prod.column("nombre",    width=200)
        self._tree_prod.column("categoria", width=120)
        self._tree_prod.column("modulo",    width=100, anchor=tk.CENTER)
        self._tree_prod.column("precio",    width=100, anchor=tk.E)
        self._tree_prod.column("activo",    width=55,  anchor=tk.CENTER)
        _aplicar_estilo_tree(self._tree_prod)

        sb = tk.Scrollbar(parent, command=self._tree_prod.yview,
                          bg=st.OSCURO_MEDIO, troughcolor=st.OSCURO)
        self._tree_prod.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12))
        self._tree_prod.pack(fill=tk.BOTH, expand=True, padx=(12, 0), pady=(0, 4))

        bf = tk.Frame(parent, bg=st.OSCURO)
        bf.pack(fill=tk.X, padx=12, pady=4)
        tk.Button(bf, text="➕ Nuevo Producto",
                  command=self._nuevo_producto,
                  **st.estilo_boton_exito()).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(bf, text="✏️ Editar Precio",
                  command=self._editar_precio,
                  **st.estilo_boton_secundario()).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(bf, text="🚫 Activar/Desactivar",
                  command=self._toggle_producto,
                  **st.estilo_boton_peligro()).pack(side=tk.LEFT)

        self._cargar_productos()

    # ── Datos ─────────────────────────────────────────────────────────────────

    def _guardar_config(self):
        for clave, entry in self._entries_config.items():
            db.set_config(clave, entry.get().strip())
        self._lbl_msg_config.config(
            text="✅ Configuración guardada correctamente.")

    def _cargar_usuarios(self):
        for row in self._tree_usr.get_children():
            self._tree_usr.delete(row)
        conn = db.get_connection()
        usuarios = conn.execute(
            "SELECT * FROM usuarios ORDER BY rol, usuario"
        ).fetchall()
        conn.close()
        self._usuarios_data = [dict(u) for u in usuarios]
        for u in self._usuarios_data:
            self._tree_usr.insert("", tk.END, values=(
                u["usuario"], u["nombre"], u["rol"],
                "Sí" if u["activo"] else "No",
            ))

    def _nuevo_usuario(self):
        dlg = _DialogoUsuario(self)
        self.wait_window(dlg)
        if dlg.resultado:
            u, n, r, p = dlg.resultado
            conn = db.get_connection()
            try:
                conn.execute(
                    "INSERT INTO usuarios (usuario, contrasena_hash, nombre, rol) "
                    "VALUES (?,?,?,?)",
                    (u, db.hash_password(p), n, r))
                conn.commit()
                self._cargar_usuarios()
            except Exception as exc:
                messagebox.showerror("Error", str(exc), parent=self)
            finally:
                conn.close()

    def _cambiar_contrasena(self):
        sel = self._tree_usr.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Seleccione un usuario.", parent=self)
            return
        idx = self._tree_usr.index(sel[0])
        usr = self._usuarios_data[idx]
        nueva = _pedir_texto(self, "Nueva contraseña",
                             f"Ingrese nueva contraseña para '{usr['usuario']}':",
                             oculto=True)
        if not nueva:
            return
        conn = db.get_connection()
        conn.execute("UPDATE usuarios SET contrasena_hash=? WHERE id=?",
                     (db.hash_password(nueva), usr["id"]))
        conn.commit()
        conn.close()
        messagebox.showinfo("Listo", "Contraseña actualizada.", parent=self)

    def _toggle_usuario(self):
        sel = self._tree_usr.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Seleccione un usuario.", parent=self)
            return
        idx = self._tree_usr.index(sel[0])
        usr = self._usuarios_data[idx]
        nuevo = 0 if usr["activo"] else 1
        conn = db.get_connection()
        conn.execute("UPDATE usuarios SET activo=? WHERE id=?",
                     (nuevo, usr["id"]))
        conn.commit()
        conn.close()
        self._cargar_usuarios()

    def _cargar_productos(self):
        for row in self._tree_prod.get_children():
            self._tree_prod.delete(row)
        mod = self._combo_mod_prod.get()
        conn = db.get_connection()
        if mod == "Todos":
            prods = conn.execute(
                "SELECT * FROM productos ORDER BY modulo, categoria, nombre"
            ).fetchall()
        else:
            prods = conn.execute(
                "SELECT * FROM productos WHERE modulo=? ORDER BY categoria, nombre",
                (mod,)
            ).fetchall()
        conn.close()
        self._productos_data = [dict(p) for p in prods]
        simbolo = db.get_config("moneda_simbolo", "$")
        for p in self._productos_data:
            self._tree_prod.insert("", tk.END, values=(
                p["nombre"], p["categoria"], p["modulo"],
                f"{simbolo}{p['precio']:.2f}",
                "Sí" if p["activo"] else "No",
            ))

    def _nuevo_producto(self):
        dlg = _DialogoProducto(self)
        self.wait_window(dlg)
        if dlg.resultado:
            nombre, cat, mod, precio, desc = dlg.resultado
            conn = db.get_connection()
            conn.execute(
                "INSERT INTO productos (nombre, categoria, modulo, precio, descripcion)"
                " VALUES (?,?,?,?,?)",
                (nombre, cat, mod, precio, desc))
            conn.commit()
            conn.close()
            self._cargar_productos()

    def _editar_precio(self):
        sel = self._tree_prod.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Seleccione un producto.", parent=self)
            return
        idx = self._tree_prod.index(sel[0])
        prod = self._productos_data[idx]
        nuevo = _pedir_texto(self, "Nuevo precio",
                             f"Precio actual: {prod['precio']}\n"
                             f"Ingrese nuevo precio para '{prod['nombre']}':")
        if not nuevo:
            return
        try:
            precio = float(nuevo)
        except ValueError:
            messagebox.showerror("Error", "Precio inválido.", parent=self)
            return
        conn = db.get_connection()
        conn.execute("UPDATE productos SET precio=? WHERE id=?",
                     (precio, prod["id"]))
        conn.commit()
        conn.close()
        self._cargar_productos()

    def _toggle_producto(self):
        sel = self._tree_prod.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Seleccione un producto.", parent=self)
            return
        idx  = self._tree_prod.index(sel[0])
        prod = self._productos_data[idx]
        nuevo = 0 if prod["activo"] else 1
        conn = db.get_connection()
        conn.execute("UPDATE productos SET activo=? WHERE id=?",
                     (nuevo, prod["id"]))
        conn.commit()
        conn.close()
        self._cargar_productos()


# ── Diálogos auxiliares ───────────────────────────────────────────────────────

class _DialogoUsuario(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Nuevo Usuario")
        self.configure(bg=st.OSCURO)
        self.resizable(False, False)
        self.grab_set()
        self.geometry(f"340x300+{parent.winfo_rootx()+60}+{parent.winfo_rooty()+60}")
        self.resultado = None
        self._build()

    def _build(self):
        f = tk.Frame(self, bg=st.OSCURO, padx=20, pady=20)
        f.pack(fill=tk.BOTH, expand=True)
        tk.Label(f, text="Nuevo Usuario", font=("Segoe UI", 12, "bold"),
                 bg=st.OSCURO, fg=st.DORADO).pack(anchor=tk.W, pady=(0, 12))
        self._entries: dict[str, tk.Entry] = {}
        for lbl, key, oculto in [
            ("Usuario:", "usuario", False),
            ("Nombre:",  "nombre",  False),
            ("Contraseña:", "contra", True),
        ]:
            tk.Label(f, text=lbl, font=("Segoe UI", 10),
                     bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(anchor=tk.W)
            e = tk.Entry(f, show="•" if oculto else "",
                         **st.estilo_entry(), width=28)
            e.configure(bg=st.OSCURO_CLARO)
            e.pack(fill=tk.X, pady=(2, 8))
            self._entries[key] = e

        tk.Label(f, text="Rol:", font=("Segoe UI", 10),
                 bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(anchor=tk.W)
        self._combo_rol = ttk.Combobox(
            f, values=["admin", "cajero", "mesero"],
            state="readonly", width=14, font=("Segoe UI", 10))
        self._combo_rol.set("cajero")
        self._combo_rol.pack(anchor=tk.W, pady=(2, 12))

        tk.Button(f, text="Guardar", command=self._guardar,
                  **st.estilo_boton_exito()).pack(anchor=tk.W)

    def _guardar(self):
        u = self._entries["usuario"].get().strip()
        n = self._entries["nombre"].get().strip()
        p = self._entries["contra"].get()
        r = self._combo_rol.get()
        if not u or not n or not p:
            messagebox.showwarning("Datos incompletos",
                                   "Complete todos los campos.", parent=self)
            return
        self.resultado = (u, n, r, p)
        self.destroy()


class _DialogoProducto(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Nuevo Producto")
        self.configure(bg=st.OSCURO)
        self.resizable(False, False)
        self.grab_set()
        self.geometry(f"360x340+{parent.winfo_rootx()+60}+{parent.winfo_rooty()+60}")
        self.resultado = None
        self._build()

    def _build(self):
        f = tk.Frame(self, bg=st.OSCURO, padx=20, pady=20)
        f.pack(fill=tk.BOTH, expand=True)
        tk.Label(f, text="Nuevo Producto", font=("Segoe UI", 12, "bold"),
                 bg=st.OSCURO, fg=st.DORADO).pack(anchor=tk.W, pady=(0, 12))

        self._entries: dict[str, tk.Entry] = {}
        for lbl, key in [
            ("Nombre:", "nombre"),
            ("Categoría:", "categoria"),
            ("Precio:", "precio"),
            ("Descripción:", "descripcion"),
        ]:
            tk.Label(f, text=lbl, font=("Segoe UI", 10),
                     bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(anchor=tk.W)
            e = tk.Entry(f, **st.estilo_entry(), width=30)
            e.configure(bg=st.OSCURO_CLARO)
            e.pack(fill=tk.X, pady=(2, 8))
            self._entries[key] = e

        tk.Label(f, text="Módulo:", font=("Segoe UI", 10),
                 bg=st.OSCURO, fg=st.TEXTO_GRIS).pack(anchor=tk.W)
        self._combo_mod = ttk.Combobox(
            f, values=["restaurante", "bar", "spa"],
            state="readonly", width=16, font=("Segoe UI", 10))
        self._combo_mod.set("restaurante")
        self._combo_mod.pack(anchor=tk.W, pady=(2, 12))

        tk.Button(f, text="Guardar", command=self._guardar,
                  **st.estilo_boton_exito()).pack(anchor=tk.W)

    def _guardar(self):
        nombre = self._entries["nombre"].get().strip()
        cat    = self._entries["categoria"].get().strip()
        mod    = self._combo_mod.get()
        desc   = self._entries["descripcion"].get().strip()
        try:
            precio = float(self._entries["precio"].get())
        except ValueError:
            messagebox.showerror("Error", "Precio inválido.", parent=self)
            return
        if not nombre or not cat:
            messagebox.showwarning("Datos incompletos",
                                   "Nombre y categoría son obligatorios.", parent=self)
            return
        self.resultado = (nombre, cat, mod, precio, desc)
        self.destroy()


def _pedir_texto(parent, titulo: str, mensaje: str, oculto: bool = False) -> str | None:
    dlg = tk.Toplevel(parent)
    dlg.title(titulo)
    dlg.configure(bg=st.OSCURO)
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.geometry(f"320x160+{parent.winfo_rootx()+60}+{parent.winfo_rooty()+60}")
    tk.Label(dlg, text=mensaje, font=("Segoe UI", 10),
             bg=st.OSCURO, fg=st.TEXTO_CLARO,
             wraplength=280).pack(padx=16, pady=(16, 8))
    e = tk.Entry(dlg, show="•" if oculto else "",
                 **st.estilo_entry(), width=28)
    e.configure(bg=st.OSCURO_CLARO)
    e.pack(padx=16, pady=(0, 12))
    e.focus_set()
    resultado = [None]

    def ok():
        resultado[0] = e.get()
        dlg.destroy()

    tk.Button(dlg, text="Aceptar", command=ok,
              **st.estilo_boton_primario()).pack(pady=4)
    dlg.bind("<Return>", lambda _: ok())
    dlg.wait_window()
    return resultado[0]


def _aplicar_estilo_tree(tree: ttk.Treeview):
    st.aplicar_estilo_tree(tree)
