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
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        try:
            self.i2c = smbus.SMBus(self.i2c_bus)
            logging.info(f"Bus I2C {self.i2c_bus} inicializado correctamente.")
        except Exception as e:
            logging.error(f"Error inicializando el bus I2C: {e}")
            raise

    def select_channel(self, channel):
        """
        Selecciona un canal en el MUX.

        :param channel: Canal a activar (0-7).
        """
        try:
            if channel is None:
                self.disable_all_channels()
            elif 0 <= channel <= 7:
                self.i2c.write_byte_data(self.i2c_address, 0x00, 1 << channel)
                logging.info(f"Canal {channel} activado en el MUX.")
            else:
                raise ValueError("Canal fuera del rango permitido (0-7)")
        except Exception as e:
            logging.error(f"Error activando el canal {channel} en el MUX: {e}")
            raise

    def disable_all_channels(self):
        """
        Desactiva todos los canales del MUX.
        """
        try:
            self.i2c.write_byte_data(self.i2c_address, 0x00, 0x00)
            logging.info("Todos los canales desactivados en el MUX.")
        except Exception as e:
            logging.error(f"Error desactivando todos los canales en el MUX: {e}")
            raise

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
        Verifica si un canal específico está activo en el MUX probando comunicación.

        :param channel: Número del canal (0-7).
        :return: True si el canal está activo, False en caso contrario.
        """
        if channel < 0 or channel > 7:
            raise ValueError("El canal debe estar entre 0 y 7.")
        
        try:
            self.select_channel(channel)
            # Prueba de lectura para verificar si el canal es funcional
            self.bus.read_byte(self.i2c_address)
            return True
        except OSError:
            # Canal no funcional
            return False
        finally:
            self.disable_all_channels()

    def verify_sensor_connection(self):
        """
        Verifica si un sensor está conectado en el canal activo del MUX.

        :return: True si el sensor responde, False si no.
        """
        SENSOR_I2C_ADDRESS = 0x49  # Dirección estándar del sensor AS7265x
        HW_VERSION_REGISTER = 0x00  # Registro que contiene la versión de hardware

        try:
            hw_version = self.i2c.read_byte_data(SENSOR_I2C_ADDRESS, HW_VERSION_REGISTER)
            logging.info(f"Conexión al sensor detectada, versión de hardware: {hw_version}")
            return hw_version is not None
        except Exception as e:
            logging.error(f"No se detecta sensor en el canal activo: {e}")
            return False

