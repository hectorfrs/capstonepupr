import customtkinter as ctk

# Configuración del tema
class ThemeManager:
    """
    Clase para gestionar colores, fuentes y estilos de la interfaz.
    """

    # Colores principales
    PRIMARY_COLOR = "#2D2E83"   # Azul oscuro (fondo principal)
    ACCENT_COLOR = "#FF3366"   # Rosa brillante (botones y acentos)
    TEXT_COLOR = "#FFFFFF"     # Blanco (texto principal)
    TEXT_SECONDARY_COLOR = "#C0C0C0"  # Gris claro (texto secundario)

    # Fuentes
    FONT_MAIN = ("Helvetica", 16)     # Fuente principal
    FONT_TITLE = ("Helvetica", 20, "bold")  # Fuente para títulos
    FONT_SUBTITLE = ("Helvetica", 14) # Fuente para subtítulos

    # Estilos personalizados
    @staticmethod
    def apply_theme():
        """
        Aplica el tema a CustomTkinter.
        """
        ctk.set_appearance_mode("Dark")  # Tema oscuro
        ctk.set_default_color_theme({
            "button": {
                "fg_color": ThemeManager.ACCENT_COLOR,
                "hover_color": "#FF6686",
                "text_color": ThemeManager.TEXT_COLOR,
            },
            "label": {
                "text_color": ThemeManager.TEXT_COLOR,
            },
            "frame": {
                "bg_color": ThemeManager.PRIMARY_COLOR,
            }
        })

    @staticmethod
    def style_button(button):
        """
        Aplica estilos personalizados a un botón.
        """
        button.configure(
            fg_color=ThemeManager.ACCENT_COLOR,
            text_color=ThemeManager.TEXT_COLOR,
            hover_color="#FF6686"
        )

    @staticmethod
    def style_label(label):
        """
        Aplica estilos personalizados a un label.
        """
        label.configure(
            text_color=ThemeManager.TEXT_COLOR,
            font=ThemeManager.FONT_MAIN
        )
