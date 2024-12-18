# network_manager.py - Clase para manejar la conexión de red en Raspberry Pi.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import os
import time
import subprocess
from threading import Thread

class NetworkManager:
    """
    Maneja la conexión de red para conmutar entre Ethernet y Wi-Fi automáticamente.
    """

    def __init__(self, config_manager, mqtt_handler=None):
        """
        Inicializa el NetworkManager con la configuración proporcionada.

        :param config_manager: Instancia de ConfigManager para manejar configuraciones centralizadas.
        :param mqtt_handler: Instancia opcional de MQTTHandler para reportar eventos de red.
        """
        from modules.logging_manager import LoggingManager

        self.config_manager = config_manager
        self.mqtt_handler = mqtt_handler
        self.enable_network_monitoring = self.config_manager.get("system.enable_network_monitoring", True)
        self.current_interface = "ethernet"  # Ethernet por defecto
        self.ping_host = self.config_manager.get("network.ping_host", "192.168.1.147")
        self.check_interval = self.config_manager.get("network.check_interval", 10)
        self.network_status = {"ethernet": False, "wifi": False}
        self.monitoring_thread = None
        self.keep_monitoring = False

        # Configurar logger centralizado
        self.logger = LoggingManager(config_manager).setup_logger("[NETWORK_MANAGER]")

        if not self.enable_network_monitoring:
            self.logger.warning("El monitoreo de red está deshabilitado en la configuración.")

    def is_connected(self, host=None):
        """
        Verifica si hay conexión a Internet haciendo ping a un host.
        """
        host = host or self.ping_host
        try:
            subprocess.check_call(
                ["ping", "-c", "1", "-W", "2", host],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def switch_to_wifi(self):
        """
        Conmuta a Wi-Fi configurando la interfaz y reiniciando la red.
        """
        self.logger.warning("Conmutando a red Wi-Fi...")
        self.current_interface = "wifi"
        self.network_status["wifi"] = True
        if self.mqtt_handler and self.mqtt_handler.is_connected():
            self.mqtt_handler.publish("network/events", {
                "event": "switched_to_wifi",
                "timestamp": time.time()
            })

    def switch_to_ethernet(self):
        """
        Conmuta a Ethernet configurando la interfaz y reiniciando la red.
        """
        self.logger.warning("Conmutando a red Ethernet...")
        self.current_interface = "ethernet"
        self.network_status["ethernet"] = True
        if self.mqtt_handler and self.mqtt_handler.is_connected():
            self.mqtt_handler.publish("network/events", {
                "event": "switched_to_ethernet",
                "timestamp": time.time()
            })

    def monitor_network(self):
        """
        Monitorea la conexión de red y conmutación entre Ethernet y Wi-Fi.
        """
        if not self.enable_network_monitoring:
            self.logger.warning("El monitoreo de red está deshabilitado.")
            return

        self.logger.info("Iniciando monitoreo de red...")
        self.keep_monitoring = True
        while self.keep_monitoring:
            if self.current_interface == "ethernet" and not self.is_connected():
                self.logger.warning("Conexión Ethernet perdida. Intentando cambiar a Wi-Fi...")
                self.switch_to_wifi()
            elif self.current_interface == "wifi" and not self.is_connected():
                self.logger.warning("Conexión Wi-Fi perdida. Intentando cambiar a Ethernet...")
                self.switch_to_ethernet()
            time.sleep(self.check_interval)

    def start_monitoring(self):
        """
        Inicia el monitoreo en un hilo independiente.
        """
        if not self.enable_network_monitoring:
            self.logger.warning("El monitoreo de red está deshabilitado en la configuración. Operación omitida.")
            return

        if not self.monitoring_thread:
            self.monitoring_thread = Thread(target=self.monitor_network, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("Monitoreo de red iniciado.")

    def stop_monitoring(self):
        """
        Detiene el monitoreo de red.
        """
        self.keep_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
            self.monitoring_thread = None
            self.logger.info("Monitoreo de red detenido.")
