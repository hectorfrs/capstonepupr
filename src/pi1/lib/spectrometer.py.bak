# spectrometer.py - Clase para interactuar con el SparkFun Triad Spectroscopy Sensor.
import time
from smbus2 import SMBus

class Spectrometer:
    """
    Clase para interactuar con el SparkFun Triad Spectroscopy Sensor.
    """
    # Constantes de dirección y registros
    I2C_ADDR = 0x49
    STATUS_REG = 0x00
    WRITE_REG = 0x01
    READ_REG = 0x02
    TX_VALID = 0x02
    RX_VALID = 0x01
    POLLING_DELAY = 0.05

    def __init__(self, i2c_bus=1):
        """
        Inicializa el espectrómetro en el bus I2C especificado.
        """
        self.i2c = SMBus(i2c_bus)
        # Inicialización del bus I2C

    def read_reg(self, addr):
        """
        Lee un registro del espectrómetro.
        """
        # Verificar si hay datos disponibles para leer
        try:
            status = self.i2c.read_byte_data(self.I2C_ADDR, self.STATUS_REG)
            if status & self.RX_VALID:
                self.i2c.read_byte_data(self.I2C_ADDR, self.READ_REG)

            # Esperar hasta que el registro de escritura esté listo
            while True:
                status = self.i2c.read_byte_data(self.I2C_ADDR, self.STATUS_REG)
                if not (status & self.TX_VALID):
                    break
                time.sleep(self.POLLING_DELAY)

            # Escribir la dirección del registro que queremos leer
            self.i2c.write_byte_data(self.I2C_ADDR, self.WRITE_REG, addr)
            while True:
                status = self.i2c.read_byte_data(self.I2C_ADDR, self.STATUS_REG)
                if status & self.RX_VALID:
                    break
                time.sleep(self.POLLING_DELAY)

            # Leer el valor del registro
            return self.i2c.read_byte_data(self.I2C_ADDR, self.READ_REG)
        except Exception as e:
            print(f"Error leyendo el registro {addr}: {e}")
        raise

    def write_reg(self, addr, data):
        """
        Escribe un valor en un registro del espectrómetro.
        """
        while True:
            status = self.i2c.read_byte_data(self.I2C_ADDR, self.STATUS_REG)
            if not (status & self.TX_VALID):
                break
            time.sleep(self.POLLING_DELAY)

        self.i2c.write_byte_data(self.I2C_ADDR, self.WRITE_REG, addr | 0x80)
        while True:
            status = self.i2c.read_byte_data(self.I2C_ADDR, self.STATUS_REG)
            if not (status & self.TX_VALID):
                break
            time.sleep(self.POLLING_DELAY)

        self.i2c.write_byte_data(self.I2C_ADDR, self.WRITE_REG, data)

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

    def set_gain(self, gain):
        """
        Configura la ganancia.
        """
        devices = ["AS72651", "AS72652", "AS72653"]
        for device in devices:
            self.set_devsel(device)
            config_reg = self.read_reg(0x04)
            config_reg = (config_reg & 0b11001111) | (gain << 4)
            self.write_reg(0x04, config_reg)

    def read_calibrated_spectrum(self):
        """
        Lee el espectro calibrado.
        """
        cal_registers = [
            (0x14, 0x15, 0x16, 0x17), (0x18, 0x19, 0x1a, 0x1b),
            (0x1c, 0x1d, 0x1e, 0x1f), (0x20, 0x21, 0x22, 0x23),
            (0x24, 0x25, 0x26, 0x27), (0x28, 0x29, 0x2a, 0x2b)
        ]
        devices = ["AS72651", "AS72652", "AS72653"]
        cal_values = []

        for device in devices:
            self.set_devsel(device)
            for reg_quad in cal_registers:
                cal = [self.read_reg(r) for r in reg_quad]
                cal_values.append(self.ieee754_to_float(cal))

        return self.reorder_data(cal_values)

    def reorder_data(self, data):
        """
        Ordena los datos espectrales.
        """
        mappings = [
            (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7),
            (8, 8), (13, 9), (14, 11), (9, 10), (10, 12), (15, 13),
            (16, 14), (17, 15), (18, 16), (11, 17), (12, 18)
        ]
        sorted_data = [0] * 18
        for pair in mappings:
            sorted_data[pair[1] - 1] = data[pair[0] - 1]
        return sorted_data

    def set_devsel(self, device):
        """
        Configura el dispositivo activo.
        """
        devsel_bits = {"AS72651": 0b00, "AS72652": 0b01, "AS72653": 0b10}
        if device not in devsel_bits:
            raise ValueError("Dispositivo no válido.")
        self.write_reg(0x4f, devsel_bits[device])

    def set_device_and_write(self, device, addr, data):
        """
        Selecciona el dispositivo y escribe en un registro.
        """
        self.set_devsel(device)
        self.write_reg(addr, data)

    def ieee754_to_float(self, val_array):
        """
        Convierte datos IEEE754 a float.
        """
        c0, c1, c2, c3 = val_array
        full_channel = (c0 << 24) | (c1 << 16) | (c2 << 8) | c3
        sign = (-1) ** ((full_channel >> 31) & 1)
        exponent = (full_channel >> 23) & 0xff
        fraction = full_channel & 0x7fffff
        accum = 1 + sum(((fraction & (1 << bit)) >> bit) / 2 ** (23 - bit) for bit in range(22, -1, -1))
        return sign * accum * (2 ** (exponent - 127))
