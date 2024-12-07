import logging
from lib.as7265x import CustomAS7265x

class SensorManager:
    """
    Clase para manejar múltiples sensores AS7265x conectados al MUX.
    """

    def __init__(self, sensor_config, mux_manager, alert_manager=None):
        """
        Inicializa el administrador de sensores.

        :param sensor_config: Configuración de los sensores cargada desde YAML.
        :param mux_manager: Instancia de MUXManager para manejar los canales.
        :param alert_manager: Instancia opcional de AlertManager para manejar alertas.
        """
        self.sensor_config = sensor_config
        self.mux_manager = mux_manager
        self.alert_manager = alert_manager
        self.sensors = {}  # Diccionario para almacenar sensores por canal

    def initialize_sensors(self, active_channels):
        """
        Inicializa los sensores en los canales activos detectados.

        :param active_channels: Lista de canales activos detectados.
        """
        for channel in active_channels:
            try:
                # Crear una instancia del sensor AS7265x
                sensor = CustomAS7265x(
                    config_path=self.sensor_config.get("config_path", "config/pi1_config.yaml"),
                    name=self.sensor_config["mux"]["channels"][channel]["sensor_name"],
                )

                # Verificar si el sensor está conectado
                if sensor.is_connected():
                    self.sensors[channel] = sensor
                    logging.info(f"Sensor {sensor.name} inicializado correctamente en canal {channel}.")
                else:
                    logging.warning(f"No se detectó sensor en canal {channel}.")
            except Exception as e:
                logging.error(f"Error inicializando sensor en canal {channel}: {e}")
                if self.alert_manager:
                    self.alert_manager.send_alert(
                        level="CRITICAL",
                        message=f"Error inicializando sensor en canal {channel}",
                        metadata={"channel": channel, "error": str(e)},
                    )

    def read_sensor_data(self, channel):
        """
        Lee los datos del sensor en el canal especificado.

        :param channel: Canal del MUX donde está el sensor.
        :return: Diccionario con los datos del sensor, o None si hay un error.
        """
        try:
            self.mux_manager.select_channel(channel)  # Seleccionar el canal en el MUX
            sensor = self.sensors.get(channel)

            if sensor:
                # Leer datos avanzados del espectro
                data = sensor.read_advanced_spectrum()
                logging.info(f"Datos del sensor {sensor.name} en canal {channel}: {data}")
                return data
            else:
                raise RuntimeError(f"Sensor no configurado en canal {channel}")
        except Exception as e:
            logging.error(f"Error leyendo datos del sensor en canal {channel}: {e}")
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="CRITICAL",
                    message=f"Error leyendo datos del sensor en canal {channel}",
                    metadata={"channel": channel, "error": str(e)},
                )
        finally:
            self.mux_manager.disable_all_channels()  # Desactivar todos los canales después de leer
        return None

    def perform_diagnostics(self):
        """
        Ejecuta diagnósticos en los sensores inicializados.
        """
        for channel, sensor in self.sensors.items():
            try:
                if sensor.is_critical():
                    logging.warning(f"Sensor en canal {channel} está en estado crítico.")
                    if self.alert_manager:
                        self.alert_manager.send_alert(
                            level="WARNING",
                            message=f"Sensor crítico en canal {channel}",
                            metadata={"sensor_name": sensor.name, "channel": channel},
                        )
                else:
                    logging.info(f"Sensor en canal {channel} está funcionando correctamente.")
            except Exception as e:
                logging.error(f"Error ejecutando diagnósticos en sensor {sensor.name}: {e}")
                if self.alert_manager:
                    self.alert_manager.send_alert(
                        level="ERROR",
                        message=f"Error en diagnósticos de sensor en canal {channel}",
                        metadata={"sensor_name": sensor.name, "channel": channel, "error": str(e)},
                    )

    def power_off_sensors(self):
        """
        Apaga los sensores para ahorrar energía.
        """
        for channel, sensor in self.sensors.items():
            try:
                sensor.power_off()
                logging.info(f"Sensor {sensor.name} apagado para ahorro de energía.")
            except Exception as e:
                logging.error(f"Error apagando el sensor {sensor.name}: {e}")
                if self.alert_manager:
                    self.alert_manager.send_alert(
                        level="WARNING",
                        message=f"Error apagando sensor en canal {channel}",
                        metadata={"sensor_name": sensor.name, "channel": channel, "error": str(e)},
                    )
