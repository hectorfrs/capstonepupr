# AS7265xManager.py - Clase para manejar el sensor AS7265x utilizando la biblioteca Qwiic I2C.
# Desarrollado por Héctor F. Rivera Santiago
# copyright (c) 2024

from smbus2 import SMBus
import time
import logging

# Configurar logging para el módulo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class AS7265xManager:
    """
    Clase optimizada para manejar el sensor AS7265x utilizando SMBus2.
    Proporciona funcionalidad completa para la configuración y lectura del espectro,
    incluyendo soporte para múltiples dispositivos internos del sensor.
    """

    I2C_ADDR = 0x49             # Dirección predeterminada del AS7265x
    REG_STATUS = 0x00           # Registro de estado
    REG_WRITE = 0x01            # Registro para escritura
    REG_READ = 0x02             # Registro para lectura

    TX_VALID = 0x02             # Buffer de escritura ocupado
    RX_VALID = 0x01             # Datos disponibles para leer
    POLLING_DELAY = 0.05        # Retardo de espera para el buffer de escritura

    DEVICES = {"AS72651-NIR": 0b00, "AS72652-VIS": 0b01, "AS72653-UV": 0b10}  # Selección de dispositivos internos

    def __init__(self, bus_num=1, address=I2C_ADDR):
        """
        Inicializa el sensor en el bus I²C.
        :param bus_num: Número del bus I²C.
        :param address: Dirección I²C del sensor.
        """
        self.address = address
        self.bus = SMBus(bus_num)
        #logging.info(f"Sensor AS7265x inicializado en la dirección {hex(address)}.")

    def _write_register(self, reg, value):
        """
        Escribe un valor en un registro del sensor.
        :param reg: Dirección del registro.
        :param value: Valor a escribir.
        """
        self.bus.write_byte_data(self.address, reg, value)
        #logging.debug(f"Escrito {value} en el registro {hex(reg)}.")

    def _read_register(self, reg):
        """
        Lee un valor de un registro del sensor.
        :param reg: Dirección del registro.
        :return: Valor leído.
        """
        attempts = 3
        for attempt in range(attempts):
            try:
                value = self.bus.read_byte_data(self.address, reg)
                #logging.debug(f"Leído {value} del registro {hex(reg)}.")
                return value
            except OSError as e:
                logging.warning(f"Error de I2C al leer el registro {hex(reg)} (Intento {attempt + 1}/{attempts}): {e}")
                time.sleep(self.POLLING_DELAY)  # Esperar antes de reintentar
        raise OSError(f"No se pudo leer el registro {hex(reg)} después de {attempts} intentos.")

    def _write_virtual_register(self, reg, value):
        """
        Escribe en un registro virtual del sensor.
        :param reg: Dirección del registro virtual.
        :param value: Valor a escribir.
        """
        while self._read_status() & self.TX_VALID:
            time.sleep(0.05)                                # Esperar hasta que el buffer de escritura esté listo
        self._write_register(self.REG_WRITE, reg | 0x80)    # Escribir dirección del registro
        self._write_register(self.REG_WRITE, value)         # Escribir valor
        #logging.debug(f"Registro virtual {hex(reg)} configurado con {value}.")

    def _read_virtual_register(self, reg):
        """
        Lee un registro virtual del sensor.
        :param reg: Dirección del registro virtual.
        :return: Valor leído del registro.
        """
        while self._read_status() & self.TX_VALID:
            time.sleep(0.01)                                # Esperar hasta que el buffer de escritura esté listo
        self._write_register(self.REG_WRITE, reg)           # Escribir dirección para leer
        while not (self._read_status() & self.RX_VALID):
            time.sleep(0.01)                                # Esperar hasta que haya datos disponibles
        value = self._read_register(self.REG_READ)          # Leer valor
        #logging.debug(f"Registro virtual {hex(reg)} leído con valor {value}.")
        return value

    def _read_status(self):
        """
        Lee el estado del sensor.
        :return: Valor del registro de estado.
        """
        return self._read_register(self.REG_STATUS)

    def configure(self, integration_time, gain, mode):
        """
        Configura el sensor con parámetros básicos.
        :param integration_time: Tiempo de integración (1-255).
        :param gain: Ganancia (0=1x, 1=3.7x, 2=16x, 3=64x).
        :param mode: Modo de operación (0-3).
        """
        self._write_virtual_register(0x05, integration_time)            # Configurar tiempo de integración
        config = self._read_virtual_register(0x04)                      # Leer configuración actual
        config = (config & 0b11001111) | (gain << 4)                    # Ajustar ganancia
        self._write_virtual_register(0x04, config)                      # Escribir nueva configuración
        self._write_virtual_register(0x07, mode)                        # Configurar modo de operación
        logging.info(f"Sensor configurado: integración={integration_time}, ganancia={gain}, modo={mode}.")

    def set_devsel(self, device):
        """
        Selecciona el dispositivo interno del sensor.
        :param device: Dispositivo a seleccionar (AS72651, AS72652, AS72653).
        """
        if device_name == "AS72651-NIR":
            # Cambia al dispositivo NIR
            self._write_register(0x4F, 0x00)
        elif device_name == "AS72652-VIS":
            # Cambia al dispositivo VIS
            self._write_register(0x4F, 0x01)
        elif device_name == "AS72653-UV":
            # Cambia al dispositivo UV
            self._write_register(0x4F, 0x02)

        if device not in self.DEVICES:
            raise ValueError(f"Dispositivo {device} no válido. Seleccione entre {list(self.DEVICES.keys())}.")
        self._write_virtual_register(0x4F, self.DEVICES[device])
        logging.info(f"Dispositivo seleccionado: {device}.")

    def read_calibrated_spectrum(self):
        """
        Lee y devuelve el espectro calibrado del sensor.
        :return: Lista de valores calibrados para los 18 canales.
        """
        spectrum = []
        for reg in range(0x14, 0x2C, 2):
            msb = self._read_virtual_register(reg)
            lsb = self._read_virtual_register(reg + 1)
            value = (msb << 8) | lsb
            spectrum.append(value / 1000.0)  # Convertir a flotante
        #logging.info(f"Espectro calibrado leído: {spectrum}")
        return spectrum

    # def read_raw_spectrum(self):
    #     """
    #     Lee y devuelve los valores crudos del espectro en un formato de diccionario.
    #     :return: Diccionario con nombres de colores y valores.
    #     """
    #     raw_registers = [
    #         (0x08, 0x09), (0x0A, 0x0B), (0x0C, 0x0D),
    #         (0x0E, 0x0F), (0x10, 0x11), (0x12, 0x13)
    #     ]
    #     wavelengths = ["Violet", "Blue", "Green", "Yellow", "Orange", "Red"]
    #     devices = ["AS72651", "AS72652", "AS72653"]

    #     spectral_data = {color: 0 for color in wavelengths}

    #     for device in devices:
    #         self.set_devsel(device)  # Selecciona el dispositivo
    #         for i, reg_pair in enumerate(raw_registers):
    #             high_byte = self._read_register(reg_pair[0])
    #             low_byte = self._read_register(reg_pair[1])
    #             value = (high_byte << 8) | low_byte
    #             spectral_data[wavelengths[i]] += value

    #     return spectral_data

    def read_raw_spectrum(self):
        """
        Lee y devuelve los valores crudos del espectro para los 18 registros de cada dispositivo.
        :return: Diccionario con los valores crudos organizados por dispositivo y longitud de onda.
        """
        raw_registers = [
            (0x08, 0x09), (0x0A, 0x0B), (0x0C, 0x0D),
            (0x0E, 0x0F), (0x10, 0x11), (0x12, 0x13)
        ]
        wavelengths = ["Violet", "Blue", "Green", "Yellow", "Orange", "Red"]
        devices = ["AS72651-NIR", "AS72652-VIS", "AS72653-UV"]

        spectral_data = {device: {color: 0 for color in wavelengths} for device in devices}

        for device in devices:
            self.set_devsel(device)  # Selecciona el dispositivo
            for i, reg_pair in enumerate(raw_registers):
                high_byte = self._read_register(reg_pair[0])
                low_byte = self._read_register(reg_pair[1])
                if high_byte is None or low_byte is None:
                    logging.error(f"Error al leer los registros {reg_pair} para {device_name}")
                value = (high_byte << 8) | low_byte
                spectral_data[device][wavelengths[i]] = value

        return spectral_data




    def reorder_data(self, data):
        """
        Reordena los datos según las especificaciones del sensor.
        :param data: Lista de datos espectrales.
        :return: Lista reordenada.
        """
        mappings = [
            (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7),
            (8, 8), (13, 9), (14, 11), (9, 10), (10, 12), (15, 13),
            (16, 14), (17, 15), (18, 16), (11, 17), (12, 18)
        ]
        reordered = [0] * 18
        for src, dest in mappings:
            reordered[dest - 1] = data[src - 1]
        #logging.info(f"Datos reordenados: {reordered}")
        return reordered
    
    def set_integration_time(self, time):
        """
        Configura el tiempo de integración.
        """
        if not (1 <= time <= 255):
            raise ValueError("El tiempo de integración debe estar entre 1 y 255.")
        
        devices = ["AS72651", "AS72652", "AS72653"]
        for device in devices:
            self.set_devsel(device)
            self.write_reg(0x05, time)

    def reset(self):
        """
        Reinicia el sensor AS7265x utilizando el bit de reset.
        """
        try:
            self._write_virtual_register(0x04, 0x02)  # Registro de control: bit de reinicio
            time.sleep(1)  # Esperar 1 segundo para que el sensor se reinicie
            #logging.info("El sensor ha sido reiniciado.")
        except Exception as e:
            logging.error(f"Error al intentar reiniciar el sensor: {e}")
            raise
