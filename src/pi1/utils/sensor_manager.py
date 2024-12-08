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
        """
        Inicializa sensores según la configuración definida en el archivo config.yaml.
        """
        try:
            # Verificar configuración de sensores en config.yaml
            sensor_channels = self.config.get('sensors', {}).get('as7265x', {}).get('channels', {})
            if not sensor_channels:
                raise ValueError("No se encontraron configuraciones de canales para sensores en config.yaml.")

            for channel_info in sensor_channels:
                channel = channel_info['channel']
                sensor_name = channel_info['name']
                enabled = channel_info.get('enabled', True)
                read_interval = channel_info.get('read_interval', 3)

                if not enabled:
                    logging.info(f"Sensor {sensor_name} en canal {channel} está deshabilitado.")
                    continue

                # Inicializar el sensor
                sensor = CustomAS7265x(name=sensor_name, mux_manager=self.mux_manager)
                sensor.channel = channel
                sensor.read_interval = read_interval
                self.sensors.append(sensor)
                logging.info(f"Sensor {sensor_name} inicializado en canal {channel} con intervalo de lectura {read_interval} segundos.")
        except Exception as e:
            logging.error(f"Error inicializando sensores: {e}")
            raise

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
        for sensor in self.sensors:
            try:
                if not sensor.is_connected():
                    logging.warning(f"Sensor {sensor.name} no está conectado.")

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

