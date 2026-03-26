"""
login.py – Ventana de inicio de sesión.
"""

import tkinter as tk
from tkinter import messagebox

from modules import database as db
from modules import estilos as st


class VentanaLogin(tk.Tk):
    """Ventana principal de login. Al autenticarse lanza el Dashboard."""

    def __init__(self):
        super().__init__()
        self.title("Hotel de Lujo – POS")
        self.resizable(False, False)
        self.configure(bg=st.OSCURO)
        self._centrar_ventana(420, 560)
        self._build_ui()
        self.bind("<Return>", lambda _e: self._ingresar())

    def _centrar_ventana(self, ancho: int, alto: int):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - ancho) // 2
        y = (sh - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    # ── Construcción de la UI ─────────────────────────────────────────────────

    def _build_ui(self):
        config = {
            "hotel_nombre":   db.get_config("hotel_nombre",   "Hotel de Lujo"),
            "hotel_slogan":   db.get_config("hotel_slogan",   "Sistema de Punto de Venta"),
            "version":        db.get_config("version",        "1.0.0"),
        }

        contenedor = tk.Frame(self, bg=st.OSCURO, padx=40, pady=30)
        contenedor.pack(fill=tk.BOTH, expand=True)

        # ── Logo ──────────────────────────────────────────────────────────────
        tk.Label(
            contenedor, text="🏨",
            font=("Segoe UI", 54),
            bg=st.OSCURO, fg=st.DORADO,
        ).pack(pady=(0, 4))

        tk.Label(
            contenedor,
            text=config["hotel_nombre"].upper(),
            font=("Segoe UI", 20, "bold"),
            bg=st.OSCURO, fg=st.DORADO,
        ).pack()

        tk.Label(
            contenedor,
            text=config["hotel_slogan"].upper(),
            font=("Segoe UI", 9),
            bg=st.OSCURO, fg=st.TEXTO_GRIS,
        ).pack(pady=(2, 20))

        # ── Tarjeta de login ──────────────────────────────────────────────────
        card = tk.Frame(
            contenedor,
            bg=st.OSCURO_MEDIO,
            highlightthickness=1,
            highlightbackground=st.DORADO,
            padx=28, pady=24,
        )
        card.pack(fill=tk.X)

        tk.Label(
            card,
            text="Iniciar Sesión",
            font=("Segoe UI", 13, "bold"),
            bg=st.OSCURO_MEDIO, fg=st.DORADO_CLARO,
        ).pack(pady=(0, 18))

        # Usuario
        tk.Label(card, text="USUARIO", font=("Segoe UI", 8),
                 bg=st.OSCURO_MEDIO, fg=st.TEXTO_GRIS).pack(anchor=tk.W)
        self._entry_usuario = tk.Entry(card, **st.estilo_entry())
        self._entry_usuario.configure(bg=st.OSCURO_CLARO)
        self._entry_usuario.pack(fill=tk.X, pady=(2, 12))

        # Contraseña
        tk.Label(card, text="CONTRASEÑA", font=("Segoe UI", 8),
                 bg=st.OSCURO_MEDIO, fg=st.TEXTO_GRIS).pack(anchor=tk.W)
        self._entry_contra = tk.Entry(card, show="•", **st.estilo_entry())
        self._entry_contra.configure(bg=st.OSCURO_CLARO)
        self._entry_contra.pack(fill=tk.X, pady=(2, 8))

        # Mensaje de error
        self._lbl_error = tk.Label(
            card, text="", font=("Segoe UI", 9),
            bg=st.OSCURO_MEDIO, fg=st.ERROR,
        )
        self._lbl_error.pack(pady=(0, 8))

        # Botón ingresar
        btn = tk.Button(card, text="INGRESAR",
                        command=self._ingresar, **st.estilo_boton_primario())
        btn.pack(fill=tk.X, pady=(4, 0))

        # Versión
        tk.Label(
            contenedor,
            text=f"v{config['version']}",
            font=("Segoe UI", 8),
            bg=st.OSCURO, fg="#444466",
        ).pack(pady=(16, 0))

        self._entry_usuario.focus_set()

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _ingresar(self):
        usuario  = self._entry_usuario.get().strip()
        contrasena = self._entry_contra.get()

        if not usuario or not contrasena:
            self._lbl_error.config(text="Por favor complete todos los campos.")
            return

        fila = db.verificar_credenciales(usuario, contrasena)
        if fila:
            self._lbl_error.config(text="")
            self._abrir_dashboard(dict(fila))
        else:
            self._lbl_error.config(text="Usuario o contraseña incorrectos.")
            self._entry_contra.delete(0, tk.END)
            self._entry_contra.focus_set()

    def _abrir_dashboard(self, usuario: dict):
        from modules.dashboard import VentanaDashboard
        self.withdraw()
        dash = VentanaDashboard(usuario, on_logout=self._al_cerrar_sesion)
        dash.protocol("WM_DELETE_WINDOW", lambda: self._al_cerrar_app(dash))
        dash.mainloop()

    def _al_cerrar_sesion(self, dash_window):
        dash_window.destroy()
        self._entry_usuario.delete(0, tk.END)
        self._entry_contra.delete(0, tk.END)
        self._lbl_error.config(text="")
        self.deiconify()
        self._entry_usuario.focus_set()

    def _al_cerrar_app(self, dash_window):
        dash_window.destroy()
        self.destroy()
