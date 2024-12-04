import logging
import json
from datetime import datetime
from utils.mqtt_publisher import MQTTPublisher

class AlertManager:
    """
    Clase para manejar alertas críticas del sistema.
    """
    def __init__(self, mqtt_client=None, alert_topic="raspberry-1/alerts", local_log_path="/logs/alerts.json"):
        """
        Inicializa el manejador de alertas.

        :param mqtt_client: Cliente MQTT para enviar notificaciones (opcional).
        :param alert_topic: Tópico MQTT para enviar alertas.
        :param local_log_path: Ruta para almacenar alertas localmente.
        """
        self.mqtt_client = mqtt_client
        self.alert_topic = alert_topic
        self.local_log_path = local_log_path

    def send_alert(self, level, message, metadata=None):
        """
        Envía una alerta con el nivel y el mensaje especificado.

        :param level: Nivel de alerta (INFO, WARNING, CRITICAL).
        :param message: Mensaje descriptivo de la alerta.
        :param metadata: Datos adicionales (opcional).
        """
        alert = {
            "level": level,
            "message": message,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Registrar alerta en el log
        self._log_alert(alert)

        # Enviar alerta por MQTT si está habilitado
        if self.mqtt_client:
            try:
                self.mqtt_client.publish(self.alert_topic, json.dumps(alert))
                logging.info(f"Alerta enviada a MQTT: {alert}")
            except Exception as e:
                logging.error(f"Error enviando alerta a MQTT: {e}")

    def _log_alert(self, alert):
        """
        Registra la alerta en el archivo local y en el sistema de logs.

        :param alert: Diccionario con los datos de la alerta.
        """
        log_level = alert["level"].upper()
        if log_level == "CRITICAL":
            logging.critical(alert["message"])
        elif log_level == "WARNING":
            logging.warning(alert["message"])
        else:
            logging.info(alert["message"])

        # Guardar en archivo JSON
        try:
            with open(self.local_log_path, "a") as log_file:
                json.dump(alert, log_file)
                log_file.write("\n")
        except Exception as e:
            logging.error(f"Error guardando alerta localmente: {e}")
