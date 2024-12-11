# AS7265x High Level - Clase de alto nivel para el sensor AS7265x.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024

import logging
from classes.AS7265x_Manager import AS7265xManager

# Configurar logging para el manejo de nivel alto
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

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

    def read_raw_data(self):
        """
        Lee y devuelve los datos crudos del sensor.
        :return: Lista de valores crudos.
        """
        raw_data = self.sensor.read_raw_data()
        logging.info(f"Datos crudos leídos: {raw_data}")
        return raw_data

    def check_sensor_status(self):
        """
        Verifica el estado inicial del sensor AS7265x.
        """
        status = self.sensor._read_register(0x00)
        if sensor_status & 0x80 == 0x80:
            logging.error("El sensor está ocupado procesando datos.")
            raise Exception("El sensor no está en estado listo.")
        elif sensor_status & 0x01 == 0x01:
            logging.error(f"Estado inesperado del sensor: {hex(sensor_status)}")
            raise Exception("El sensor no está en estado listo.")
        else:
            logging.info("El sensor está listo para recibir comandos.")
