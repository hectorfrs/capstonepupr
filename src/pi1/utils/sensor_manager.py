# sensor_manager.py - Clase para manejar múltiples sensores AS7265x conectados al MUX.
import logging
import time
import threading

from lib.as7265x import CustomAS7265x
from typing import List, Dict
from lib.mux_manager import MUXManager
from concurrent.futures import ThreadPoolExecutor


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
        self.config = config                    # Configuración de los sensores.
        self.mux_manager = mux_manager          # Instancia de MUXManager.
        self.alert_manager = alert_manager      # Instancia de AlertManager.
        self.sensors = []                       # Lista de sensores inicializados.
        self.lock = threading.Lock()            # Cerradura para sincronización.

    

    def validate_sensor_config(self) -> List[Dict]:
        """
        Valida la configuración de sensores y devuelve una lista de configuraciones válidas.
        """
        try:
            channels = self.config.get('sensors', {}).get('as7265x', {}).get('channels', [])
            if not isinstance(channels, list):
                raise ValueError("La configuración de sensores debe ser una lista.")
            for channel in channels:
                if not isinstance(channel, dict):
                    raise ValueError(f"Cada canal debe ser un diccionario. Se encontró: {channel}")
            return channels
        except Exception as e:
            logging.error(f"Error validando la configuración de sensores: {e}")
            raise

    def validate_sensor_data(self, data):
        """
        Valida los datos leídos del sensor.
        """
        expected_keys = ['violet', 'blue', 'green', 'yellow', 'orange', 'red']
        for key in expected_keys:
            value = data.get(key, None)
            if value is None or not (0 <= value <= 65535):
                logging.error(f"Datos inválidos detectados: {data}")
                return False
        logging.info(f"Datos validados correctamente: {data}")
        return True

    def read_sensor_with_retries(self, sensor, retries=3, delay=1):
        """
        Intenta leer datos de un sensor con un número especificado de reintentos.

        :param sensor: El sensor del cual se leerán los datos.
        :param retries: Número de intentos antes de fallar.
        :param delay: Tiempo en segundos entre reintentos.
        :return: Datos leídos o None si falla.
        """
        for attempt in range(retries):
            try:
                with self.lock:
                    self.mux_manager.select_channel(sensor.channel)
                data = sensor.read_advanced_spectrum()
                logging.info(f"Datos leídos del sensor {sensor.name} en intento {attempt + 1}: {data}")
                return data
            except Exception as e:
                logging.warning(f"Error leyendo sensor {sensor.name} en intento {attempt + 1}: {e}")
                time.sleep(delay)
            finally:
                with self.lock:
                    self.mux_manager.disable_all_channels()
        logging.error(f"Fallo al leer el sensor {sensor.name} tras {retries} intentos.")
        return None

    def read_sensors(self):
        """
        Lee datos de todos los sensores y valida los resultados.

        :return: Un diccionario con los nombres de los sensores como claves y los datos leídos como valores.
        """
        results = {}
        for sensor in self.sensors:
            logging.info(f"Iniciando lectura del sensor {sensor.name}.")
            data = self.read_sensor_with_retries(sensor)
            if data and self.validate_sensor_data(data):
                results[sensor.name] = data
            else:
                logging.warning(f"Datos no válidos o no disponibles para el sensor {sensor.name}.")
        return results
        return True

    def check_sensor_status(sensor):
        try:
            status = sensor.get_status_register()
            if status & 0x01:  # Estado válido, dependiendo del registro
                return True
            print("Advertencia: Sensor no listo")
            return False
        except Exception as e:
            print(f"Error verificando estado del sensor: {e}")
            return False

    def read_sensors_concurrently(self):
        """
        Lee datos espectrales de los sensores de manera concurrente.
        """
        def read_sensor(sensor):
            """
            Lee datos de un sensor específico.
            """
            while True:
                try:
                    with self.lock:
                        self.mux_manager.select_channel(sensor.channel)
                    data = sensor.read_advanced_spectrum()
                    logging.info(f"Datos leídos del sensor {sensor.name}: {data}")
                except Exception as e:
                    logging.error(f"Error leyendo datos del sensor {sensor.name}: {e}")
                finally:
                    with self.lock:
                        self.mux_manager.disable_all_channels()

        # Crear un ThreadPoolExecutor para ejecutar las lecturas en paralelo
        with ThreadPoolExecutor(max_workers=len(self.sensors)) as executor:
            futures = [executor.submit(read_sensor, sensor) for sensor in self.sensors]

            # Manejar excepciones si ocurre algún error en los hilos
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error en la ejecución del hilo: {e}")

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
                elif sensor.is_critical():
                    logging.warning(f"Sensor {sensor.name} está en estado crítico.")
                    if self.alert_manager:
                        self.alert_manager.send_alert(
                            level="WARNING",
                            message=f"Sensor {sensor.name} en estado crítico.",
                            metadata={"sensor_name": sensor.name, "channel": sensor.channel}
                        )
                else:
                    logging.info(f"Sensor {sensor.name} está funcionando correctamente.")
            except Exception as e:
                logging.error(f"Error ejecutando diagnósticos en sensor {sensor.name}: {e}")
                if self.alert_manager:
                    self.alert_manager.send_alert(
                        level="ERROR",
                        message=f"Error en diagnósticos del sensor {sensor.name}",
                        metadata={"sensor_name": sensor.name, "channel": sensor.channel, "error": str(e)}
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
                        message=f"Error apagando el sensor {sensor.name}",
                        metadata={"sensor_name": sensor.name, "channel": sensor.channel, "error": str(e)}
                    )

    # def initialize_sensors(self):
    #     """
    #     Inicializa sensores según la configuración definida en config.yaml.
    #     """
    #     try:
    #         # Validar la configuración
    #         sensor_channels = self.validate_sensor_config()
    #         default_settings = self.config.get('sensors', {}).get('default_settings', {})

    #         # Inicializar sensores
    #         for sensor_config in sensor_channels:
    #             if not sensor_config.get("enabled", True):
    #                 logging.info(f"Sensor {sensor_config.get('name')} en canal {sensor_config.get('channel')} está deshabilitado. Omitiendo...")
    #                 continue

    #             # Aplicar configuraciones específicas o usar valores predeterminados
    #             integration_time = sensor_config.get("integration_time", default_settings.get("integration_time", 100))
    #             gain = sensor_config.get("gain", default_settings.get("gain", 3))
    #             led_intensity = sensor_config.get("led_intensity", default_settings.get("led_intensity", 0))
    #             read_interval = sensor_config.get("read_interval", default_settings.get("read_interval", 3))
    #             operating_mode = sensor_config.get("operating_mode", default_settings.get("operating_mode", 0))
    #             enable_interrupts = sensor_config.get("enable_interrupts", default_settings.get("enable_interrupts", True))

    #             # Crear instancia del sensor
    #             sensor = CustomAS7265x(
    #             name=sensor_config.get("name"),
    #             channel=sensor_config.get("channel"),
    #             i2c_address=sensor_config.get("i2c_address", 0x49),  # Dirección predeterminada: 0x49
    #             integration_time=integration_time,
    #             gain=gain,
    #             led_intensity=led_intensity,
    #             read_interval=read_interval,
    #             mux_manager=self.mux_manager,
    #             i2c_bus=self.mux_manager.i2c_bus
    #             )

    #             self.sensors.append(sensor)
    #             logging.info(f"Sensor {sensor.name} inicializado en canal {sensor.channel} con:")
    #             logging.info(f"  - Tiempo de integración: {integration_time} ms")
    #             logging.info(f"  - Ganancia: {gain}")
    #             logging.info(f"  - Intensidad LED: {led_intensity}")
    #             logging.info(f"  - Intervalo de lectura: {read_interval} s")
    #             logging.info(f"  - Modo de operación: {operating_mode}")
    #             logging.info(f"  - Interrupciones habilitadas: {enable_interrupts}")

    #         if not self.sensors:
    #             raise RuntimeError("No se inicializaron sensores. Verifique la configuración.")

    #         logging.info("Sensores inicializados correctamente.")

    #     except Exception as e:
    #         logging.critical(f"Error inicializando sensores: {e}", exc_info=True)
    #         if self.alert_manager:
    #             self.alert_manager.send_alert(
    #                 level="CRITICAL",
    #                 message="Error inicializando los sensores.",
    #                 metadata={"error": str(e)}
    #             )
    #         raise


