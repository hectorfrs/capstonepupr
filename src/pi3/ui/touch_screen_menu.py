import customtkinter as ctk
from utils.mqtt_client import MQTTPublisher  # Ajusta según tu implementación
import threading
import json

# Configuración inicial de CustomTkinter
ctk.set_appearance_mode("dark")  # Opciones: "dark", "light", "system"
ctk.set_default_color_theme("blue")  # Opciones: "blue", "green", "dark-blue"

class TouchScreenMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("Capstone: Raspberry Pi #3")
        self.root.geometry("800x480")  # Resolución para pantallas táctiles típicas

        # Configurar MQTT
        self.mqtt_client = MQTTPublisher(config_path="config/pi3_config.yaml")
        self.mqtt_client.connect()

        # Crear el menú principal
        self.create_main_menu()

    def create_main_menu(self):
        """Crea el menú principal."""
        self.clear_screen()

        # Título
        ctk.CTkLabel(self.root, text="Menú Principal", font=("Arial", 28, "bold")).pack(pady=20)

        # Botones de opciones
        ctk.CTkButton(self.root, text="Estado del Sistema", font=("Arial", 18),
                      command=self.show_system_status).pack(pady=10)
        ctk.CTkButton(self.root, text="Cámara", font=("Arial", 18),
                      command=self.camera_menu).pack(pady=10)
        ctk.CTkButton(self.root, text="Configuración", font=("Arial", 18),
                      command=self.configuration_menu).pack(pady=10)
        ctk.CTkButton(self.root, text="Acciones", font=("Arial", 18),
                      command=self.actions_menu).pack(pady=10)
        ctk.CTkButton(self.root, text="Logs y Diagnósticos", font=("Arial", 18),
                      command=self.logs_menu).pack(pady=10)
        ctk.CTkButton(self.root, text="Salir", font=("Arial", 18),
                      command=self.root.quit).pack(pady=20)

    def show_system_status(self):
        """Muestra el estado del sistema."""
        self.clear_screen()
        ctk.CTkLabel(self.root, text="Estado del Sistema", font=("Arial", 24, "bold")).pack(pady=20)

        # Estado de sensores y MQTT
        ctk.CTkLabel(self.root, text="Estado de Raspberry #1 y #2", font=("Arial", 18)).pack(pady=10)
        ctk.CTkLabel(self.root, text="Conexión MQTT: Activa", font=("Arial", 16)).pack(pady=5)
        ctk.CTkButton(self.root, text="Regresar", font=("Arial", 18),
                      command=self.create_main_menu).pack(pady=20)

    def camera_menu(self):
        """Submenú de Cámara."""
        self.clear_screen()
        ctk.CTkLabel(self.root, text="Cámara", font=("Arial", 24, "bold")).pack(pady=20)

        # Botones para capturar y procesar imágenes
        ctk.CTkButton(self.root, text="Capturar Imagen", font=("Arial", 18),
                      command=self.capture_image).pack(pady=10)
        ctk.CTkButton(self.root, text="Ver Imagen", font=("Arial", 18),
                      command=self.view_image).pack(pady=10)
        ctk.CTkButton(self.root, text="Procesar con AWS", font=("Arial", 18),
                      command=self.process_with_aws).pack(pady=10)
        ctk.CTkButton(self.root, text="Regresar", font=("Arial", 18),
                      command=self.create_main_menu).pack(pady=20)

    def configuration_menu(self):
        """Submenú de Configuración."""
        self.clear_screen()
        ctk.CTkLabel(self.root, text="Configuración", font=("Arial", 24, "bold")).pack(pady=20)

        # Configuración general
        ctk.CTkButton(self.root, text="Red", font=("Arial", 18),
                      command=self.network_config).pack(pady=10)
        ctk.CTkButton(self.root, text="Sensores", font=("Arial", 18),
                      command=self.sensor_config).pack(pady=10)
        ctk.CTkButton(self.root, text="Broker MQTT", font=("Arial", 18),
                      command=self.mqtt_config).pack(pady=10)
        ctk.CTkButton(self.root, text="Pantalla", font=("Arial", 18),
                      command=self.screen_config).pack(pady=10)
        ctk.CTkButton(self.root, text="Regresar", font=("Arial", 18),
                      command=self.create_main_menu).pack(pady=20)

    def clear_screen(self):
        """Limpia la pantalla."""
        for widget in self.root.winfo_children():
            widget.destroy()

# Iniciar aplicación
if __name__ == "__main__":
    root = ctk.CTk()
    app = TouchScreenMenu(root)
    root.mainloop()
