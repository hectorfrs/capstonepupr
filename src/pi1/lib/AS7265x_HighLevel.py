# AS7265x High Level - Clase de alto nivel para el sensor AS7265x.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024

import logging
from classes.AS7265x_Manager import AS7265xManager

# Configurar logging para el manejo de nivel alto
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

class AS7265xSensorHighLevel:
    """
    Manejo de alto nivel para un sensor AS7265x.
    Este archivo abstrae las operaciones comunes como configuración y lectura de espectros.
    """

    def __init__(self, address=0x49):
        """
        Inicializa el controlador de alto nivel para el sensor AS7265x.
        :param address: Dirección I²C del sensor.
        """
        self.sensor = AS7265xManager(address=address)
        logging.info(f"Sensor AS7265x inicializado en la dirección {hex(address)}.")

    def configure(self, integration_time=100, gain=2, mode=3):
        """
        Configura el sensor con los parámetros dados.
        :param integration_time: Tiempo de integración (1-255).
        :param gain: Ganancia (0=1x, 1=3.7x, 2=16x, 3=64x).
        :param mode: Modo de operación (0-3).
        """
        self.sensor.configure(integration_time, gain, mode)
        logging.info(f"Sensor configurado: integración={integration_time}, ganancia={gain}, modo={mode}.")

    def read_calibrated_spectrum(self):
        """
        Lee y devuelve el espectro calibrado del sensor.
        :return: Lista de valores calibrados.
        """
        spectrum = self.sensor.read_calibrated_spectrum()
        logging.info(f"Espectro calibrado leído: {spectrum}")
        return spectrum

    def read_raw_spectrum(self):
        """
        Lee el espectro crudo en formato de diccionario usando AS7265x_Manager.
        :return: Diccionario con nombres de colores y valores.
        """
        try:
            logging.debug("Leyendo espectro crudo desde AS7265x_Manager...")
            raw_spectrum = self.sensor.read_raw_spectrum()  # Llama a la función del manager
            logging.info(f"Espectro crudo leído: {raw_spectrum}")
            return raw_spectrum
        except Exception as e:
            raise RuntimeError(f"Error leyendo el espectro crudo: {e}")


    def check_sensor_status(self):
        """
        Verifica el estado inicial del sensor AS7265x.
        """
        # Leer el estado del sensor
        for attempt in range(3):  # Hasta 3 intentos
            sensor_status = self._read_status()
            logging.debug(f"Estado del sensor: {bin(sensor_status)}")

            if sensor_status & 0x80:  # Bit ocupado
                logging.warning(f"El sensor está ocupado. Reintento {attempt + 1}/3...")
                time.sleep(1)  # Esperar 1 segundo antes de reintentar
            else:
                logging.info("El sensor está listo para recibir comandos.")
        return True

        raise Exception("El sensor sigue ocupado después de varios intentos.")

    def reset(self):
        """
        Reinicia el sensor AS7265x utilizando la clase base.
        """
        try:
            self.sensor.reset()
            logging.info("El sensor ha sido reiniciado correctamente.")
        except Exception as e:
            logging.error(f"Error al reiniciar el sensor: {e}")
            raise

    def read_status(self):
        """
        Lee el estado del sensor AS7265x.
        :return: Valor del estado del sensor.
        """
        return self.sensor._read_status()

    
