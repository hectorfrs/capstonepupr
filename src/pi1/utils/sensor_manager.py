# sensor_manager.py - Clase para manejar múltiples sensores AS7265x conectados al MUX.
import logging
from lib.as7265x import CustomAS7265x
from threading import Thread
from typing import List, Dict


class SensorManager:
    """
    Clase para manejar múltiples sensores AS7265x conectados al MUX.
    """

    def __init__(self, config, mux_manager, alert_manager=None):
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

    

    def validate_sensor_config(self, config):
        try:
            channels = config.get('sensors', {}).get('as7265x', {}).get('channels', [])
            if not isinstance(channels, list):
                raise ValueError("La configuración de sensores debe ser una lista.")
            for channel in channels:
                if not isinstance(channel, dict):
                    raise ValueError(f"Cada canal debe ser un diccionario. Se encontró: {channel}")
            return channels
        except Exception as e:
            logging.error(f"Error validando la configuración de sensores: {e}")
            raise




    def read_sensors_concurrently(self):
        """
        Lee datos espectrales de los sensores de manera concurrente.
        """
        def read_sensor(sensor):
            while True:
                try:
                    self.mux_manager.select_channel(sensor.channel)
                    data = sensor.read_advanced_spectrum()
                    logging.info(f"Datos leídos del sensor {sensor.name} en canal {sensor.channel}: {data[sensor.name]}")
                    logging.info(f"Datos del sensor {sensor.name}: {data}")
                    time.sleep(sensor.read_interval)
                except Exception as e:
                    logging.error(f"Error leyendo datos del sensor {sensor.name}: {e}")
                finally:
                    self.mux_manager.disable_all_channels()

        threads = []
        for sensor in self.sensors:
            t = Thread(target=read_sensor, args=(sensor,), daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

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

    def initialize_sensors(self):
        """
        Inicializa los sensores AS7265x según la configuración proporcionada.
        """
        try:
            # Validar la configuración de los sensores
            sensor_channels = self.config["sensors"]["as7265x"]["channels"]
            default_settings = self.config["sensors"]["default_settings"]

            # Inicializar sensores
            for sensor_config in sensor_channels:
                channel = sensor_config.get("channel")
                name = sensor_config.get("name")
                enabled = sensor_config.get("enabled", True)

                # Omitir sensores deshabilitados
                if not enabled:
                    logging.info(f"Sensor {name} en canal {channel} está deshabilitado. Omitiendo...")
                    continue

                # Aplicar configuraciones específicas o usar valores por defecto
                integration_time = sensor_config.get("integration_time", default_settings.get("integration_time", 100))
                gain = sensor_config.get("gain", default_settings.get("gain", 3))
                led_intensity = sensor_config.get("led_intensity", default_settings.get("led_intensity", 0))
                read_interval = sensor_config.get("read_interval", 3)

                # Inicializar sensor
                sensor = CustomAS7265x(
                    name=name,
                    mux_manager=self.mux_manager
                )
                sensor.channel = channel
                sensor.integration_time = integration_time
                sensor.gain = gain
                sensor.led_intensity = led_intensity
                sensor.read_interval = read_interval

                # Registrar el sensor en SensorManager
                self.sensors.append(sensor)

                logging.info(f"Sensor {name} inicializado en canal {channel}:")
                logging.info(f"  - Tiempo de integración: {integration_time} ms")
                logging.info(f"  - Ganancia: {gain}")
                logging.info(f"  - Intensidad LED: {led_intensity}")
                logging.info(f"  - Intervalo de lectura: {read_interval} s")

            # Validar si los sensores están conectados
            if not self.sensors:
                raise RuntimeError("No se pudieron inicializar sensores. Verifique la configuración.")

            logging.info("Sensores inicializados correctamente.")

        except Exception as e:
            logging.critical(f"Error inicializando sensores: {e}", exc_info=True)
            if self.alert_manager:
                self.alert_manager.send_alert(
                    level="CRITICAL",
                    message="Error inicializando los sensores.",
                    metadata={"error": str(e)}
                )
            raise





    # def initialize_sensors(self):
    #     """
    #     Inicializa sensores según la configuración definida en el archivo config.yaml.
    #     """
    #     try:
    #         sensor_channels = self.config.get('sensors', {}).get('as7265x', {}).get('channels', [])
    #         if not sensor_channels:
    #             raise ValueError("No se encontraron configuraciones de canales para sensores en config.yaml.")

    #         # Asegúrate de que sensor_channels sea una lista
    #         if not isinstance(sensor_channels, list):
    #             raise ValueError("La configuración de los sensores no es válida. Se esperaba una lista en 'sensors->as7265x->channels'.")

    #         # Iterar sobre la lista de sensores
    #         for channel_info in sensor_channels:
    #             if not isinstance(channel_info, dict):
    #                 raise ValueError(f"Cada canal debe ser un diccionario. Se encontró: {channel_info}")

    #             channel = channel_info['channel']
    #             sensor_name = channel_info['name']
    #             enabled = channel_info.get('enabled', True)
    #             read_interval = channel_info.get('read_interval', 3)

    #             if not enabled:
    #                 logging.info(f"Sensor {sensor_name} en canal {channel} está deshabilitado.")
    #                 continue

    #             # Inicializar el sensor
    #             sensor = CustomAS7265x(name=sensor_name, mux_manager=self.mux_manager)
    #             sensor.channel = channel
    #             sensor.read_interval = read_interval
    #             self.sensors.append(sensor)
    #             logging.info(f"Sensor {sensor_name} inicializado en canal {channel} con intervalo de lectura {read_interval} segundos.")
    #     except Exception as e:
    #         logging.error(f"Error inicializando sensores: {e}")
    #         raise