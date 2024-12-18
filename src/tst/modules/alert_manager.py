# alert_manager.py - Clase para manejar alertas críticas del sistema.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import logging
import json
import os
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Dict
from modules.logging_manager import LoggingManager
from modules.mqtt_handler import MQTTHandler

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

    def __init__(self, config_manager, mqtt_handler=None, local_log_path="~/logs/alerts.json", rotate_logs=True):
        """
        Inicializa el manejador de alertas.

        :param config_manager: Instancia de ConfigManager para manejar configuraciones dinámicas.
        :param mqtt_handler: Instancia opcional de MQTTHandler para transmitir alertas.
        :param local_log_path: Ruta para almacenar alertas localmente.
        :param rotate_logs: Habilitar o deshabilitar la rotación de logs.
        """
        self.config_manager = config_manager
        self.mqtt_handler = mqtt_handler

        # Configurar logger centralizado
        self.logger = LoggingManager(config_manager).setup_logger("[ALERT_MANAGER]")

        # Generar el tópico dinámicamente si no se proporciona
        self.alert_topic = self.config_manager.get("mqtt.alert_topic", "alerts/default")
        self.local_log_path = os.path.expanduser(local_log_path)
        self.rotate_logs = rotate_logs

        # Crear directorio de logs si no existe
        log_dir = os.path.dirname(self.local_log_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            self.logger.info(f"Directorio creado para logs locales de alertas: {log_dir}")

    def send_alert(self, level, message, metadata=None):
        """
        Envía una alerta con el nivel y el mensaje especificado.

        :param level: Nivel de alerta (INFO, WARNING, CRITICAL).
        :param message: Mensaje descriptivo de la alerta.
        :param metadata: Datos adicionales (opcional).
        """
        if level not in self.ALLOWED_LEVELS:
            self.logger.error(f"Nivel de alerta inválido: {level}. Debe ser uno de {self.ALLOWED_LEVELS}.")
            return

        if metadata is not None and not isinstance(metadata, dict):
            self.logger.error("El parámetro 'metadata' debe ser un diccionario.")
            return

        alert = Alert(level=level, message=message, metadata=metadata or {})

        # Registrar alerta en el log
        self._log_alert(alert)

        # Enviar alerta por MQTT si está habilitado
        if self.mqtt_handler and self.mqtt_handler.is_connected():
            self._send_mqtt_alert(alert)

    def _send_mqtt_alert(self, alert):
        """
        Envía una alerta por MQTT, incluyendo un ID único.

        :param alert: Instancia de la clase Alert.
        """
        try:
            alert_data = alert.__dict__.copy()
            alert_data["id"] = str(uuid.uuid4())  # Agregar un ID único

            self.mqtt_handler.publish(self.alert_topic, alert_data)
            self.logger.info(f"Alerta enviada a MQTT: {alert_data}")
        except Exception as e:
            self.logger.error(f"Error enviando alerta a MQTT: {e}")

    def _log_alert(self, alert):
        """
        Registra la alerta en el archivo local y en el sistema de logs.

        :param alert: Instancia de la clase Alert.
        """
        log_level = alert.level.upper()
        if log_level == "CRITICAL":
            self.logger.critical(alert.message)
        elif log_level == "WARNING":
            self.logger.warning(alert.message)
        else:
            self.logger.info(alert.message)

        # Guardar en archivo JSON
        try:
            if self.rotate_logs and os.path.exists(self.local_log_path) and os.path.getsize(self.local_log_path) > 5 * 1024 * 1024:  # 5 MB
                self._rotate_log()

            with open(self.local_log_path, "a") as log_file:
                json.dump(alert.__dict__, log_file)
                log_file.write("\n")
        except Exception as e:
            self.logger.error(f"Error guardando alerta localmente: {e}")

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
            self.logger.info(f"Archivo de log de alertas rotado. Respaldo creado en {backup_path}.")
        except Exception as e:
            self.logger.error(f"Error rotando el archivo de log de alertas: {e}")
