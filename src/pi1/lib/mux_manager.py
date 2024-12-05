# mux_manager.py - Clase para manejar dinámicamente el estado y la configuración del MUX.
import logging
from smbus2 import SMBus
from lib.mux_controller import MUXController
from utils.alert_manager import AlertManager


class MUXManager:
    """
    Clase para manejar dinámicamente el estado y la configuración del MUX.
    """
    def __init__(self, i2c_bus, i2c_address, alert_manager=None):
        """
        Inicializa el manejador del MUX.

        :param i2c_bus: Bus I2C del MUX.
        :param i2c_address: Dirección I2C del MUX.
        :param alert_manager: Instancia del AlertManager para manejar alertas (opcional).
        """
        self.mux = MUXController(i2c_bus=i2c_bus, i2c_address=i2c_address)
        self.alert_manager = alert_manager
        self.bus = SMBus(i2c_bus)

    def is_mux_connected(self):
        """
        Verifica si el MUX está accesible.
        :return: True si el MUX responde, False en caso contrario.
        """
        try:
            self.mux.get_status()
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
        Selecciona un canal en el MUX y maneja excepciones.

        :param channel: Número del canal a activar.
        """
        if channel is not None and (channel < 0 or channel >= 8):
            raise ValueError(f"Canal inválido: {channel}")
        try:
            self.mux.select_channel(channel)
            logging.info(f"Canal {channel} activado en el MUX.")
        except Exception as e:
            logging.error(f"Error activando canal {channel} en el MUX: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="CRITICAL",
                    message=f"Error activando canal {channel} en el MUX.",
                    metadata={"channel": channel, "error": str(e)}
                )
            raise

    def disable_all_channels(self):
        """
        Desactiva todos los canales del MUX de manera explícita.
        """
        try:
            for channel in range(8):  # Iterar sobre los 8 canales
                self.mux.select_channel(channel)  # Activar canal
                self.mux.select_channel(None)  # Desactivar canal
            logging.info("Todos los canales del MUX han sido desactivados.")
        except Exception as e:
            logging.error(f"Error desactivando todos los canales en el MUX: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="WARNING",
                    message="Error desactivando todos los canales en el MUX.",
                    metadata={"error": str(e)}
                )

    def get_status(self):
        """
        Obtiene el estado actual de los canales del MUX.

        :return: Diccionario con el estado de cada canal.
        """
        try:
            status = {channel: self.mux.is_channel_active(channel) for channel in range(8)}
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
            Detecta los canales activos del MUX probando cada canal.

            :return: Lista de canales con sensores conectados.
            """
            active_channels = []
            for channel in range(8):  # El MUX tiene 8 canales
                try:
                    # Activar canal
                    self.mux.select_channel(channel)
                    # Intentar leer algún dispositivo en este canal
                    self.bus.read_byte(self.mux.i2c_address)
                    active_channels.append(channel)
                    logging.info(f"Dispositivo detectado en el canal {channel}.")
                except FileNotFoundError:
                        logging.error(f"No se encontró el dispositivo I2C en el canal {channel}.")
                except OSError:
                    # No hay dispositivo conectado en este canal
                    logging.info(f"No se detectó dispositivo en el canal {channel}.")
                except Exception as e:
                    logging.error(f"Error detectando canal {channel}: {e}")
                    if self.alert_manager:
                        self.alert_manager.send_alert(
                            level="WARNING",
                            message=f"Error detectando canal {channel}",
                            metadata={"channel": channel, "error": str(e)}
                        )
            # Desactivar todos los canales después de la detección
            self.disable_all_channels()
            return active_channels

    def run_diagnostics(self):
        """
        Ejecuta diagnósticos básicos en el MUX.
        :return: Diccionario indicando si cada canal está funcional.
        """
        diagnostics = {}
        for channel in range(8):
            try:
                self.select_channel(channel)
                diagnostics[channel] = True
            except Exception as e:
                diagnostics[channel] = False
                logging.error(f"Error en el canal {channel} durante el diagnóstico: {e}")
                if self.alert_manager:
                    self.alert_manager.send_alert(
                        level="ERROR",
                        message=f"Error en el diagnóstico del canal {channel}.",
                        metadata={"channel": channel, "error": str(e)}
                    )
        self.disable_all_channels()
        logging.info(f"Resultados del diagnóstico del MUX: {diagnostics}")
        return diagnostics
