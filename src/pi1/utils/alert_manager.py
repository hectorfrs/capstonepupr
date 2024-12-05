# alert_manager.py - Clase para manejar alertas críticas del sistema.
import logging
import json
import os
from datetime import datetime
from utils.mqtt_publisher import MQTTPublisher

class AlertManager:
    """
    Clase para manejar alertas críticas del sistema.
    """
    ALLOWED_LEVELS = {"INFO", "WARNING", "CRITICAL"}

    def __init__(self, mqtt_client=None, alert_topic="raspberry-1/alerts", local_log_path="/home/raspberry-1/logs/alerts.json"):
        """
        Inicializa el manejador de alertas.

        :param mqtt_client: Cliente MQTT para enviar notificaciones (opcional).
        :param alert_topic: Tópico MQTT para enviar alertas.
        :param local_log_path: Ruta para almacenar alertas localmente.
        """
        self.mqtt_client = mqtt_client
        self.alert_topic = alert_topic
        self.local_log_path = local_log_path or config["logging"]["log_file"]

        # Crear directorio de logs si no existe
        log_dir = os.path.dirname(local_log_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            logging.info(f"Directorio creado para logs locales de alertas: {log_dir}")

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
            if os.path.exists(self.local_log_path) and os.path.getsize(self.local_log_path) > 5 * 1024 * 1024:  # 5 MB
                self._rotate_log()

            with open(self.local_log_path, "a") as log_file:
                json.dump(alert, log_file)
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

    def validate_config(self):
        required_logging_keys = ["log_file", "error_log_file"]
        for key in required_logging_keys:
            if key not in self.config.get("logging", {}):
                logging.warning(f"Clave {key} faltante en la sección 'logging'. Usando valor predeterminado.")
                self.config["logging"][key] = f"/home/raspberry-1/logs/default_{key}.log"
