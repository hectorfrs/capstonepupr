# mux_manager.py - Clase para manejar dinámicamente el estado y la configuración del MUX.
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import logging
from smbus2 import SMBus
from lib.mux_controller import MUXController
from utils.alert_manager import AlertManager

@dataclass
class MUXConfig:
    i2c_bus: int
    i2c_address: int
    channels: List[Dict[str, int]] = field(default_factory=list)
class MUXManager:
    def __init__(self, i2c_bus: int, i2c_address: int, alert_manager: Optional[AlertManager] = None, config: Optional[Dict] = None):
        """
        Inicializa el MUXManager con la configuración del MUX.

        :param i2c_bus: Bus I2C del MUX.
        :param i2c_address: Dirección I2C del MUX.
        :param alert_manager: Instancia del AlertManager para manejar alertas (opcional)
        :param config: Configuración del MUX (opcional)
        """
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.alert_manager = alert_manager
        self.bus = SMBus(i2c_bus)
        self.mux = MUXController(i2c_bus=self.i2c_bus, i2c_address=self.i2c_address)
        self.status = {}
        logging.info(f"MUX conectado en I2C Bus: {self.i2c_bus}, Dirección: {hex(self.i2c_address)}.")
        if isinstance(config, dict):
            #config_mux = config.get('mux', {})
            #config_mux.pop('active_channels', None)  # Elimina active_channels si existe
            self.config = MUXConfig(**config['mux'])
        else:
            self.config = config if config else MUXConfig(i2c_bus=i2c_bus, i2c_address=i2c_address)
        self.mux = MUXController(i2c_bus=self.i2c_bus, i2c_address=self.i2c_address)
        logging.info(f"MUX conectado en I2C Bus: {self.i2c_bus}, Dirección: {hex(self.i2c_address)}.")
        try:
            logging.info("MUX inicializado correctamente.")
        except Exception as e:
            logging.critical(f"Error inicializando el MUX: {e}")
            if alert_manager:
                alert_manager.send_alert(
                    level="CRITICAL",
                    message="Error inicializando el MUX.",
                    metadata={"error": str(e)}
                )
            raise

    def validate_connection(self):
        """
        Valida que el MUX esté conectado y funcionando.
        """
        try:
            if hasattr(self.mux, "validate_connection"):
                self.mux.validate_connection()  # Método estándar
                logging.info("MUX está accesible y conectado.")
            else:
                # Fallback a un registro específico si no hay validate_connection
                self.mux.read_register(0x00)  # Ejemplo: lectura de un registro base
                logging.info("MUX está accesible al leer un registro.")
        except Exception as e:
            logging.critical(f"No se pudo conectar al MUX: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="CRITICAL",
                    message="Error conectando al MUX.",
                    metadata={"error": str(e)}
                )
            raise RuntimeError("MUX no está conectado o no responde.")

    def is_mux_connected(self):
        """
        Verifica si el MUX está accesible.
        """
        try:
            self.bus.read_byte(self.i2c_address)
            logging.info(f"MUX conectado en I2C Bus: {self.i2c_bus}, Dirección: {hex(self.i2c_address)}.")
            return True
        except Exception as e:
            logging.error(f"Error verificando conexión del MUX: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="CRITICAL",
                    message="MUX no accesible.",
                    metadata={"error": str(e)},
                )
            return False

    def select_channel(self, channel: int):
        """
        Selecciona un canal en el MUX.
        :param channel: Número del canal (0-7).
        """
        try:
            if not (0 <= channel <= 7):
                raise ValueError(f"Canal {channel} fuera de rango (0-7).")
            self.bus.write_byte(self.i2c_address, 1 << channel)
            self.status[channel] = True
            logging.info(f"Canal {channel} activado en el MUX.")
        except ValueError as ve:
            logging.error(f"Error de valor: {ve}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="ERROR",
                    message=f"Error de valor activando canal {channel}",
                    metadata={"channel": channel, "error": str(ve)},
                )
        except Exception as e:
            logging.error(f"Error activando canal {channel}: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="CRITICAL",
                    message=f"Error activando canal {channel}",
                    metadata={"channel": channel, "error": str(e)},
                )

    def disable_all_channels(self):
        """
        Desactiva todos los canales del MUX.
        """
        try:
            self.bus.write_byte(self.i2c_address, 0x00)
            self.status = {channel: False for channel in range(8)}
            logging.info("Todos los canales del MUX desactivados.")
        except Exception as e:
            logging.error(f"Error desactivando todos los canales: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="WARNING",
                    message="Error desactivando todos los canales del MUX.",
                    metadata={"error": str(e)},
                )

    def get_status(self):
        """
        Obtiene el estado actual de los canales del MUX.

        :return: Diccionario con el estado de cada canal.
        """
        try:
            channel_states = self.mux.get_channel_states()
            status = {channel: bool(channel_states & (1 << channel)) for channel in range(8)}
            logging.info(f"Estado del MUX: {status}")
            return status
        except Exception as e:
            logging.error(f"Error obteniendo estado del MUX: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="ERROR",
                    message="Error obteniendo estado del MUX.",
                    metadata={"error": str(e)}
                )
            return {}

    def reset_channel(self, channel: int):
        """
        Reinicia un canal específico del MUX.

        :param channel: Canal a reiniciar.
        """
        try:
            self.disable_all_channels()
            self.select_channel(channel)
            logging.info(f"Canal {channel} reiniciado en el MUX.")
        except Exception as e:
            logging.error(f"Error reiniciando canal {channel}: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="WARNING",
                    message=f"Error reiniciando canal {channel} en el MUX.",
                    metadata={"channel": channel, "error": str(e)}
                )

    def detect_active_channels(self):
        detected_channels = []
        for channel in self.channels:
            try:
                self.select_channel(channel["channel"])
                if self.verify_sensor_on_channel(channel["channel"]):
                    detected_channels.append(channel["channel"])
                    logging.info(f"Canal {channel['channel']} activo con sensor {channel['sensor_name']}.")
                else:
                    logging.warning(f"Canal {channel['channel']} no tiene sensor.")
            except Exception as e:
                logging.error(f"Error verificando canal {channel['channel']}: {e}")
        self.disable_all_channels()
        return detected_channels


    def run_diagnostics(self):
        """
        Ejecuta diagnósticos básicos en el MUX.

        :return: Diccionario indicando si cada canal está funcional.
        """
        diagnostics = {}
        try:
            diagnostics = self.mux.run_diagnostics()
            logging.info(f"Resultados del diagnóstico del MUX: {diagnostics}")
        except Exception as e:
            logging.error(f"Error ejecutando diagnósticos del MUX: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="ERROR",
                    message="Error en los diagnósticos del MUX.",
                    metadata={"error": str(e)}
                )
        return diagnostics
    
    def initialize_mux(config, alert_manager):
        try:
            # Elimina "active_channels" si está presente
            mux_config_data = {k: v for k, v in config['mux'].items() if k != 'active_channels'}
            mux_config = MUXConfig(**mux_config_data)

            i2c_address = int(config['mux']['i2c_address'], 16) if isinstance(config['mux']['i2c_address'], str) else config['mux']['i2c_address']
            mux_manager = MUXManager(i2c_bus=mux_config.i2c_bus, i2c_address=i2c_address, alert_manager=alert_manager)

            if not mux_manager.is_mux_connected():
                raise RuntimeError("MUX no conectado o no accesible.")

            logging.info("MUX inicializado correctamente.")
            return mux_manager
        except Exception as e:
            logging.critical(f"Error inicializando el MUX: {e}", exc_info=True)
            alert_manager.send_alert(
                level="CRITICAL",
                message="Error inicializando el MUX.",
                metadata={"error": str(e)}
            )
            raise


    def is_channel_active(self, channel: int):
        """
        Verifica si un canal específico está activo en el MUX.

        :param channel: Número del canal (0-7).
        :return: True si el canal está activo, False en caso contrario.
        """
        return self.mux.is_channel_active(channel)
        
    def verify_sensor_on_channel(self, channel: int):
        """
        Verifica si un sensor está conectado en el canal especificado.

        :param channel: Canal a verificar.
        :return: True si el sensor está conectado, False en caso contrario.
        """
        try:
            self.select_channel(channel)
            # Verifica un registro específico del sensor que confirme la conexión
            sensor_response = self.mux.read_register(0x00)  # Cambia 0x00 por un registro válido
            return sensor_response is not None
        except Exception as e:
            logging.error(f"Error verificando sensor en canal {channel}: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="ERROR",
                    message=f"Error verificando sensor en canal {channel}",
                    metadata={"channel": channel, "error": str(e)}
                )
            return False
        finally:
            self.disable_all_channels()