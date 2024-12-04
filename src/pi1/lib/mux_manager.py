import logging
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

    def select_channel(self, channel):
        """
        Selecciona un canal en el MUX y maneja excepciones.

        :param channel: Número del canal a activar.
        """
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
        Desactiva todos los canales del MUX.
        """
        try:
            self.mux.disable_all_channels()
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
