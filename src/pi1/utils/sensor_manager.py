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

    def initialize_sensors(self):
        
            try:
                if not self.config.get('mux', {}).get('channels', []):
                    raise ValueError("No se encontraron configuraciones de canales")

                for channel_info in self.config['mux']['channels']:    
                    sensor_name = channel_info['sensor_name']
                    channel = channel_info['channel']
                    sensor = CustomAS7265x(channel=channel, name=sensor_name, mux_manager=self.mux_manager)
                    sensor.channel = channel
                    self.sensors.append(sensor)
                    logging.info(f"Sensor {sensor_name} inicializado en canal {channel}.")
            except Exception as e:
                logging.error(f"Error inicializando sensor en canal {channel}: {e}")
                raise


    # def initialize_sensors(self):
    #     """
    #     Inicializa sensores según configuración.
    #     """
    #     try:
    #         sensor_config = self.config.get('sensors', {})
    #         if not sensor_config:
    #             raise ValueError("No se encontraron configuraciones de sensores en config.yaml.")

    #         for sensor in sensor_config.get('as7265x', {}).get('channels', []):
    #             channel = sensor['channel']
    #             sensor_name = sensor['sensor_name']
    #             new_sensor = CustomAS7265x(channel=channel, name=sensor_name, mux_manager=self.mux_manager)
    #             self.sensors.append(new_sensor)
    #             logging.info(f"Sensor {sensor_name} inicializado en canal {channel}.")
    #     except Exception as e:
    #         logging.critical(f"Error inicializando sensores: {e}")
    #         raise


    
    def read_all_sensors(self):
        """
        Lee datos espectrales de todos los sensores inicializados.
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
        for sensor in self.sensors:
            try:
                if sensor.is_critical():
                    logging.warning(f"Sensor {sensor.name} está en estado crítico.")
                    if self.alert_manager:
                        self.alert_manager.send_alert(
                            level="WARNING",
                            message=f"Sensor crítico detectado.",
                            metadata={"sensor_name": sensor.name, "channel": sensor.channel},
                        )
                else:
                    logging.info(f"Sensor {sensor.name} está funcionando correctamente.")
            except Exception as e:
                logging.error(f"Error ejecutando diagnósticos en sensor {sensor.name}: {e}")
                if self.alert_manager:
                    self.alert_manager.send_alert(
                        level="ERROR",
                        message=f"Error en diagnósticos del sensor {sensor.name}",
                        metadata={"sensor_name": sensor.name, "channel": sensor.channel, "error": str(e)},
                    )


    def power_off_sensors(self):
        """
        Apaga los sensores para ahorrar energía.
        """
        for sensor in self.sensors:
            try:
                sensor.power_off()
                logging.info(f"Sensor {sensor.name} apagado para ahorro de energía.")
            except Exception as e:
                logging.error(f"Error apagando el sensor {sensor.name}: {e}")
                if self.alert_manager:
                    self.alert_manager.send_alert(
                        level="WARNING",
                        message=f"Error apagando sensor {sensor.name}",
                        metadata={"sensor_name": sensor.name, "channel": sensor.channel, "error": str(e)},
                    )

