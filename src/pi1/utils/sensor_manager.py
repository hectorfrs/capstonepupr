# sensor_manager.py - Clase para manejar múltiples sensores AS7265x conectados al MUX.
import logging
from lib.as7265x import CustomAS7265x

class SensorManager:
    """
    Clase para manejar múltiples sensores AS7265x conectados al MUX.
    """

    def __init__(self, mux_manager, alert_manager=None, config=None):
        """
        Inicializa el administrador de sensores.

        :param sensor_config: Configuración de los sensores cargada desde YAML.
        :param mux_manager: Instancia de MUXManager para manejar los canales.
        :param alert_manager: Instancia opcional de AlertManager para manejar alertas.
        """
        self.config = config                # Configuración de los sensores.
        self.mux_manager = mux_manager      # Instancia de MUXManager.
        self.alert_manager = alert_manager  # Instancia de AlertManager.
        self.sensors = []                   # Lista de sensores inicializados.

    def initialize_sensors(self, mux_manager):
        """
        Inicializa sensores según configuración.
        """
        channels = self.config['mux']['channels']
        for channel_info in channels:
            try:
                sensor_name = channel_info['sensor_name']
                channel = channel_info['channel']
                sensor = CustomAS7265x(name=sensor_name)

                if sensor.is_connected():
                    sensor.channel = channel
                    self.sensors.append(sensor)
                    logging.info(f"Sensor {sensor_name} conectado en canal {channel}.")
                else:
                    logging.warning(f"Sensor {sensor_name} no responde en canal {channel}.")
            except Exception as e:
                logging.error(f"Error inicializando sensor en canal {channel}: {e}")
    
    def update_config_with_active_channels(self, active_channels):
        self.config['mux']['active_channels'] = active_channels
        self.save_config()

    def read_all_sensors(self):
        """
        Lee datos espectrales de todos los sensores.
        """
        data = {}
        for sensor in self.sensors:
            try:
                data[sensor.name] = sensor.read_advanced_spectrum()
            except Exception as e:
                logging.error(f"Error leyendo datos del sensor {sensor.name}: {e}")
        return data

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
