# network_manager.py - Clase para manejar la conexión de red en Raspberry Pi.
# Desarrollado por Héctor F. Rivera Santiago
# copyright (c) 2024

import os
import time
import logging
import socket
import subprocess
from threading import Thread

class NetworkManager:
    """
    Maneja la conexión de red para conmutar entre Ethernet y Wi-Fi automáticamente.
    """
    def __init__(self, config):
        self.config = config
        self.current_interface = "ethernet"  # Ethernet por defecto
        self.ping_host = "localhost"  # Google DNS para pruebas de conectividad
        self.check_interval = 10  # Intervalo en segundos para verificar conectividad
        self.network_status = {"ethernet": False, "wifi": False}
        self.monitoring_thread = None
        self.keep_monitoring = False

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
        logging.warning("[MANAGER] [NET] Conmutando a red Wi-Fi...")
        self.current_interface = "wifi"
        self._configure_network(self.config["network"]["wifi"])
        self.network_status["wifi"] = True

    def switch_to_ethernet(self):
        """
        Conmuta a Ethernet configurando la interfaz y reiniciando la red.
        """
        logging.warning("[MANAGER] [NET] Conmutando a red Ethernet...")
        self.current_interface = "ethernet"
        self._configure_network(self.config["network"]["ethernet"])
        self.network_status["ethernet"] = True

    def _configure_network(self, network_config):
        """
        Configura los parámetros de red (IP estática, puerta de enlace).
        """
        try:
            logging.info(f"[MANAGER] [NET] Configurando red para la interfaz {self.current_interface}...")
            ip = network_config["ip"]
            gateway = network_config["gateway"]

            # Asignar IP estática
            subprocess.run(
                ["sudo", "ifconfig", self.current_interface, ip, "netmask", "255.255.255.0"],
                check=True
            )
            subprocess.run(
                ["sudo", "route", "add", "default", "gw", gateway, self.current_interface],
                check=True
            )
            logging.info(f"[MANAGER] [NET] Red configurada con IP: {ip}, Gateway: {gateway}.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error configurando red: {e}")

    def monitor_network(self):
        """
        Monitorea la conexión de red y conmutación entre Ethernet y Wi-Fi.
        """
        logging.info("[MANAGER] [NET] Iniciando monitoreo de red...")
        self.keep_monitoring = True
        while self.keep_monitoring:
            if self.current_interface == "ethernet" and not self.is_connected():
                logging.warning("[MANAGER] [NET] Conexión Ethernet perdida. Intentando cambiar a Wi-Fi...")
                self.switch_to_wifi()
            elif self.current_interface == "wifi" and not self.is_connected():
                logging.warning("[MANAGER] [NET] Conexión Wi-Fi perdida. Intentando cambiar a Ethernet...")
                self.switch_to_ethernet()
            time.sleep(self.check_interval)

    def start_monitoring(self):
        """
        Inicia el monitoreo en un hilo independiente.
        """
        if not self.monitoring_thread:
            self.monitoring_thread = Thread(target=self.monitor_network, daemon=True)
            self.monitoring_thread.start()
            logging.info(f"[MANAGER] [NET] Monitoreo de red iniciado.")

    def stop_monitoring(self):
        """
        Detiene el monitoreo de red.
        """
        self.keep_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
            self.monitoring_thread = None
            logging.info("[MANAGER] [NET] Monitoreo de red detenido.")
