# mux_manager.py - Clase para manejar dinámicamente el estado y la configuración del MUX.
import logging
from lib.mux_controller import MUXController
from utils.alert_manager import AlertManager
from unittest.mock import Mock



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
        self.mock = mock
        if mock:
            self.mux = Mock()  # Simula la instancia del MUXController para pruebas
            logging.info("Inicializando MUX en modo simulación (mock).")
        else:
            self.mux = MUXController(i2c_bus=i2c_bus, i2c_address=i2c_address)
            self.alert_manager = alert_manager
            self.status = {}

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

        :param channel: Número del canal a activar (0-7) o None para desactivar todos.
        """
        try:
            self.mux.select_channel(channel)
            logging.info(f"Canal {channel if channel is not None else 'None'} activado en el MUX.")
        except Exception as e:
            logging.error(f"Error activando canal {channel}: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="CRITICAL",
                    message=f"Error activando canal {channel}.",
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
            logging.error(f"Error desactivando todos los canales: {e}")
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
        Detecta los canales activos del MUX probando cada canal y verificando sensores.

        :return: Lista de canales activos con sensores válidos.
        """
        active_channels = []
        for channel in range(8):  # Iterar sobre los 8 canales posibles
            try:
                self.select_channel(channel)
                if self.mux.is_channel_active(channel):
                    # Aquí puedes agregar lógica para verificar si un sensor responde en este canal
                    sensor_response = self.verify_sensor_on_channel(channel)  # Nueva función
                    if sensor_response:
                        active_channels.append(channel)
                        logging.info(f"Canal {channel} activo y sensor detectado en el MUX.")
                    else:
                        logging.warning(f"Canal {channel} activo, pero sin sensor detectado.")
                else:
                    logging.info(f"Canal {channel} no activo en el MUX.")
            except Exception as e:
                logging.error(f"Error detectando canal {channel}: {e}")
                if self.alert_manager:
                    self.alert_manager.send_alert(
                        level="WARNING",
                        message=f"Error detectando canal {channel}",
                        metadata={"channel": channel, "error": str(e)},
                    )
        self.disable_all_channels()
        return active_channels

    def verify_sensor_on_channel(self, channel):
        """
        Verifica si hay un sensor funcional en el canal activo.

        :param channel: Canal a verificar.
        :return: True si el sensor responde, False en caso contrario.
        """
        try:
            # Seleccionar canal en el MUX
            self.select_channel(channel)

            # Leer el registro HW_VERSION del sensor AS7265x
            hw_version = self.mux.read_register(0x3F)
            if hw_version:  # Verifica que el valor no sea nulo o inválido
                logging.info(f"Sensor detectado en canal {channel}. Versión HW: {hw_version}")
                return True
            else:
                logging.warning(f"No se detectó respuesta del sensor en canal {channel}.")
                return False
        except Exception as e:
            logging.error(f"Error verificando sensor en canal {channel}: {e}")
            return False
        finally:
        # Desactivar el canal para evitar conflictos
            self.disable_all_channels()

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

