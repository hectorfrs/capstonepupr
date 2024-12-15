# TCA9548A High Level - Clase de alto nivel para el MUX TCA9548A.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024

import logging
import time
from classes.TCA9548A_Controller_v1 import MUX_TCA9548A

# Configurar logging para el manejo de nivel alto
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

class TCA9548A_Manager:
    """
    Manejo de alto nivel para el MUX TCA9548A.
    Este archivo abstrae las operaciones comunes como habilitar/deshabilitar canales.
    """

    def __init__(self, address=0x70, i2c_bus=1):
        """
        Inicializa el controlador de alto nivel para el MUX TCA9548A.
        :param address: Dirección I²C del MUX.
        """
        self.i2c_bus = i2c_bus
        self.address = address
        try:
            self.mux = MUX_TCA9548A(address=address, i2c_bus=i2c_bus)
            # Aquí puedes inicializar el objeto mux según tu lógica
            # Por ejemplo, si tienes otro objeto que controla el MUX, asígnalo aquí
            logging.info(f"[CONTROLLER] [MUX] MUX TCA9548A inicializado en la dirección {address}.")
        except Exception as e:
            logging.critical(f"[CONTROLLER] [MUX] Error inicializando el MUX: {e}")
            raise

    def enable_channel(self, channel):
        """
        Habilita un canal específico en el MUX.
        :param channel: Canal a habilitar (0-7).
        """
        try:
            self.mux.enable_channel(channel)
            logging.info(f"[MANAGER] [MUX] [CANAL {channel}] Habilitado.")
            time.sleep(2)
        except Exception as e:
            logging.error(f"[MANAGER] [MUX] Error al habilitar el canal {channel}: {e}")

    def disable_channel(self, channel):
        """
        Deshabilita un canal específico en el MUX.
        :param channel: Canal a deshabilitar (0-7).
        """
        self.mux.disable_channel(channel)
        logging.info(f"[MANAGER] [MUX] [CANAL {channel}] Deshabilitado.")

    def enable_multiple_channels(self, channels):
        """
        Habilita múltiples canales en el MUX.
        :param channels: Lista de canales a habilitar (0-7).
        """
        self.mux.enable_multiple_channels(channels)
        logging.info(f"[MANAGER] [MUX] Canales {channels} habilitados.")

    def disable_all_channels(self):
        """
        Deshabilita todos los canales del MUX.
        """
        self.mux.disable_all_channels()
        logging.info("[MANAGER] [MUX] Todos los canales deshabilitados.")

    def get_active_channel(self):
        """
        Devuelve los canales actualmente activos en el MUX.
        :return: Lista de canales activos (0-7).
        """
        status = self.mux.read_control_register()  # Leer el registro de control
        active_channels = [i for i in range(8) if status & (1 << i)]
        logging.info(f"[MANAGER] [MUX] Canales activos: {active_channels}")
        return active_channels



