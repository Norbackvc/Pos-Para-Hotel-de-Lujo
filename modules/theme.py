"""
Hotel POS - Configuración de temas y estilos visuales
"""

# ── Paleta de colores ────────────────────────────────────────────────────────

DARK_THEME = {
    "bg":           "#1a1a2e",   # fondo principal
    "bg2":          "#16213e",   # fondo secundario
    "bg3":          "#0f3460",   # fondo de paneles
    "accent":       "#e94560",   # color de acento (rojo rubí)
    "accent2":      "#f5a623",   # acento secundario (dorado)
    "fg":           "#e0e0e0",   # texto principal
    "fg2":          "#a0a0b0",   # texto secundario
    "success":      "#27ae60",   # verde éxito
    "warning":      "#f39c12",   # amarillo advertencia
    "error":        "#e74c3c",   # rojo error
    "info":         "#3498db",   # azul info
    "sidebar":      "#0f3460",   # fondo sidebar
    "sidebar_sel":  "#e94560",   # item seleccionado en sidebar
    "card":         "#1e2a45",   # fondo de tarjetas
    "border":       "#2d4070",   # bordes
    "table_bg":     "#16213e",   # fondo de tablas
    "table_alt":    "#1a2845",   # filas alternadas
    "table_sel":    "#e94560",   # fila seleccionada
    "entry_bg":     "#1e2a45",   # fondo de entradas
    "button_bg":    "#e94560",   # fondo botones primarios
    "button_fg":    "#ffffff",   # texto botones primarios
    "button2_bg":   "#0f3460",   # fondo botones secundarios
    "button2_fg":   "#e0e0e0",   # texto botones secundarios
    "gold":         "#c9a84c",   # dorado lujo
    "font":         "Helvetica",
    "font_mono":    "Courier",
}

LIGHT_THEME = {
    "bg":           "#f5f5f0",
    "bg2":          "#ebe8e0",
    "bg3":          "#d4c9b0",
    "accent":       "#8b1a1a",
    "accent2":      "#c8860a",
    "fg":           "#1a1a1a",
    "fg2":          "#555555",
    "success":      "#1e8449",
    "warning":      "#b7770d",
    "error":        "#c0392b",
    "info":         "#1a5276",
    "sidebar":      "#2c2c2c",
    "sidebar_sel":  "#8b1a1a",
    "card":         "#fffef8",
    "border":       "#c8c0a8",
    "table_bg":     "#fffef8",
    "table_alt":    "#f5f0e8",
    "table_sel":    "#8b1a1a",
    "entry_bg":     "#ffffff",
    "button_bg":    "#8b1a1a",
    "button_fg":    "#ffffff",
    "button2_bg":   "#d4c9b0",
    "button2_fg":   "#1a1a1a",
    "gold":         "#c9a84c",
    "font":         "Helvetica",
    "font_mono":    "Courier",
}


def get_theme(name: str = "dark") -> dict:
    return LIGHT_THEME if name == "light" else DARK_THEME
