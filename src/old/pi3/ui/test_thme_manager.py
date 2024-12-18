import customtkinter as ctk
from ui.theme_manager import ThemeManager

# Configurar la aplicación
class TestApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración básica de la ventana
        self.title("Prueba de ThemeManager")
        self.geometry("400x300")

        # Aplicar el tema
        ThemeManager.apply_theme()

        # Frame principal
        frame = ctk.CTkFrame(self)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Etiqueta de prueba
        label = ctk.CTkLabel(frame, text="Hola, este es un ejemplo de tema.", font=ThemeManager.FONT_TITLE)
        label.pack(pady=10)
        ThemeManager.style_label(label)

        # Botón de prueba
        button = ctk.CTkButton(frame, text="Presióname", command=self.button_action)
        button.pack(pady=10)
        ThemeManager.style_button(button)

    def button_action(self):
        # Acción del botón
        ctk.CTkMessagebox.show_info("Acción", "¡Botón presionado!")

# Ejecutar la aplicación
if __name__ == "__main__":
    app = TestApp()
    app.mainloop()
