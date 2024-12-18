# AS7265x High Level - Clase de alto nivel para el sensor AS7265x.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024

import json
import logging
from classes.AS7265x_Controller_v1 import SENSOR_AS7265x
import time
import yaml

# with open("/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config_optimized.yaml", "r") as file:
#     config = yaml.safe_load(file)

# Configurar logging para el manejo de nivel alto
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

class AS7265x_Manager:
    """
    Manejo de alto nivel para un sensor AS7265x.
    Este archivo abstrae las operaciones comunes como configuración y lectura de espectros.
    """
    
    READY = 0x08 # Máscara para el bit "READY" del registro REG_STATUS

    def __init__(self, address=0x49, config=None, i2c_bus=1):
        """
        Inicializa el controlador de alto nivel para el sensor AS7265x.
        :param address: Dirección I²C del sensor.
        :param config: Configuración del sistema cargada desde config.yaml.
        :param i2c_bus: Bus I²C donde está conectado el sensor.
        """
        if config is None:
            raise ValueError("[MANAGER] [SENSOR] La configuración no puede ser None.")

        required_keys = ['sensors', 'system']
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            logging.error(f"[MANAGER] [SENSOR] Configuración actual: {config}")
            logging.error(f"[MANAGER] [SENSOR] Faltan claves requeridas en la configuración: {missing_keys}")
            raise KeyError(f"Faltan claves requeridas en la configuración: {missing_keys}")
        self.config = config
        self.address = address
        self.i2c_bus = i2c_bus
        self.sensor = SENSOR_AS7265x(i2c_bus=i2c_bus, address=address)
        logging.info(f"[SENSOR] AS7265x inicializado en la dirección {hex(address)}.")


    def configure(self):
        """
        Configura el sensor usando los parámetros de configuración desde config.yaml.
        """
        logging.info("[MANAGER] [SENSOR] Iniciando configuración del sensor...")
        try:
            integration_time = self.config['sensors']['integration_time']
            gain = self.config['sensors']['gain']
            mode = self.config['sensors']['mode']

            logging.info(f"[MANAGER] [SENSOR] Parámetros: integración={integration_time}, ganancia={gain}, modo={mode}.")

            # Llamada segura al controlador
            if hasattr(self.sensor, 'configure'):
                logging.info("[MANAGER] [SENSOR] Configurando el sensor.")
                self.sensor.configure(integration_time, gain, mode)
                logging.info(f"[MANAGER] [SENSOR] Configuración completada exitosamente.")
            else:
                raise AttributeError("[MANAGER] [SENSOR] El controlador no tiene un método 'configure'.")
        except KeyError as e:
            logging.error(f"[MANAGER] [SENSOR] Clave de configuración faltante: {e}")
            raise
        except Exception as e:
            logging.error(f"[MANAGER] [SENSOR] Error al configurar el sensor: {e}")
            raise


    def read_calibrated_spectrum(self):
        """
        Lee y devuelve el espectro calibrado del sensor.
        :return: Lista de valores calibrados.
        """
        try:
            spectrum = self.sensor.read_calibrated_spectrum()
            if not spectrum:
                raise ValueError("[MANAGER] [SENSOR] El espectro calibrado está vacío o es nulo.")

            # Diagnóstico opcional
            if self.config['system'].get('enable_sensor_diagnostics', False):
                self._diagnostic_check(spectrum)

            logging.info(f"[MANAGER] [SENSOR] Espectro calibrado leído:\n{json.dumps(spectrum, indent=4)}")
            return spectrum
        except Exception as e:
            logging.error(f"[MANAGER] [SENSOR] Error leyendo el espectro calibrado: {e}")
            raise

    def read_raw_spectrum(self):
        """
        Lee y devuelve el espectro crudo del sensor.
        :return: Diccionario con nombres de colores y valores.
        """
        try:
            raw_spectrum = self.sensor.read_raw_spectrum()
            if not raw_spectrum:
                raise ValueError("[MANAGER] [SENSOR] El espectro crudo está vacío o es nulo.")

            logging.info(f"[MANAGER] [SENSOR] Espectro crudo leído:\n{json.dumps(raw_spectrum, indent=4)}")
            return raw_spectrum
        except Exception as e:
            logging.error(f"[MANAGER] [SENSOR] Error leyendo el espectro crudo: {e}")
            raise

    def check_sensor_status(self):
        """
        Verifica el estado del sensor llamando a la función de bajo nivel `verify_ready_state` en el Controller.

        :return: True si el sensor está listo, False en caso contrario.
        """
        try:
            ready = self.sensor.verify_ready_state()
            if ready:
                logging.info("[MANAGER] [SENSOR] El sensor está listo para operar.")
                return True
            if not self.sensor.verify_ready_state():
                logging.error("[MANAGER] [SENSOR] El sensor no está listo después del reinicio.")
            raise RuntimeError("[MANAGER] [SENSOR] El sensor no está listo después del reinicio.")
        except Exception as e:
            logging.error(f"[MANAGER] [SENSOR] Error al verificar el estado del sensor: {e}")
            return False




    def reset(self):
        """
        Reinicia el sensor AS7265x.
        """
        try:
            self.sensor._reset()
            logging.info("[MANAGER] [SENSOR] Reinicio del sensor completado correctamente.")
        except Exception as e:
            logging.error(f"[MANAGER] [SENSOR] Error durante el reinicio: {e}")
            raise

    def read_status(self):
        """
        Lee el estado del sensor AS7265x.
        :return: Valor del estado del sensor.
        """

        logging.info(f"[MANAGER] [SENSOR] El sensor está listo.")
        return self.sensor.verify_ready_state()

    def _diagnostic_check(self, spectrum):
        """
        Verifica la calidad de los datos espectrales y genera alertas si son inconsistentes.
        :param spectrum: Datos espectrales calibrados.
        """
        try:
            if not spectrum:
                raise ValueError("[MANAGER] [SENSOR] El espectro está vacío para el diagnóstico.")

            if all(entry['calibrated_value'] == 0 for entry in spectrum):
                logging.warning("[MANAGER] [SENSOR] Diagnóstico: Todos los valores del espectro son 0.")

            if any(entry['calibrated_value'] > 3000 for entry in spectrum):
                logging.warning("[MANAGER] [SENSOR] Diagnóstico: Valor excesivo detectado en el espectro.")

            logging.info("[MANAGER] [SENSOR] Diagnóstico completado exitosamente.")
        except Exception as e:
            logging.error(f"[MANAGER] [SENSOR] Error en diagnóstico del espectro: {e}")
    
    def initialize_sensor(self):
        """
        Inicializa el sensor AS7265x y verifica que esté listo.
        """
        try:
            logging.info("[MANAGER] [SENSOR] Inicializando sensor AS7265x...")
            self.reset()  # Envío de comando de reinicio
            time.sleep(5)  # Espera tras el reinicio
            if self.sensor.check_sensor_status():
                logging.info("[MANAGER] [SENSOR] Sensor inicializado correctamente.")
            return True
        except Exception as e:
            logging.error(f"[MANAGER] [SENSOR] Error inicializando el sensor: {str(e)}")
            return False


    def is_ready(self):
        """
        Verifica si el sensor está en estado READY.
        """
        try:
            status = self.sensor._read_register(self.sensor.REG_STATUS)
            ready = bool(status & self.sensor.READY)
            logging.debug(f"[MANAGER] [SENSOR] REG_STATUS={bin(status)}, READY={ready}")
            return ready
        except Exception as e:
            logging.error(f"[MANAGER] [SENSOR] Error al verificar estado READY: {e}")
            return False



# Al final de AS7265x_HighLevel.py, fuera de clases
def generate_summary(successful_reads, failed_reads, error_details):
    """
    Genera un resumen mejorado al final del proceso.
    :param successful_reads: Número total de lecturas exitosas.
    :param failed_reads: Número total de fallos.
    :param error_details: Lista de detalles de errores.
    """
    warnings = []  # Asegúrate de que esté inicializado

    if failed_reads > 0:
        warnings.append("Se detectaron fallos durante la operación.")

    if successful_reads == 0:
        warnings.append("No se completaron lecturas exitosas.")

    logging.info("=" * 50)
    logging.info("")
    logging.info("========== RESUMEN FINAL ==========")
    logging.info(f"Lecturas exitosas: {successful_reads}")
    logging.info(f"Fallos totales: {failed_reads}")
    logging.info("")
    if error_details:
        logging.info("Detalles de los fallos por canal:")
        for error in error_details:
            channel = error.get('channel', 'Desconocido')
            message = error.get('error_message', 'Error no especificado.')
            logging.error(f" - Canal {channel}: {message}")
    if warnings:
        for warning in warnings:
            logging.warning(warning)

    if successful_reads == 0:
        logging.warning("No se completaron lecturas exitosas.")

    logging.info("=" * 50)
