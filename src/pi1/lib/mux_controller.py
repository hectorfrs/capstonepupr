# mux_controller.py - Clase para controlar el MUX Qwiic TCA9548A.
import logging
import yaml
import qwiic_tca9548a
from smbus2 import SMBus

class MUXController:
    """
    Clase para controlar el MUX Qwiic TCA9548A.
    """
    def __init__(self, i2c_bus, i2c_address):
        """
        Inicializa el controlador del MUX.

        :param i2c_bus: Bus I2C donde está conectado el MUX.
        :param i2c_address: Dirección I2C del MUX.
        """
        self.i2c_address = i2c_address
        self.bus = SMBus(i2c_bus)  # Inicializar el bus I2C

        # Inicializar el MUX
        self.mux = qwiic_tca9548a.QwiicTCA9548A(address=self.i2c_address)
        if not self.mux.connected:
            raise ConnectionError(f"El MUX con dirección {hex(self.i2c_address)} no está conectado.")
        logging.info(f"MUX conectado en la dirección {hex(self.i2c_address)}.")

    def select_channel(self, channel):
        """
        Activa un canal específico en el MUX.

        :param channel: Número del canal a activar (0-7).
        """
        if channel < 0 or channel > 7:
            raise ValueError("El canal debe estar entre 0 y 7.")
        self.mux.enable_channels(1 << channel)  # Activa el canal
        logging.info(f"Canal {channel} activado en el MUX.")

    def disable_all_channels(self):
        """
        Desactiva todos los canales del MUX.
        """
        self.mux.disable_channels()
        logging.info("Todos los canales desactivados en el MUX.")


    def detect_active_channels(self):
        """
        Detecta canales activos intentando comunicarse con dispositivos conectados.
        
        :return: Lista de canales con dispositivos conectados.
        """
        active_channels = []
        for channel in range(8):
            try:
                self.select_channel(channel)
                self.bus.read_byte(self.i2c_address)  # Prueba de lectura
                active_channels.append(channel)
            except OSError:
                pass  # Canal inactivo
        self.disable_all_channels()
        return active_channels

    def run_diagnostics(self):
        """
        Ejecuta un diagnóstico básico activando cada canal.

        :return: Diccionario indicando si cada canal responde.
        """
        diagnostics = {}
        for channel in range(8):
            try:
                self.select_channel(channel)
                diagnostics[channel] = True
            except Exception:
                diagnostics[channel] = False
        self.disable_all_channels()
        return diagnostics

    def validate_connection(self):
        """
        Valida si el MUX está conectado.
        """
        if not self.mux.connected:
            raise ConnectionError(f"El MUX con dirección {hex(self.i2c_address)} ha perdido la conexión.")
    
    def is_channel_active(self, channel):
        """
        Verifica si un canal específico está activo en el MUX.

        :param channel: Número del canal (0-7).
        :return: True si el canal está activo, False en caso contrario.
        """
        if channel < 0 or channel > 7:
            raise ValueError("El canal debe estar entre 0 y 7.")

        # Obtener el estado de los canales habilitados
        enabled_channels = self.mux.get_channels_enabled()

        # Verificar si el bit correspondiente al canal está habilitado
        return bool(enabled_channels & (1 << channel))
