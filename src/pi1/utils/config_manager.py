import yaml
import logging
import os

class ConfigManager:
    """
    Clase para manejar la configuración del sistema desde un archivo YAML.
    """

    def __init__(self, config_path):
        """
        Inicializa el ConfigManager cargando la configuración desde el archivo YAML.

        :param config_path: Ruta al archivo YAML.
        """
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        """
        Carga la configuración desde un archivo YAML.

        :return: Diccionario con la configuración cargada.
        """
        try:
            with open(self.config_path, "r") as file:
                config = yaml.safe_load(file)
                logging.info(f"Configuración cargada desde {self.config_path}")
                return config
        except FileNotFoundError:
            logging.error(f"No se encontró el archivo de configuración: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logging.error(f"Error al leer el archivo YAML: {e}")
            raise

    def validate_config(self):
        """
        Valida las claves requeridas en la configuración y establece valores predeterminados.
        """
        required_sections = ["system", "network", "mux", "sensors", "logging", "mqtt", "aws"]
        for section in required_sections:
            if section not in self.config:
                logging.warning(f"Sección {section} no encontrada en la configuración. Usando valores predeterminados.")
                self.config[section] = {}

    def save_config(self):
        """
        Guarda la configuración actual en el archivo YAML.
        """
        try:
            with open(self.config_path, "w") as file:
                yaml.dump(self.config, file, default_flow_style=False)
                logging.info(f"Configuración guardada en {self.config_path}")
        except Exception as e:
            logging.error(f"Error al guardar la configuración: {e}")
            raise

    def get(self, key_path, default=None):
        """
        Obtiene un valor de configuración dado su ruta en el diccionario.

        :param key_path: Ruta de la clave (por ejemplo, "system.enable_sensors").
        :param default: Valor predeterminado si la clave no existe.
        :return: Valor de configuración o el predeterminado.
        """
        keys = key_path.split(".")
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

# Ejemplo de uso
if __name__ == "__main__":
    config_manager = ConfigManager("/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml")
    config_manager.validate_config()

    # Ejemplo de lectura de configuraciones
    logging.info(f"MQTT habilitado: {config_manager.get('system.enable_mqtt')}")
    logging.info(f"Tópico para datos de sensores: {config_manager.get('mqtt.topics.sensor_data')}")
