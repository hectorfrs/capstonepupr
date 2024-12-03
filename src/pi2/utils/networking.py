import os
import subprocess
import yaml


class NetworkManager:
    """
    Clase para manejar la conectividad de red en Raspberry Pi.
    Incluye configuración para Ethernet y Wi-Fi según los parámetros del archivo YAML.
    """

    def __init__(self, config_path="config/pi2_config.yaml"):
        """
        Inicializa el NetworkManager cargando la configuración de red.

        :param config_path: Ruta al archivo YAML con la configuración de red.
        """
        self.config = self.load_config(config_path)

        # Configuración de Ethernet y Wi-Fi
        self.ethernet_config = self.config['network']['ethernet']
        self.wifi_config = self.config['network']['wifi']

    @staticmethod
    def load_config(config_path):
        """
        Carga la configuración desde un archivo YAML.

        :param config_path: Ruta al archivo YAML.
        :return: Diccionario con la configuración cargada.
        """
        with open(config_path, "r") as file:
            return yaml.safe_load(file)

    def configure_ethernet(self):
        """
        Configura la conexión Ethernet usando los parámetros del archivo YAML.
        """
        print("Configurando conexión Ethernet...")
        eth_config = f"""
auto eth0
iface eth0 inet static
    address {self.ethernet_config['ip']}
    netmask 255.255.255.0
    gateway {self.ethernet_config['gateway']}
        """
        self._write_network_config(eth_config)
        self.restart_network()
        print("Conexión Ethernet configurada.")

    def configure_wifi(self):
        """
        Configura la conexión Wi-Fi usando los parámetros del archivo YAML.
        """
        print("Configurando conexión Wi-Fi...")
        wifi_config = f"""
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
network={{
    ssid="{self.wifi_config['ssid']}"
    psk="{self.wifi_config['password']}"
    key_mgmt=WPA-PSK
}}
        """
        with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as file:
            file.write(wifi_config)
        subprocess.run(["wpa_cli", "-i", "wlan0", "reconfigure"], check=True)
        print("Conexión Wi-Fi configurada.")

    def check_connection(self):
        """
        Verifica la conexión a Internet intentando conectarse a un servidor externo.

        :return: True si la conexión es exitosa, False de lo contrario.
        """
        try:
            subprocess.run(["ping", "-c", "1", "8.8.8.8"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Conexión a Internet verificada.")
            return True
        except subprocess.CalledProcessError:
            print("No hay conexión a Internet.")
            return False

    @staticmethod
    def restart_network():
        """
        Reinicia los servicios de red para aplicar los cambios.
        """
        print("Reiniciando servicios de red...")
        subprocess.run(["sudo", "systemctl", "restart", "networking"], check=True)

    @staticmethod
    def _write_network_config(config):
        """
        Escribe la configuración de Ethernet en el archivo de interfaces.

        :param config: Configuración de red en formato string.
        """
        with open("/etc/network/interfaces", "w") as file:
            file.write(config)


# # Ejemplo de uso:

# #Configurar la conexión Ethernet y Wi-Fi

# from utils.networking import NetworkManager

# def main():
#     # Inicializar el administrador de red
#     network_manager = NetworkManager(config_path="config/pi1_config.yaml")

#     # Configurar Ethernet
#     network_manager.configure_ethernet()

#     # Configurar Wi-Fi
#     network_manager.configure_wifi()

#     # Verificar conexión a Internet
#     if network_manager.check_connection():
#         print("El dispositivo está conectado a Internet.")
#     else:
#         print("No hay conexión a Internet.")

# if __name__ == "__main__":
#     main()
