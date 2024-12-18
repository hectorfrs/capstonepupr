import os
import subprocess

class Networking:
    """
    Clase para manejar la conexión de red en un Raspberry Pi, priorizando LAN (Ethernet) y
    utilizando Wi-Fi como respaldo. Este enfoque asegura que el dispositivo siempre intente
    mantenerse conectado a Internet.
    """
    def __init__(self, lan_config, wifi_config):
        """
        Inicializa las configuraciones de red.

        :param lan_config: Diccionario con configuración de LAN (IP estática y gateway).
        :param wifi_config: Diccionario con configuración de Wi-Fi (SSID, password, IP y gateway).
        """
        self.lan_config = lan_config
        self.wifi_config = wifi_config
        print("Configuración de Networking inicializada.")

    def check_connection(self, interface):
        """
        Verifica si hay conexión a Internet desde una interfaz específica utilizando 'ping'.

        :param interface: Nombre de la interfaz de red (ejemplo: 'eth0' para LAN, 'wlan0' para Wi-Fi).
        :return: True si hay conexión, False de lo contrario.
        """
        print(f"Comprobando conexión a Internet en la interfaz {interface}...")
        try:
            # Comando 'ping' para verificar conectividad con un servidor externo
            result = subprocess.run(
                ["ping", "-c", "1", "-I", interface, "8.8.8.8"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if result.returncode == 0:
                print(f"Conexión establecida a través de {interface}.")
                return True
            else:
                print(f"No se pudo conectar a través de {interface}.")
                return False
        except Exception as e:
            print(f"Error al verificar conexión en {interface}: {e}")
            return False

    def configure_wifi(self):
        """
        Configura la conexión Wi-Fi utilizando el comando 'nmcli'.

        :return: True si la conexión es exitosa, False de lo contrario.
        """
        print("Intentando conectar a la red Wi-Fi...")
        try:
            # Usar nmcli para conectarse al SSID especificado
            os.system(f'nmcli dev wifi connect "{self.wifi_config["ssid"]}" password "{self.wifi_config["password"]}"')
            # Verificar conexión en la interfaz Wi-Fi
            if self.check_connection("wlan0"):
                print("Conexión Wi-Fi exitosa.")
                return True
            else:
                print("No se pudo establecer conexión Wi-Fi.")
                return False
        except Exception as e:
            print(f"Error al conectar a Wi-Fi: {e}")
            return False

    def ensure_connection(self):
        """
        Garantiza que el dispositivo esté conectado a Internet. Prioriza la conexión LAN (Ethernet)
        y utiliza Wi-Fi como respaldo si LAN no está disponible.

        :return: True si hay conexión, False de lo contrario.
        """
        print("Iniciando proceso para garantizar conectividad a Internet...")

        # Verificar conexión LAN
        if self.check_connection("eth0"):
            print("Conexión LAN activa. No es necesario usar Wi-Fi.")
            return True

        # Intentar conexión Wi-Fi si LAN falla
        if self.configure_wifi():
            print("Conexión Wi-Fi activa como respaldo.")
            return True

        # Si ambos fallan
        print("Error: No se pudo establecer ninguna conexión de red.")
        return False
