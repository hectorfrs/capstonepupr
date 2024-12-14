# TCA9548A_Controller.py - Clase para manejar el MUX TCA9548A utilizando la librería Qwiic.
# Desarrollado por Héctor F. Rivera Santiago
# copyright (c) 2024

import qwiic_tca9548a
from smbus2 import SMBus
import time
import logging
import sys

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class MUX_TCA9548A:
    """Clase para manejar el MUX TCA9548A utilizando la librería Qwiic & SMBus."""
    
    POLLING_DELAY = 0.05 # Retardo de polling en segundos

    def __init__(self, address=0x70, i2c_bus=1):
        """
        Inicializa el MUX TCA9548A.
        :param address: Dirección I2C del MUX.
        :param i2c_bus: Número del bus I2C (por defecto: 1).
        """
        self.address = address
        self.bus = SMBus(i2c_bus)

        try:
            logging.debug(f"[CONTROLLER] [MUX] Intentando conectar a la dirección {hex(self.address)} en el bus {i2c_bus}.")
            self.bus.read_byte(self.address)
            logging.info(f"[CONTROLLER] [MUX] TCA9548A conectado en la dirección {hex(self.address)}.")
        except Exception as e:
            logging.error(f"[CONTROLLER] [MUX] No se puede conectar a {hex(self.address)}: {e}")
            raise

    def enable_channel(self, channel):
        """
        Habilita un canal en el MUX.
        :param channel: Canal a habilitar (0-7).
        """
        logging.debug(f"[CONTROLLER] [MUX] Intentando habilitar el canal {channel}.")
        if not (0 <= channel <= 7):
            logging.error(f"[CONTROLLER] [MUX] Canal inválido: {channel}.")
            raise ValueError("El canal debe estar entre 0 y 7.")
        try:
            self.bus.write_byte(self.address, 1 << channel)
            logging.info(f"[CONTROLLER] [MUX] Canal {channel} habilitado en el MUX.")
        except Exception as e:
            logging.error(f"[CONTROLLER] [MUX] Error al habilitar el canal {channel} en el MUX: {str(e)}")
            raise

    def disable_channel(self, channel):
        """
        Deshabilita un canal en el MUX escribiendo 0 en su máscara.
        :param channel: Canal a deshabilitar (0-7).
        """
        logging.debug(f"[CONTROLLER] [MUX] Intentando deshabilitar el canal {channel}.")
        raise NotImplementedError("La deshabilitación individual no es soportada por el MUX TCA9548A.")
    
    def enable_multiple_channels(self, channels):
        """
        Habilita múltiples canales en el MUX.
        :param channels: Lista de canales a habilitar (0-7).
        """
        logging.debug(f"[CONTROLLER] [MUX] Intentando habilitar múltiples canales: {channels}.")
        mask = 0
        for channel in channels:
            if not 0 <= channel <= 7:
                raise ValueError(f"Canal inválido: {channel}. Debe estar entre 0 y 7.")
            mask |= 1 << channel  # Agregar el canal a la máscara
        try:
            self.bus.write_byte(self.address, mask)  # Escribir la máscara en el MUX
            #logging.info(f"Canales {channels} habilitados en el MUX con máscara {bin(mask)}.")
        except Exception as e:
            logging.error(f"[CONTROLLER] [MUX] Error al habilitar múltiples canales {channels} en el MUX: {e}")
            raise
    
    def select_channel(self, channel):
        logging.debug(f"[CONTROLLER] [MUX] Seleccionando canal {channel}.")
        if channel < 0 or channel > 7:
            logging.error(f"[CONTROLLER] [MUX] Canal inválido: {channel}.")
            raise ValueError("El canal debe estar entre 0 y 7.")
        try:
            self.i2c_bus.write_byte(self.address, 1 << channel)
            logging.info(f"[CONTROLLER] [MUX] Canal {channel} seleccionado correctamente.")
        except Exception as e:
            logging.error(f"[CONTROLLER] [MUX] Error al seleccionar canal {channel}: {e}")
            raise


    def disable_all_channels(self):
        """
        Deshabilita todos los canales del MUX escribiendo 0x00 en el registro de control.
        """
        logging.debug("[CONTROLLER] [MUX] Intentando deshabilitar todos los canales.")
        try:
            self.bus.write_byte(self.address, 0x00)
            logging.info("[CONTROLLER] [MUX] Todos los canales deshabilitados en el MUX.")
            time.sleep(1)  # Pausa adicional para estabilización
        except Exception as e:
            logging.error(f"[CONTROLLER] [MUX] Error al deshabilitar todos los canales en el MUX: {e}")
            raise

    def get_active_channels(self):
        """
        Devuelve los canales actualmente activos en el MUX.
        :return: Lista de canales activos (0-7).
        """
        logging.debug("[CONTROLLER] [MUX] Leyendo canales activos.")
        status = self.read_control_register()
        active_channels = [i for i in range(8) if status & (1 << i)]
        logging.info(f"[CONTROLLER] [MUX] Canales activos: {active_channels}.")
        return active_channels

    def read_control_register(self):
        """
        Lee el registro de control del MUX para determinar los canales activos.
        :return: Byte que representa el estado de los canales activos.
        """
        logging.debug("[CONTROLLER] [MUX] Leyendo registro de control.")
        try:
            status = self.bus.read_byte(self.address)  # Dirección del MUX
            logging.debug(f"[CONTROLLER] [MUX] Registro de control leído: {bin(status)}.")
            return status
        except Exception as e:
            logging.error(f"[CONTROLLER] [MUX] Error al leer el registro de control del MUX: {e}")
            raise

    def reset(self):
        """
        Resetea el MUX escribiendo 0x00 en el registro de control.
        """
        logging.debug("[CONTROLLER] [MUX] Reseteando el MUX.")
        try:
            self.bus.write_byte(self.address, 0x00)
            logging.info("[CONTROLLER] [MUX] MUX reseteado y todos los canales deshabilitados.")
        except Exception as e:
            logging.error(f"[CONTROLLER] [MUX] Error al resetear el MUX: {e}")
            raise