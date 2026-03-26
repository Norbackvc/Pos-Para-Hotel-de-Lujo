"""
Hotel POS - Widgets reutilizables personalizados
"""

import tkinter as tk
from tkinter import ttk


class StyledButton(tk.Button):
    """Botón estilizado para el POS."""

    def __init__(self, parent, text, command=None, style="primary",
                 width=None, height=None, theme=None, **kwargs):
        t = theme or {}
        if style == "primary":
            bg = t.get("button_bg", "#e94560")
            fg = t.get("button_fg", "#ffffff")
        elif style == "secondary":
            bg = t.get("button2_bg", "#0f3460")
            fg = t.get("button2_fg", "#e0e0e0")
        elif style == "success":
            bg = t.get("success", "#27ae60")
            fg = "#ffffff"
        elif style == "warning":
            bg = t.get("warning", "#f39c12")
            fg = "#ffffff"
        elif style == "danger":
            bg = t.get("error", "#e74c3c")
            fg = "#ffffff"
        elif style == "gold":
            bg = t.get("gold", "#c9a84c")
            fg = "#1a1a1a"
        else:
            bg = t.get("button_bg", "#e94560")
            fg = t.get("button_fg", "#ffffff")

        kw = dict(
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            relief="flat",
            cursor="hand2",
            font=(t.get("font", "Helvetica"), 10, "bold"),
            padx=12,
            pady=6,
            activebackground=bg,
            activeforeground=fg,
            bd=0,
        )
        if width:
            kw["width"] = width
        if height:
            kw["height"] = height
        kw.update(kwargs)
        super().__init__(parent, **kw)

        # Efecto hover
        def on_enter(_):
            self.config(bg=self._lighten(bg))

        def on_leave(_):
            self.config(bg=bg)

        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)

    @staticmethod
    def _lighten(hex_color: str) -> str:
        """Aclara un color hex en ~20%."""
        try:
            hex_color = hex_color.lstrip("#")
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            r = min(255, r + 40)
            g = min(255, g + 40)
            b = min(255, b + 40)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return f"#{hex_color}"


class LabeledEntry(tk.Frame):
    """Entrada con etiqueta integrada."""

    def __init__(self, parent, label, theme=None, width=20, show="", **kwargs):
        t = theme or {}
        super().__init__(parent, bg=t.get("bg2", "#16213e"), **kwargs)
        tk.Label(
            self, text=label,
            bg=t.get("bg2", "#16213e"),
            fg=t.get("fg2", "#a0a0b0"),
            font=(t.get("font", "Helvetica"), 9),
        ).pack(anchor="w")
        self.var = tk.StringVar()
        self.entry = tk.Entry(
            self, textvariable=self.var,
            bg=t.get("entry_bg", "#1e2a45"),
            fg=t.get("fg", "#e0e0e0"),
            insertbackground=t.get("fg", "#e0e0e0"),
            relief="flat", bd=4,
            font=(t.get("font", "Helvetica"), 10),
            width=width,
            show=show,
        )
        self.entry.pack(fill="x", pady=(2, 0))

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)

    def clear(self):
        self.var.set("")


class SectionTitle(tk.Label):
    """Título de sección con línea decorativa."""

    def __init__(self, parent, text, theme=None, **kwargs):
        t = theme or {}
        super().__init__(
            parent, text=f"  {text}",
            bg=t.get("bg2", "#16213e"),
            fg=t.get("gold", "#c9a84c"),
            font=(t.get("font", "Helvetica"), 13, "bold"),
            anchor="w",
            **kwargs,
        )


class StatusBadge(tk.Label):
    """Badge de estado con color según valor."""

    STATUS_COLORS = {
        "disponible":  ("#27ae60", "#ffffff"),
        "ocupada":     ("#e74c3c", "#ffffff"),
        "mantenimiento": ("#f39c12", "#ffffff"),
        "activa":      ("#3498db", "#ffffff"),
        "completada":  ("#27ae60", "#ffffff"),
        "cancelada":   ("#7f8c8d", "#ffffff"),
        "abierta":     ("#3498db", "#ffffff"),
        "cerrada":     ("#7f8c8d", "#ffffff"),
        "pendiente":   ("#f39c12", "#ffffff"),
        "pagada":      ("#27ae60", "#ffffff"),
    }

    def __init__(self, parent, status, **kwargs):
        bg, fg = self.STATUS_COLORS.get(status.lower(), ("#7f8c8d", "#ffffff"))
        super().__init__(
            parent,
            text=f" {status.upper()} ",
            bg=bg, fg=fg,
            font=("Helvetica", 8, "bold"),
            padx=4, pady=1,
            relief="flat",
            **kwargs,
        )


class ScrollableFrame(tk.Frame):
    """Frame con scrollbar vertical."""

    def __init__(self, parent, theme=None, **kwargs):
        t = theme or {}
        super().__init__(parent, bg=t.get("bg2", "#16213e"), **kwargs)
        canvas = tk.Canvas(self, bg=t.get("bg2", "#16213e"), highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=t.get("bg2", "#16213e"))
        self.inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * int(e.delta / 120), "units"))


class StyledTreeview(ttk.Treeview):
    """Treeview estilizado."""

    def __init__(self, parent, columns, headings, theme=None, **kwargs):
        t = theme or {}
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Hotel.Treeview",
            background=t.get("table_bg", "#16213e"),
            foreground=t.get("fg", "#e0e0e0"),
            fieldbackground=t.get("table_bg", "#16213e"),
            rowheight=28,
            font=(t.get("font", "Helvetica"), 10),
        )
        style.configure(
            "Hotel.Treeview.Heading",
            background=t.get("bg3", "#0f3460"),
            foreground=t.get("gold", "#c9a84c"),
            font=(t.get("font", "Helvetica"), 10, "bold"),
            relief="flat",
        )
        style.map(
            "Hotel.Treeview",
            background=[("selected", t.get("table_sel", "#e94560"))],
            foreground=[("selected", "#ffffff")],
        )
        super().__init__(
            parent,
            columns=columns,
            show="headings",
            style="Hotel.Treeview",
            **kwargs,
        )
        for col, heading in zip(columns, headings):
            self.heading(col, text=heading)
            self.column(col, anchor="center")

    def clear(self):
        for item in self.get_children():
            self.delete(item)

    def insert_row(self, values, tags=()):
        self.insert("", "end", values=values, tags=tags)
