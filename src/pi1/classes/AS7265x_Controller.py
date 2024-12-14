# AS7265x_Controller.py - Clase para manejar el sensor AS7265x utilizando la biblioteca Qwiic I2C.
# Desarrollado por Héctor F. Rivera Santiago
# copyright (c) 2024

from smbus2 import SMBus
import time
import logging

# Configurar logging para el módulo
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class SENSOR_AS7265x:
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

    DEVICES = {"AS72651": 0b00, "AS72652": 0b01, "AS72653": 0b10}  # Selección de dispositivos internos

    def __init__(self, i2c_bus=1, address=0x49):
        """
        Inicializa el sensor en el bus I²C.
        :param i2c_bus: Número del bus I²C.
        :param address: Dirección I²C del sensor.
        """
        self.i2c = SMBus(i2c_bus)
        self.address = address

        logging.info(f"[CONTROLLER] [SENSOR] AS7265x inicializado en dirección {hex(self.address)} en el bus I2C {i2c_bus}.")

    def _write_register(self, reg, value):
        """
        Escribe un valor en un registro del sensor.
        :param reg: Dirección del registro.
        :param value: Valor a escribir.
        """
        while True:
            status = self.i2c.read_byte_data(self.I2C_ADDR, self.REG_STATUS)
            if not (status & self.TX_VALID):
                break
            time.sleep(self.POLLING_DELAY)

        self.i2c.write_byte_data(self.I2C_ADDR, self.REG_WRITE, reg | 0x80)
        while True:
            status = self.i2c.read_byte_data(self.I2C_ADDR, self.REG_STATUS)
            if not (status & self.TX_VALID):
                break
            time.sleep(self.POLLING_DELAY)

        self.i2c.write_byte_data(self.I2C_ADDR, self.REG_WRITE, value)

    def _read_register(self, reg):
        """
        Lee un valor de un registro del sensor.
        :param reg: Dirección del registro.
        :return: Valor leído.
        """
        try:
            status = self.i2c.read_byte_data(self.I2C_ADDR, self.REG_STATUS)
            if status & self.RX_VALID:
                self.i2c.read_byte_data(self.I2C_ADDR, self.REG_READ)

            while True:
                status = self.i2c.read_byte_data(self.I2C_ADDR, self.REG_STATUS)
                if not (status & self.TX_VALID):
                    break 
                time.sleep(self.POLLING_DELAY)

            self.i2c.write_byte_data(self.I2C_ADDR, self.REG_WRITE, reg)
            while True:
                status = self.i2c.read_byte_data(self.I2C_ADDR, self.REG_STATUS)
                if status & self.RX_VALID:
                    break
                time.sleep(self.POLLING_DELAY)

            return self.i2c.read_byte_data(self.I2C_ADDR, self.REG_READ)
            return self._attempt_action(lambda: self.i2c.read_byte_data(self.I2C_ADDR, reg))
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
            time.sleep(self.POLLING_DELAY)                                # Esperar hasta que el buffer de escritura esté listo
        self._write_register(self.REG_WRITE, reg | 0x80)    # Escribir dirección del registro
        self._write_register(self.REG_WRITE, value)         # Escribir valor
        logging.debug(f"[CONTROLLER] [SENSOR] Intentando escribir {value} en el registro virtual {hex(reg)}.")

    def _read_virtual_register(self, reg):
        """
        Lee un registro virtual del sensor.
        :param reg: Dirección del registro virtual.
        :return: Valor leído del registro.
        """
        while self._read_status() & self.TX_VALID:
            time.sleep(self.POLLING_DELAY)                                # Esperar hasta que el buffer de escritura esté listo
        self._write_register(self.REG_WRITE, reg)           # Escribir dirección para leer
        while not (self._read_status() & self.RX_VALID):
            time.sleep(self.POLLING_DELAY)                                # Esperar hasta que haya datos disponibles
        value = self._read_register(self.REG_READ)          # Leer valor
        logging.debug(f"[CONTROLLER] [SENSOR] Registro virtual {hex(reg)} leído con valor {value}.")
        return value

    def _read_status(self):
        """
        Lee el estado del sensor.
        :return: Valor del registro de estado.
        """
        return self._read_register(self.REG_STATUS)

    def _attempt_action(self, action, max_attempts=3, delay=0.05):
        """
        Intenta ejecutar una acción específica (lectura/escritura) con reintentos en caso de fallos.
        :param action: Función que realiza la acción.
        :param max_attempts: Número máximo de intentos.
        :param delay: Tiempo de espera entre intentos.
        """
        for attempt in range(max_attempts):
            try:
                return action()
            except OSError as e:
                logging.warning(f"Intento {attempt + 1}/{max_attempts} fallido: {e}")
                time.sleep(delay)
        raise OSError("No se pudo completar la acción después de múltiples intentos.")

    def configure(self, integration_time, gain, mode):
        """
        Configura el sensor con parámetros básicos.
        :param integration_time: Tiempo de integración (1-255).
        :param gain: Ganancia (0=1x, 1=3.7x, 2=16x, 3=64x).
        :param mode: Modo de operación (0-3).
        """
        if not (1 <= integration_time <= 255):
            raise ValueError("[CONTROLLER] [SENSOR] El tiempo de integración debe estar entre 1 y 255.")
        if gain not in [0, 1, 2, 3]:
            raise ValueError("[CONTROLLER] [SENSOR] Ganancia no válida.")
        if mode not in [0, 1, 2, 3]:
            raise ValueError("[CONTROLLER] [SENSOR] Modo no válido.")
        try:
            self._write_virtual_register(0x05, integration_time) # Configurar tiempo de integración
            config = self._read_virtual_register(0x04)           # Leer configuración actual
            logging.info(f"[CONTROLLER] [SENSOR] Configuración actual: {bin(config)}")
            config = (config & 0b11001111) | (gain << 4)         # Ajustar ganancia
            logging.info(f"[CONTROLLER] [SENSOR] Configurando ganancia: {gain} (valor ajustado: {bin(config)}).")
            self._write_virtual_register(0x04, config)           # Escribir nueva configuración
            logging.info(f"[CONTROLLER] [SENSOR] Configurando modo de operación: {mode}.")
            self._write_virtual_register(0x07, mode)             # Configurar modo de operación
            logging.info("[CONTROLLER] [SENSOR] Configuración completada exitosamente.")
        except Exception as e:
            logging.error(f"[CONTROLLER] [SENSOR] Error durante la configuración: {e}")
        raise

    def set_devsel(self, device):
        """
        Selecciona el dispositivo interno del sensor.
        :param device: Dispositivo a seleccionar (AS72651(NIR), AS72652(VIS), AS72653(UV)).
        """
        if device not in self.DEVICES:
            raise ValueError(f"[CONTROLLER] [SENSOR] Dispositivo {device} no válido. Seleccione entre {list(self.DEVICES.keys())}.")
        
        self._write_virtual_register(0x4F, self.DEVICES[device])
        selected_device = self._read_virtual_register(0x4F)
        if selected_device != self.DEVICES[device]:
            raise RuntimeError(f"[CONTROLLER] [SENSOR] Error al seleccionar el dispositivo {device}.")
        
        logging.info(f"[CONTROLLER] [SENSOR] Dispositivo seleccionado: {device}.")

    def _read_calibrated_values(self, device):
        cal_registers = [
            (0x14, 0x15, 0x16, 0x17), (0x18, 0x19, 0x1a, 0x1b),
            (0x1c, 0x1d, 0x1e, 0x1f), (0x20, 0x21, 0x22, 0x23),
            (0x24, 0x25, 0x26, 0x27), (0x28, 0x29, 0x2a, 0x2b)
        ]
        cal_values = []
        self.set_devsel(device)
        for reg_quad in cal_registers:
            cal = [self._read_register(r) for r in reg_quad]
            cal_values.append(self.ieee754_to_float(cal))
        return self.reorder_data(cal_values)

    def read_calibrated_spectrum(self):
        """
        Lee el espectro calibrado junto con las longitudes de onda.
        """
        wavelengths_nm = [
            410, 435, 460, 485, 510, 535, 560, 585, 610,
            645, 680, 705, 730, 760, 810, 860, 900, 940
        ]
        devices = ["AS72651", "AS72652", "AS72653"]

        all_cal_values = []
        for device in devices:
            all_cal_values.extend(self._read_calibrated_values(device))
        
        spectrum = {"wavelengths": wavelengths_nm, "calibrated_values": all_cal_values}
        logging.info(f"[CONTROLLER] [SENSOR] Espectro calibrado leído: {spectrum}")
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
        devices = ["AS72651", "AS72652", "AS72653"]

        spectral_data = {device: {color: 0 for color in wavelengths} for device in devices}

        for device in devices:
            self.set_devsel(device)  # Selecciona el dispositivo
            for i, reg_pair in enumerate(raw_registers):
                high_byte = self._read_register(reg_pair[0])
                low_byte = self._read_register(reg_pair[1])
                if high_byte is None or low_byte is None:
                    logging.error(f"[CONTROLLER] [SENSOR] Error al leer los registros {reg_pair} para {device_name}")
                value = (high_byte << 8) | low_byte
                spectral_data[device][wavelengths[i]] = value

                # value = (self._read_register(0x10) << 8) | self._read_register(0x11)
                # logging.info(f"Registro Orange leído directamente: {value}")
        return spectral_data
        pass

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
            self._write_register(0x05, time)

    def set_gain(self, gain):
        """
        Configura la ganancia.
        """
        devices = ["AS72651", "AS72652", "AS72653"]
        for device in devices:
            self.set_devsel(device)
            config_reg = self._read_register(0x04)
            config_reg = (config_reg & 0b11001111) | (gain << 4)
            self._write_register(0x04, config_reg)

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

    def reset(self):
        """
        Reinicia el sensor AS7265x utilizando el bit de reset.
        """
        try:
            self._write_virtual_register(0x04, 0x02)  # Registro de control: bit de reinicio
            time.sleep(1)  # Esperar 1 segundo para que el sensor se reinicie
            #logging.info("El sensor ha sido reiniciado.")
        except Exception as e:
            logging.error(f"[SENSOR] Error al intentar reiniciar el sensor: {e}")
            raise
        pass

    def adjust_sensor_settings(self):
        """
        Ajusta el tiempo de integración y la ganancia dinámicamente según los datos actuales.
        """
        try:
            raw_data = self.read_raw_spectrum()
            max_value = max(raw_data.values())
            if max_value < 100:
                self.set_integration_time(500)  # Aumenta el tiempo de integración
                self.set_gain(4)  # Incrementa la ganancia
            elif max_value > 2000:
                self.set_integration_time(100)  # Reduce el tiempo de integración
                self.set_gain(1)  # Reduce la ganancia
            logging.info("[SENSOR] Configuraciones ajustadas dinámicamente según los datos.")
        except Exception as e:
            logging.error(f"[SENSOR] Error ajustando configuraciones del sensor: {e}")

