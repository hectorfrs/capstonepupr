import logging
import qwiic_relay
from utils.mqtt_publisher import MQTTPublisher
from utils.json_manager import generate_json, save_json


class RelayControl:
    """
    Clase para manejar relés Qwiic Relay conectados al bus I2C, con integración a MQTT y manejo de logs.
    """

    def __init__(self, config, mqtt_client=None, log_path="data/relay_logs.json"):
        """
        Inicializa el control de los relés basados en la configuración.

        :param config: Configuración de los relés cargada desde el archivo config.yaml.
        :param mqtt_client: Instancia del cliente MQTT (opcional).
        :param log_path: Ruta del archivo donde se guardarán los registros JSON.
        """
        self.relays = qwiic_relay.QwiicRelay()

        if not self.relays.begin():
            raise ConnectionError("El módulo Qwiic Relay no está conectado. Verifica la conexión.")

        self.valves = config["relay_module"]["addresses"]  # Diccionario con las direcciones de las válvulas
        self.trigger_level = config["trigger_level"]       # Nivel de disparo (high o low)
        self.mqtt_client = mqtt_client                    # Cliente MQTT
        self.log_path = log_path

        logging.info("Módulo Qwiic Relay inicializado.")
        print("Módulo Qwiic Relay inicializado.")

    def activate_valve(self, valve_name):
        """
        Activa una válvula específica.

        :param valve_name: Nombre de la válvula a activar.
        """
        try:
            if valve_name not in self.valves:
                raise ValueError(f"Válvula '{valve_name}' no encontrada en la configuración.")

            relay_number = self.valves[valve_name]
            self.relays.set_relay_on(relay_number)
            logging.info(f"Válvula '{valve_name}' activada (Relay {relay_number}).")
            self.log_action(valve_name, "activate", True)

            # Publicar estado en MQTT
            if self.mqtt_client:
                self.mqtt_client.publish("pi2/relay_status", f"Válvula {valve_name} activada.")
        except Exception as e:
            logging.error(f"Error al activar la válvula '{valve_name}': {e}")
            self.log_action(valve_name, "activate", False, error=str(e))

    def deactivate_valve(self, valve_name):
        """
        Desactiva una válvula específica.

        :param valve_name: Nombre de la válvula a desactivar.
        """
        try:
            if valve_name not in self.valves:
                raise ValueError(f"Válvula '{valve_name}' no encontrada en la configuración.")

            relay_number = self.valves[valve_name]
            self.relays.set_relay_off(relay_number)
            logging.info(f"Válvula '{valve_name}' desactivada (Relay {relay_number}).")
            self.log_action(valve_name, "deactivate", True)

            # Publicar estado en MQTT
            if self.mqtt_client:
                self.mqtt_client.publish("pi2/relay_status", f"Válvula {valve_name} desactivada.")
        except Exception as e:
            logging.error(f"Error al desactivar la válvula '{valve_name}': {e}")
            self.log_action(valve_name, "deactivate", False, error=str(e))

    def get_valve_status(self, valve_name):
        """
        Obtiene el estado de una válvula específica.

        :param valve_name: Nombre de la válvula a consultar.
        :return: Estado del relé (True para encendido, False para apagado).
        """
        try:
            if valve_name not in self.valves:
                raise ValueError(f"Válvula '{valve_name}' no encontrada en la configuración.")

            relay_number = self.valves[valve_name]
            status = self.relays.get_relay_state(relay_number)
            logging.info(f"Estado de la válvula '{valve_name}': {'Activada' if status else 'Desactivada'}.")
            return status
        except Exception as e:
            logging.error(f"Error al consultar el estado de la válvula '{valve_name}': {e}")
            return None

    def get_all_valve_status(self):
        """
        Consulta el estado de todas las válvulas conectadas.

        :return: Diccionario con el estado de todas las válvulas.
        """
        statuses = {}
        for valve_name in self.valves:
            statuses[valve_name] = self.get_valve_status(valve_name)
        logging.info(f"Estado de todas las válvulas: {statuses}")
        return statuses

    def deactivate_all_valves(self):
        """
        Desactiva todas las válvulas conectadas.
        """
        try:
            self.relays.set_all_relays_off()
            logging.info("Todas las válvulas desactivadas.")
            self.log_action("all", "deactivate_all", True)

            # Publicar estado en MQTT
            if self.mqtt_client:
                self.mqtt_client.publish("pi2/relay_status", "Todas las válvulas desactivadas.")
        except Exception as e:
            logging.error(f"Error al desactivar todas las válvulas: {e}")
            self.log_action("all", "deactivate_all", False, error=str(e))

    def activate_all_valves(self):
        """
        Activa todas las válvulas conectadas.
        """
        try:
            self.relays.set_all_relays_on()
            logging.info("Todas las válvulas activadas.")
            self.log_action("all", "activate_all", True)

            # Publicar estado en MQTT
            if self.mqtt_client:
                self.mqtt_client.publish("pi2/relay_status", "Todas las válvulas activadas.")
        except Exception as e:
            logging.error(f"Error al activar todas las válvulas: {e}")
            self.log_action("all", "activate_all", False, error=str(e))

    def log_action(self, valve_name, action, success, error=None):
        """
        Registra las acciones realizadas sobre las válvulas en un archivo JSON.

        :param valve_name: Nombre de la válvula afectada.
        :param action: Acción realizada ('activate', 'deactivate', etc.).
        :param success: Indica si la acción fue exitosa.
        :param error: Mensaje de error si ocurrió algún problema.
        """
        log = generate_json(
            sensor_id=valve_name,
            valve_state=action,
            pressure=None,
            action=action,
            metadata={
                "success": success,
                "error": error
            }
        )
        save_json(log, self.log_path)
