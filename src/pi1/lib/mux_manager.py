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
        logging.info(f"MUX se encuentra en I2C Bus: {self.i2c_bus}, Dirección: {hex(self.i2c_address)}.")
        if isinstance(config, dict):
            #config_mux = config.get('mux', {})
            #config_mux.pop('active_channels', None)  # Elimina active_channels si existe
            self.config = MUXConfig(**config['mux'])
        else:
            self.config = config if config else MUXConfig(i2c_bus=i2c_bus, i2c_address=i2c_address)
            self.mux = MUXController(i2c_bus=self.i2c_bus, i2c_address=self.i2c_address)
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

    def initialize_channels(self, channels: List[int]):
        """
        Inicializa los canales especificados para el MUX.

        :param channels: Lista de números de canal a inicializar.
        """
        try:
            for id in channels:
                if not (0 <= id <= 7):  # Verificar que el canal esté en el rango permitido
                    raise ValueError(f"Canal {id} fuera de rango (0-7).")
                # Registrar el estado del canal
                self.select_channel(id)
                logging.info(f"Canal {id} inicializado correctamente.")
            # Desactivar todos los canales después de la inicialización
            self.disable_all_channels()
        except Exception as e:
            logging.error(f"Error inicializando canales: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="CRITICAL",
                    message="Error inicializando canales del MUX.",
                    metadata={"error": str(e)},
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

    def select_channel(self, id: int):
        """
        Selecciona un canal en el MUX.
        :param channel: Número del canal (0-7).
        """
        try:
            if not (0 <= channel_id <= 7):
                raise ValueError(f"ID del canal {channel_id} fuera de rango (0-7).")
            self.bus.write_byte(self.i2c_address, 1 << channel_id)
            logging.info(f"Canal {channel_id} activado en el MUX.")
        except ValueError as ve:
            logging.error(f"Error de valor: {ve}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="ERROR",
                    message=f"Error de valor activando canal {id}",
                    metadata={"channel": id, "error": str(ve)},
                )
        except Exception as e:
            logging.error(f"Error activando canal {channel_id}: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="CRITICAL",
                    message=f"Error activando canal {id} en el MUX.",
                    metadata={"channel": id, "error": str(e)},
                )
            raise

    def disable_all_channels(self):
        """
        Desactiva todos los canales del MUX.
        """
        try:
            self.bus.write_byte(self.i2c_address, 0x00)
            self.status = {id: False for id in range(8)}
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
        try:
            logging.info("Estado del MUX consultado, pero omitido por diseño.")
            return {}
        except Exception as e:
            logging.error(f"Error obteniendo estado del MUX: {e}")


    def reset_channel(self, id: int):
        """
        Reinicia un canal específico del MUX.

        :param channel: Canal a reiniciar.
        """
        try:
            self.disable_all_channels()
            self.select_channel(id)
            logging.info(f"Canal {id} reiniciado en el MUX.")
        except Exception as e:
            logging.error(f"Error reiniciando canal {id}: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="WARNING",
                    message=f"Error reiniciando canal {id} en el MUX.",
                    metadata={"channel": id, "error": str(e)}
                )

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
    
    def is_channel_active(self, id: int):
        """
        Verifica si un canal específico está activo en el MUX.

        :param channel: Número del canal (0-7).
        :return: True si el canal está activo, False en caso contrario.
        """
        return self.mux.is_channel_active(id)
        
    def verify_sensor_on_channel(self, id: int):
        """
        Verifica si un sensor está conectado en el canal especificado.

        :param channel: Canal a verificar.
        :return: True si el sensor está conectado, False en caso contrario.
        """
        try:
            self.select_channel(id)
            # Verifica un registro específico del sensor que confirme la conexión
            sensor_response = self.mux.read_register(0x00)  # Cambia 0x00 por un registro válido
            return sensor_response is not None
        except Exception as e:
            logging.error(f"Error verificando sensor en canal {id}: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="ERROR",
                    message=f"Error verificando sensor en canal {id}",
                    metadata={"channel": id, "error": str(e)}
                )
            return False
        finally:
            self.disable_all_channels()