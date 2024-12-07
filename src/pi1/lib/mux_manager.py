# mux_manager.py - Clase para manejar dinámicamente el estado y la configuración del MUX.
import logging
from lib.mux_controller import MUXController
from utils.alert_manager import AlertManager

class MUXManager:
    def __init__(self, i2c_bus, i2c_address, alert_manager=None):
        """
        Inicializa el MUXManager con la configuración del MUX.
        """
        try:
            self.mux = MUXController(i2c_bus=i2c_bus, i2c_address=i2c_address)
            self.alert_manager = alert_manager
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
        :return: True si el MUX responde, False en caso contrario.
        """
        try:
            self.mux.validate_connection()
            logging.info("MUX está accesible.")
            return True
        except Exception as e:
            logging.error(f"Error verificando conexión del MUX: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="CRITICAL",
                    message="MUX no accesible.",
                    metadata={"error": str(e)}
                )
            return False

    def select_channel(self, channel):
        """
        Selecciona un canal en el MUX.
        """
        try:
            self.mux.select_channel(channel)
        except Exception as e:
            logging.error(f"Error seleccionando el canal {channel}: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="ERROR",
                    message=f"Error seleccionando canal {channel}",
                    metadata={"channel": channel, "error": str(e)}
                )
            raise                            

    def disable_all_channels(self):
        """
        Desactiva todos los canales.
        """
        try:
            self.mux.disable_all_channels()
            logging.info("Todos los canales del MUX han sido desactivados.")
        except Exception as e:
            logging.error(f"Error desactivando todos los canales: {e}")

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

    def reset_channel(self, channel):
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
        """
        Detecta canales activos verificando sensores.
        """
        active_channels = []
        for channel in range(8):  # Iterar sobre 8 canales
            try:
                self.mux.select_channel(channel)
                if self.mux.verify_sensor_connection():
                    active_channels.append(channel)
                    logging.info(f"Sensor detectado en el canal {channel}.")
                else:
                    logging.warning(f"No se detectó sensor en el canal {channel}.")
            except Exception as e:
                logging.error(f"Error verificando el canal {channel}: {e}")
                if self.alert_manager:
                    self.alert_manager.send_alert(
                        level="WARNING",
                        message=f"Error verificando canal {channel}",
                        metadata={"channel": channel, "error": str(e)}
                    )
            finally:
                self.mux.disable_all_channels()
        return active_channels

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

    def is_channel_active(self, channel):
        """
        Verifica si un canal específico está activo en el MUX.

        :param channel: Número del canal (0-7).
        :return: True si el canal está activo, False en caso contrario.
        """
        return self.mux.is_channel_active(channel)