def initialize_sensors(self):
        """
        Inicializa sensores según la configuración definida en config.yaml.
        """
        try:
            sensor_channels = self.validate_sensor_config()
            default_settings = self.config.get('sensors', {}).get('default_settings', {})

            for sensor_config in sensor_channels:
                if not sensor_config.get("enabled", True):
                    logging.info(f"Sensor {sensor_config.get('name')} en canal {sensor_config.get('channel')} está deshabilitado. Omitiendo...")
                    continue

                integration_time = sensor_config.get("integration_time", default_settings.get("integration_time", 100))
                gain = sensor_config.get("gain", default_settings.get("gain", 3))
                led_intensity = sensor_config.get("led_intensity", default_settings.get("led_intensity", 0))
                read_interval = sensor_config.get("read_interval", default_settings.get("read_interval", 3))

                sensor = CustomAS7265x(
                    name=sensor_config.get("name"),
                    channel=sensor_config.get("channel"),
                    i2c_address=sensor_config.get("i2c_address", 0x49),
                    integration_time=integration_time,
                    gain=gain,
                    led_intensity=led_intensity,
                    read_interval=read_interval,
                    mux_manager=self.mux_manager,
                    i2c_bus=self.mux_manager.i2c_bus
                )

                self.sensors.append(sensor)
                logging.info(f"Sensor {sensor.name} inicializado en canal {sensor.channel} con configuraciones específicas.")

            if not self.sensors:
                raise RuntimeError("No se inicializaron sensores. Verifique la configuración.")

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