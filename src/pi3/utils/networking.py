import os
import subprocess
import logging

class NetworkManager:
    def __init__(self, ethernet_config, wifi_config):
        """
        Inicializa la configuración de red para Ethernet y Wi-Fi.

        :param ethernet_config: Diccionario con configuración de Ethernet (IP y Gateway).
        :param wifi_config: Diccionario con configuración de Wi-Fi (SSID, contraseña, IP y Gateway).
        """
        self.ethernet_config = ethernet_config
        self.wifi_config = wifi_config

    def configure_ethernet(self):
        """
        Configura la conexión Ethernet con IP y Gateway estáticos.
        """
        print("Configuring Ethernet connection...")
        try:
            # Configurar la IP y Gateway para Ethernet
            subprocess.run([
                "sudo", "ifconfig", "eth0", self.ethernet_config['ip'], "netmask", "255.255.255.0"
            ], check=True)
            subprocess.run([
                "sudo", "route", "add", "default", "gw", self.ethernet_config['gateway'], "eth0"
            ], check=True)
            print(f"Ethernet configured with IP: {self.ethernet_config['ip']}")
            logging.info(f"Ethernet configured with IP: {self.ethernet_config['ip']}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to configure Ethernet: {e}")
            logging.error(f"Failed to configure Ethernet: {e}")

    def configure_wifi(self):
        """
        Configura la conexión Wi-Fi con SSID y contraseña.
        """
        print("Configuring Wi-Fi connection...")
        try:
            # Crear el archivo wpa_supplicant.conf para la configuración de Wi-Fi
            wpa_supplicant_config = f"""
            country=US
            ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
            update_config=1

            network={{
                ssid="{self.wifi_config['ssid']}"
                psk="{self.wifi_config['password']}"
            }}
            """
            with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as file:
                file.write(wpa_supplicant_config)

            # Reiniciar el servicio de Wi-Fi
            subprocess.run(["sudo", "wpa_cli", "-i", "wlan0", "reconfigure"], check=True)
            subprocess.run(["sudo", "ifconfig", "wlan0", self.wifi_config['ip'], "netmask", "255.255.255.0"], check=True)
            subprocess.run(["sudo", "route", "add", "default", "gw", self.wifi_config['gateway'], "wlan0"], check=True)
            print(f"Wi-Fi configured with SSID: {self.wifi_config['ssid']} and IP: {self.wifi_config['ip']}")
            logging.info(f"Wi-Fi configured with SSID: {self.wifi_config['ssid']} and IP: {self.wifi_config['ip']}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to configure Wi-Fi: {e}")
            logging.error(f"Failed to configure Wi-Fi: {e}")

    def check_connection(self):
        """
        Verifica la conexión a Internet utilizando `ping`.
        """
        print("Checking internet connection...")
        try:
            subprocess.run(["ping", "-c", "3", "8.8.8.8"], check=True)
            print("Internet connection is active.")
            logging.info("Internet connection is active.")
            return True
        except subprocess.CalledProcessError:
            print("Internet connection is inactive.")
            logging.warning("Internet connection is inactive.")
            return False

    def ensure_redundancy(self):
        """
        Asegura redundancia en la conexión de red, priorizando Ethernet.
        """
        print("Ensuring network redundancy...")
        if self.check_connection():
            print("No changes needed; connection is active.")
            return
        else:
            print("No active internet connection detected. Switching to backup.")
            self.configure_ethernet()
            if not self.check_connection():
                print("Ethernet failed; attempting Wi-Fi connection.")
                self.configure_wifi()
