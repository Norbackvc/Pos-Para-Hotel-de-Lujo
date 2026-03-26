"""
estilos.py – Constantes de tema visual y utilidades de UI compartidas.
"""

import tkinter as tk
from tkinter import ttk

# Colores (equivalentes a las variables CSS del prototipo)
DORADO       = "#c9a84c"
DORADO_CLARO = "#f0d080"
OSCURO       = "#1a1a2e"
OSCURO_MEDIO = "#16213e"
OSCURO_CLARO = "#0f3460"
TEXTO_CLARO  = "#f0f0f0"
TEXTO_GRIS   = "#a0a0b0"
ERROR        = "#e74c3c"
EXITO        = "#2ecc71"
ADVERTENCIA  = "#f39c12"
BLANCO       = "#ffffff"

# Fuentes
FUENTE_TITULO   = ("Segoe UI", 18, "bold")
FUENTE_SUBTITULO= ("Segoe UI", 13, "bold")
FUENTE_NORMAL   = ("Segoe UI", 11)
FUENTE_PEQUEÑA  = ("Segoe UI",  9)
FUENTE_BOTON    = ("Segoe UI", 11, "bold")
FUENTE_MONO     = ("Courier New", 10)

# Paddings / radios
PAD = 10
PAD_GRANDE = 20


def aplicar_tema_widget(widget, bg=OSCURO, fg=TEXTO_CLARO):
    """Aplica colores de fondo y texto a un widget tkinter."""
    try:
        widget.configure(bg=bg, fg=fg)
    except Exception:
        pass


def estilo_boton_primario() -> dict:
    return {
        "bg": DORADO,
        "fg": OSCURO,
        "font": FUENTE_BOTON,
        "relief": "flat",
        "cursor": "hand2",
        "padx": 16,
        "pady": 8,
        "activebackground": DORADO_CLARO,
        "activeforeground": OSCURO,
    }


def estilo_boton_secundario() -> dict:
    return {
        "bg": OSCURO_CLARO,
        "fg": DORADO,
        "font": FUENTE_BOTON,
        "relief": "flat",
        "cursor": "hand2",
        "padx": 16,
        "pady": 8,
        "activebackground": OSCURO_MEDIO,
        "activeforeground": DORADO_CLARO,
    }


def estilo_boton_peligro() -> dict:
    return {
        "bg": ERROR,
        "fg": BLANCO,
        "font": FUENTE_BOTON,
        "relief": "flat",
        "cursor": "hand2",
        "padx": 16,
        "pady": 8,
        "activebackground": "#c0392b",
        "activeforeground": BLANCO,
    }


def estilo_boton_exito() -> dict:
    return {
        "bg": EXITO,
        "fg": OSCURO,
        "font": FUENTE_BOTON,
        "relief": "flat",
        "cursor": "hand2",
        "padx": 16,
        "pady": 8,
        "activebackground": "#27ae60",
        "activeforeground": OSCURO,
    }


def estilo_entry() -> dict:
    return {
        "bg": OSCURO_CLARO,
        "fg": TEXTO_CLARO,
        "insertbackground": DORADO,
        "relief": "flat",
        "font": FUENTE_NORMAL,
        "highlightthickness": 1,
        "highlightbackground": DORADO,
        "highlightcolor": DORADO_CLARO,
    }


def estilo_label(bold=False) -> dict:
    font = ("Segoe UI", 11, "bold") if bold else FUENTE_NORMAL
    return {"bg": OSCURO, "fg": TEXTO_CLARO, "font": font}


def estilo_frame() -> dict:
    return {"bg": OSCURO}


def estilo_listbox() -> dict:
    return {
        "bg": OSCURO_CLARO,
        "fg": TEXTO_CLARO,
        "selectbackground": DORADO,
        "selectforeground": OSCURO,
        "font": FUENTE_NORMAL,
        "relief": "flat",
        "highlightthickness": 0,
        "borderwidth": 0,
    }


# ── Utilidades de UI compartidas ──────────────────────────────────────────────

def aplicar_estilo_tree(tree: ttk.Treeview):
    """Aplica el tema oscuro-dorado a cualquier Treeview."""
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Treeview",
                    background=OSCURO_CLARO,
                    foreground=TEXTO_CLARO,
                    fieldbackground=OSCURO_CLARO,
                    rowheight=26,
                    font=("Segoe UI", 10))
    style.configure("Treeview.Heading",
                    background=OSCURO_MEDIO,
                    foreground=DORADO,
                    font=("Segoe UI", 10, "bold"))
    style.map("Treeview",
              background=[("selected", DORADO)],
              foreground=[("selected", OSCURO)])


def dialogo_metodo_pago(parent: tk.Widget, total: float, simbolo: str) -> str | None:
    """Muestra un diálogo para seleccionar el método de pago y retorna la elección."""
    dlg = tk.Toplevel(parent)
    dlg.title("Método de pago")
    dlg.configure(bg=OSCURO)
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.geometry(f"300x210+{parent.winfo_rootx()+60}+{parent.winfo_rooty()+60}")

    tk.Label(dlg, text=f"Total: {simbolo}{total:.2f}",
             font=("Segoe UI", 13, "bold"), bg=OSCURO, fg=DORADO).pack(pady=(18, 10))
    metodo_var = tk.StringVar(value="Efectivo")
    frame_r = tk.Frame(dlg, bg=OSCURO)
    frame_r.pack()
    for op in ("Efectivo", "Tarjeta crédito", "Tarjeta débito", "Transferencia"):
        tk.Radiobutton(frame_r, text=op, variable=metodo_var, value=op,
                       bg=OSCURO, fg=TEXTO_CLARO, selectcolor=OSCURO_CLARO,
                       activebackground=OSCURO, font=("Segoe UI", 10),
                       cursor="hand2").pack(anchor=tk.W)
    resultado: list[str | None] = [None]

    def ok():
        resultado[0] = metodo_var.get()
        dlg.destroy()

    tk.Button(dlg, text="Confirmar", command=ok,
              **estilo_boton_exito()).pack(pady=10)
    dlg.wait_window()
    return resultado[0]
