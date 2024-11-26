import tkinter as tk
from tkinter import messagebox
import yaml
import paho.mqtt.client as mqtt
import threading
import json
import os

class TouchScreenInterface:
    def __init__(self, config_path='config/pi3_config.yaml'):
        # Cargar la configuración
        self.load_config(config_path)
        # Configurar el cliente MQTT
        self.setup_mqtt()
        # Iniciar la interfaz gráfica
        self.init_gui()

    def load_config(self, config_path):
        """
        Carga la configuración desde el archivo YAML.
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Archivo de configuración no encontrado en {config_path}")
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        print("Configuración cargada.")

        # Extraer configuraciones relevantes
        self.width = self.config['touch_screen']['dimensions']['width']
        self.height = self.config['touch_screen']['dimensions']['height']
        self.menu_options = self.config['touch_screen']['menu']['options']
        self.mqtt_broker = self.config['local_mqtt']['broker_address']
        self.mqtt_port = self.config['local_mqtt']['port']
        self.topic_pi1 = self.config['aws']['iot_topics']['settings_update_pi1']
        self.topic_pi2 = self.config['aws']['iot_topics']['settings_update_pi2']

    def setup_mqtt(self):
        """
        Configura el cliente MQTT para comunicación local.
        """
        self.client = mqtt.Client()
        self.client.connect(self.mqtt_broker, self.mqtt_port)
        self.client.loop_start()

    def init_gui(self):
        """
        Inicializa la interfaz gráfica de usuario.
        """
        self.root = tk.Tk()
        self.root.title("Interfaz Táctil Raspberry Pi 3")
        self.root.geometry(f"{self.width}x{self.height}")

        # Crear botones del menú
        for option in self.menu_options:
            button = tk.Button(
                self.root, 
                text=option['name'], 
                command=lambda opt=option: self.handle_action(opt['action']), 
                width=30, 
                height=5
            )
            button.pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def handle_action(self, action):
        """
        Maneja las acciones seleccionadas en el menú táctil.
        """
        if action == 'adjust_valves':
            self.adjust_valves()
        elif action == 'calibrate_sensors':
            self.calibrate_sensors()
        elif action == 'view_status':
            self.view_status()
        else:
            messagebox.showerror("Error", f"Acción desconocida: {action}")

    def adjust_valves(self):
        """
        Permite ajustar las configuraciones de las válvulas.
        """
        adjust_window = tk.Toplevel(self.root)
        adjust_window.title("Ajustar Configuración de Válvulas")

        # Campos para ajustar presión mínima y máxima
        tk.Label(adjust_window, text="Presión Mínima (PSI):").pack()
        min_pressure_var = tk.DoubleVar(value=0.0)
        tk.Entry(adjust_window, textvariable=min_pressure_var).pack()

        tk.Label(adjust_window, text="Presión Máxima (PSI):").pack()
        max_pressure_var = tk.DoubleVar(value=25.0)
        tk.Entry(adjust_window, textvariable=max_pressure_var).pack()

        def send_update():
            min_pressure = min_pressure_var.get()
            max_pressure = max_pressure_var.get()
            payload = {
                'min_pressure': min_pressure,
                'max_pressure': max_pressure
            }
            self.client.publish(self.topic_pi2, json.dumps(payload))
            messagebox.showinfo("Éxito", "Configuración de válvulas actualizada.")
            adjust_window.destroy()

        tk.Button(adjust_window, text="Actualizar", command=send_update).pack()

    def calibrate_sensors(self):
        """
        Inicia el proceso de calibración de los sensores.
        """
        if messagebox.askyesno("Calibrar Sensores", "¿Desea calibrar los sensores?"):
            # Enviar comando de calibración a Raspberry Pi #1 y #2
            payload = {'action': 'calibrate'}
            self.client.publish(self.topic_pi1, json.dumps(payload))
            self.client.publish(self.topic_pi2, json.dumps(payload))
            messagebox.showinfo("Calibración", "Comando de calibración enviado a los sensores.")

    def view_status(self):
        """
        Muestra el estado actual del sistema.
        """
        status_window = tk.Toplevel(self.root)
        status_window.title("Estado del Sistema")
        tk.Label(status_window, text="Obteniendo estado del sistema...").pack()
        # Aquí se podría implementar la suscripción a tópicos de estado y mostrar datos en tiempo real

    def on_closing(self):
        """
        Maneja el cierre de la aplicación.
        """
        if messagebox.askokcancel("Salir", "¿Desea cerrar la aplicación?"):
            self.client.loop_stop()
            self.root.destroy()

    def run(self):
        """
        Ejecuta el bucle principal de la interfaz gráfica.
        """
        self.root.mainloop()

if __name__ == '__main__':
    interface = TouchScreenInterface()
    interface.run()
