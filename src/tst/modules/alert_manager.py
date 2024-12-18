# alert_manager.py - Clase para manejar alertas críticas del sistema.
import logging
import json
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Dict
from utils.mqtt_publisher import MQTTPublisher

# Configurar el formato del logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

@dataclass
class Alert:
    level: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        valid_levels = {"INFO", "WARNING", "CRITICAL"}
        if self.level not in valid_levels:
            raise ValueError(f"Nivel de alerta inválido: {self.level}")


class AlertManager:
    """
    Clase para manejar alertas críticas del sistema.
    """
    ALLOWED_LEVELS = {"INFO", "WARNING", "CRITICAL"}

    def __init__(self, mqtt_client=None, alert_topic="raspberry-1/alerts", local_log_path="~/logs/alerts.json", rotate_logs=True):
        """
        Inicializa el manejador de alertas.

        :param mqtt_client: Cliente MQTT para enviar notificaciones (opcional).
        :param alert_topic: Tópico MQTT para enviar alertas.
        :param local_log_path: Ruta para almacenar alertas localmente.
        :param rotate_logs: Habilitar o deshabilitar la rotación de logs.
        """
        self.mqtt_client = mqtt_client
        self.alert_topic = alert_topic
        self.local_log_path = os.path.expanduser(local_log_path)
        self.rotate_logs = rotate_logs

        # Crear directorio de logs si no existe
        log_dir = os.path.dirname(self.local_log_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            logging.info(f"Directorio creado para logs locales de alertas: {log_dir}")

        # Validar configuración inicial
        self._validate_initial_config()

    def _validate_initial_config(self):
        if not self.alert_topic:
            raise ValueError("El tópico MQTT para alertas no está configurado.")
        if not self.local_log_path:
            raise ValueError("La ruta del log local no está configurada.")

    def send_alert(self, level, message, metadata=None):
        """
        Envía una alerta con el nivel y el mensaje especificado.

        :param level: Nivel de alerta (INFO, WARNING, CRITICAL).
        :param message: Mensaje descriptivo de la alerta.
        :param metadata: Datos adicionales (opcional).
        """
        if level not in self.ALLOWED_LEVELS:
            logging.error(f"Nivel de alerta inválido: {level}. Debe ser uno de {self.ALLOWED_LEVELS}.")
            return

        if metadata is not None and not isinstance(metadata, dict):
            logging.error("El parámetro 'metadata' debe ser un diccionario.")
            return

        alert = Alert(level=level, message=message, metadata=metadata or {})

        # Registrar alerta en el log
        self._log_alert(alert)

        # Enviar alerta por MQTT si está habilitado
        if self.mqtt_client:
            self._send_mqtt_alert(alert)

    def _send_mqtt_alert(self, alert):
        """
        Envía una alerta por MQTT.

        :param alert: Instancia de la clase Alert.
        """
        try:
            self.mqtt_client.publish(self.alert_topic, json.dumps(alert.__dict__))
            logging.info(f"Alerta enviada a MQTT: {alert}")
        except Exception as e:
            logging.error(f"Error enviando alerta a MQTT: {e}")

    def _log_alert(self, alert):
        """
        Registra la alerta en el archivo local y en el sistema de logs.

        :param alert: Instancia de la clase Alert.
        """
        log_level = alert.level.upper()
        if log_level == "CRITICAL":
            logging.critical(alert.message)
        elif log_level == "WARNING":
            logging.warning(alert.message)
        else:
            logging.info(alert.message)

        # Guardar en archivo JSON
        try:
            if self.rotate_logs and os.path.exists(self.local_log_path) and os.path.getsize(self.local_log_path) > 5 * 1024 * 1024:  # 5 MB
                self._rotate_log()

            with open(self.local_log_path, "a") as log_file:
                json.dump(alert.__dict__, log_file)
                log_file.write("\n")
        except Exception as e:
            logging.error(f"Error guardando alerta localmente: {e}")

    def _rotate_log(self):
        """
        Realiza una rotación del archivo de logs locales si excede el tamaño máximo.
        """
        try:
            base, ext = os.path.splitext(self.local_log_path)
            backup_path = f"{base}_backup{ext}"
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(self.local_log_path, backup_path)
            logging.info(f"Archivo de log de alertas rotado. Respaldo creado en {backup_path}.")
        except Exception as e:
            logging.error(f"Error rotando el archivo de log de alertas: {e}")

# # Ejemplo de uso
# if __name__ == "__main__":
#     # Crear una instancia de AlertManager
#     alert_manager = AlertManager(local_log_path="~/logs/alerts.json")

#     # Enviar una alerta
#     alert_manager.send_alert(
#         level="CRITICAL",
#         message="Prueba de alerta crítica",
#         metadata={"sensor": "CPU", "value": "95°C"},
#     )
