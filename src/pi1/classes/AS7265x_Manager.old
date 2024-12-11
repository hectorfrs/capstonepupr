# AS7265xManager.py - Clase para manejar el sensor AS7265x utilizando la biblioteca Qwiic I2C.
# Desarrollado por Héctor F. Rivera Santiago
# copyright (c) 2024

import qwiic
import time
import logging

# Configurar el logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class AS7265xManager:
    """
    Clase para manejar el sensor AS7265x utilizando la biblioteca Qwiic I2C.
    Combina funcionalidades avanzadas y soporte completo para los tres sensores (AS72651, AS72652, AS72653).
    """
    I2C_ADDR = 0x49  # Dirección I2C predeterminada del AS7265x
    REG_STATUS = 0x00
    REG_WRITE = 0x01
    REG_READ = 0x02

    # Bits de estado
    TX_VALID = 0x02
    RX_VALID = 0x01

    def __init__(self, address=I2C_ADDR):
        """
        Inicializa el sensor AS7265x.
        :param address: Dirección I2C del sensor.
        """
        self.sensor = qwiic.QwiicAS7265x()

        if not self.sensor.connected:
            logging.error(f"No se puede conectar al sensor en la dirección {hex(address)}")
            raise ConnectionError(f"No se puede conectar al sensor en la dirección {hex(address)}")
        logging.info(f"Sensor AS7265x conectado en la dirección {hex(address)}")

    def _write_virtual_register(self, reg, value):
        """
        Escribe en un registro virtual del sensor.
        """
        while self._read_status() & self.TX_VALID:
            time.sleep(0.01)
        self.sensor.writeCommand(self.REG_WRITE, reg | 0x80)
        self.sensor.writeCommand(self.REG_WRITE, value)
        logging.info(f"Registro virtual {hex(reg)} configurado con valor {value}")

    def _read_virtual_register(self, reg):
        """
        Lee un registro virtual del sensor.
        """
        while self._read_status() & self.TX_VALID:
            time.sleep(0.01)
        self.sensor.writeCommand(self.REG_WRITE, reg)
        while not (self._read_status() & self.RX_VALID):
            time.sleep(0.01)
        value = self.sensor.readCommand(self.REG_READ)
        logging.info(f"Leído del registro virtual {hex(reg)}: {value}")
        return value

    def _read_status(self):
        """
        Lee el registro de estado del sensor.
        """
        status = self.sensor.readCommand(self.REG_STATUS)
        logging.debug(f"Estado del sensor leído: {bin(status)}")
        return status

    def configure(self, integration_time, gain, mode):
        """
        Configura el sensor con tiempo de integración, ganancia y modo de operación.
        """
        self._write_virtual_register(0x05, integration_time)
        config = self._read_virtual_register(0x04)
        config = (config & 0b11001111) | (gain << 4)
        self._write_virtual_register(0x04, config)
        self._write_virtual_register(0x07, mode)
        logging.info("Sensor configurado correctamente")

    def set_devsel(self, device):
        """
        Selecciona el dispositivo activo (AS72651, AS72652, AS72653).
        """
        devsel_bits = {"AS72651": 0b00, "AS72652": 0b01, "AS72653": 0b10}
        if device not in devsel_bits:
            raise ValueError("Dispositivo no válido.")
        self._write_virtual_register(0x4F, devsel_bits[device])
        logging.info(f"Dispositivo seleccionado: {device}")

    def read_calibrated_spectrum(self):
        """
        Lee el espectro calibrado de los tres sensores y lo reordena.
        """
        devices = ["AS72651", "AS72652", "AS72653"]
        spectrum = []

        for device in devices:
            self.set_devsel(device)
            for reg in range(0x14, 0x2C, 2):
                msb = self._read_virtual_register(reg)
                lsb = self._read_virtual_register(reg + 1)
                value = (msb << 8) | lsb
                spectrum.append(value / 1000.0)

        reordered_spectrum = self._reorder_data(spectrum)
        logging.info(f"Espectro calibrado leído y reordenado: {reordered_spectrum}")
        return reordered_spectrum

    def _reorder_data(self, data):
        """
        Reordena los datos espectrales según las especificaciones del sensor.
        """
        mappings = [
            (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7),
            (8, 8), (13, 9), (14, 11), (9, 10), (10, 12), (15, 13),
            (16, 14), (17, 15), (18, 16), (11, 17), (12, 18)
        ]
        reordered_data = [0] * 18
        for pair in mappings:
            reordered_data[pair[1] - 1] = data[pair[0] - 1]
        return reordered_data

    def read_raw_data(self):
        """
        Lee los datos crudos del espectro de los tres sensores.
        """
        devices = ["AS72651", "AS72652", "AS72653"]
        raw_data = []

        for device in devices:
            self.set_devsel(device)
            for reg in range(0x08, 0x20, 2):
                msb = self._read_virtual_register(reg)
                lsb = self._read_virtual_register(reg + 1)
                value = (msb << 8) | lsb
                raw_data.append(value)

        logging.info(f"Datos crudos leídos: {raw_data}")
        return raw_data

    def ieee754_to_float(self, val_array):
        """
        Convierte datos IEEE754 a formato float.
        """
        c0, c1, c2, c3 = val_array
        full_channel = (c0 << 24) | (c1 << 16) | (c2 << 8) | c3
        sign = (-1) ** ((full_channel >> 31) & 1)
        exponent = (full_channel >> 23) & 0xff
        fraction = full_channel & 0x7fffff
        accum = 1 + sum(((fraction & (1 << bit)) >> bit) / 2 ** (23 - bit) for bit in range(22, -1, -1))
        return sign * accum * (2 ** (exponent - 127))
