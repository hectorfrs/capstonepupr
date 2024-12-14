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
    REG_RESET = 0x80            # Registro de reinicio (en duda)
    REG_CONFIGURATION = 0x04  # Registro para configuración (incluye reset)

    TX_VALID = 0x02             # Buffer de escritura ocupado
    RX_VALID = 0x01             # Datos disponibles para leer
    POLLING_DELAY = 0.05        # Retardo de espera para el buffer de escritura
    

    READY = 0x08     # El sensor está listo (bit específico para "READY")
    BUSY = 0x08      # El sensor está ocupado (bit específico para "BUSY")

    DEVICES = {"AS72651": 0b00, "AS72652": 0b01, "AS72653": 0b10}  # Selección de dispositivos internos

    def __init__(self, i2c_bus=1, address=0x49):
        """
        Inicializa el sensor en el bus I²C.
        :param i2c_bus: Número del bus I²C.
        :param address: Dirección I²C del sensor.
        """
        self.i2c = SMBus(i2c_bus)
        self.address = address
        DELAY = min(self.POLLING_DELAY * attempt, 1)  # Retardo de espera para el buffer de escritura
        logging.info(f"[CONTROLLER] [SENSOR] AS7265x inicializado en dirección {hex(self.address)} en el bus I2C {i2c_bus}.")

    def verify_ready_state(self, retries=5, delay=2):
        """
        Verifica si el sensor está en estado READY después del reinicio.
        Lee el registro REG_STATUS directamente del sensor y revisa si el bit READY está activo.

        :param retries: Número máximo de intentos para verificar el estado READY.
        :param delay: Tiempo (en segundos) entre intentos consecutivos.
        :return: True si el sensor está listo, False en caso contrario.
        """
        for attempt in range(retries):
            reg_status = self._read_status()  # Llama a la función de lectura del estado
            _, _, ready = reg_status
            if ready:
                logging.info("[CONTROLLER] [SENSOR] El sensor está listo para operar.")
                return True
            logging.debug(f"[CONTROLLER] [SENSOR] Intento {attempt + 1}: REG_STATUS leído: {bin(reg_status)} (READY=False)")
            time.sleep(delay)
        logging.error("[CONTROLLER] [SENSOR] El sensor no alcanzó el estado READY después de varios intentos.")
        return False



    def _write_register(self, reg, value):
        """
        Escribe un valor en un registro del sensor utilizando reintentos.
        :param reg: Dirección del registro.
        :param value: Valor a escribir.
        """
        def action():
            # Lógica de escritura
            while True:
                status = self.i2c.read_byte_data(self.I2C_ADDR, self.REG_STATUS)
                if not (status & self.TX_VALID):
                    break
                time.sleep(self.delay)

            self.i2c.write_byte_data(self.I2C_ADDR, self.REG_WRITE, reg | 0x80)
            while True:
                status = self.i2c.read_byte_data(self.I2C_ADDR, self.REG_STATUS)
                if not (status & self.TX_VALID):
                    break
                time.sleep(self.DELAY)

            self.i2c.write_byte_data(self.I2C_ADDR, self.REG_WRITE, value)

        # Usa _attempt_action para ejecutar el proceso con reintentos
        self._attempt_action(action)


    def _read_register(self, reg):
        """
        Lee un valor de un registro del sensor utilizando reintentos.
        :param reg: Dirección del registro.
        :return: Valor leído.
        """
        def action():
            try:
                logging.debug(f"[CONTROLLER] [SENSOR] Iniciando lectura del registro 0x{reg:02X}.")
                # Verifica el estado inicial del sensor
                status = self.i2c.read_byte_data(self.I2C_ADDR, self.REG_STATUS)
                logging.debug(f"[CONTROLLER] [STATUS] REG_STATUS inicial: 0x{status:02X}")
                # Validar si está listo para recibir datos
                if status & self.BUSY:
                    logging.debug("[CONTROLLER] [SENSOR] Sensor ocupado, esperando...")
                    time.sleep(self.DELAY)

                # Si está listo, verifica RX_VALID
                if status & self.RX_VALID:
                    read_val = self.i2c.read_byte_data(self.I2C_ADDR, self.REG_READ)
                    logging.debug(f"[CONTROLLER] [SENSOR] REG_READ valor: 0x{read_val:02X}")

                

                # Espera a que el buffer de escritura esté listo
                while True:
                    status = self.i2c.read_byte_data(self.I2C_ADDR, self.REG_STATUS)
                    logging.debug(f"[CONTROLLER] [SENSOR] REG_STATUS durante TX_VALID: 0x{status:02X}")
                    if not (status & self.TX_VALID):
                        break
                    time.sleep(self.DELAY)

                # Solicita lectura del registro
                self.i2c.write_byte_data(self.I2C_ADDR, self.REG_WRITE, reg)
                logging.debug(f"[CONTROLLER] REG_WRITE enviado: 0x{reg:02X}")
                while True:
                    status = self.i2c.read_byte_data(self.I2C_ADDR, self.REG_STATUS)
                    logging.debug(f"[CONTROLLER] [SENSOR] REG_STATUS durante RX_VALID: 0x{status:02X}")
                    if status & self.RX_VALID:
                        break
                    time.sleep(self.DELAY)

                # Devuelve el valor leído
                read_val = self.i2c.read_byte_data(self.I2C_ADDR, self.REG_READ)
                logging.debug(f"[CONTROLLER] [SENSOR] REG_READ final: 0x{read_val:02X}")
                return read_val
            except OSError as e:
                logging.error(f"[CONTROLLER] [SENSOR] Error durante la lectura del registro 0x{reg:02X}: {e}")
            raise

        # Usa _attempt_action para ejecutar el proceso con reintentos
        return self._attempt_action(action)


    def _write_virtual_register(self, reg, value):
        """
        Escribe en un registro virtual del sensor.
        :param reg: Dirección del registro virtual.
        :param value: Valor a escribir.
        """
        while True:
            tx_valid, _, _ = self._read_status()  # Verifica TX_VALID
            if not tx_valid:
                break
            time.sleep(self.DELAY)
        self._write_register(self.REG_WRITE, reg | 0x80)  # Escribir dirección del registro
        self._write_register(self.REG_WRITE, value)       # Escribir valor
        logging.debug(f"[CONTROLLER] [SENSOR] Intentando escribir {value} en el registro virtual {hex(reg)}.")

    def _read_virtual_register(self, reg):
        """
        Lee un registro virtual del sensor.
        :param reg: Dirección del registro virtual.
        :return: Valor leído del registro.
        """
        while True:
            tx_valid, _, _ = self._read_status()  # Verifica TX_VALID
            if not tx_valid:
                break
            time.sleep(self.DELAY)
        self._write_register(self.REG_WRITE, reg)         # Escribir dirección para leer
        while True:
            _, rx_valid, _ = self._read_status()  # Verifica RX_VALID
            if rx_valid:
                break
            time.sleep(self.DELAY)
        value = self._read_register(self.REG_READ)        # Leer valor
        logging.debug(f"[CONTROLLER] [SENSOR] Registro virtual {hex(reg)} leído con valor {value}.")
        return value

    def _read_status(self):
        """
        Lee el registro de estado y retorna detalles sobre TX_VALID, RX_VALID y READY.
        """
        reg_status = self.i2c.read_byte_data(self.I2C_ADDR, self.REG_STATUS)
        tx_valid = (reg_status & self.TX_VALID) >> 1
        rx_valid = reg_status & self.RX_VALID
        ready = (reg_status & self.READY) >> 3
        logging.debug(f"[CONTROLLER] [SENSOR] REG_STATUS leído: {bin(reg_status)} "
                    f"(TX_VALID={tx_valid}, RX_VALID={rx_valid}, READY={ready})")
        return tx_valid, rx_valid, ready



    def is_ready(self):
        """
        Verifica si el sensor está listo (READY).
        """
        status = self.verify_ready_state()
        ready = not (status & self.TX_VALID) and (status & self.RX_VALID)
        logging.debug(f"[CONTROLLER] [SENSOR] Estado del sensor: READY={ready}, TX_VALID={(status & self.TX_VALID) != 0}, RX_VALID={(status & self.RX_VALID) != 0}")
        return ready


    def _attempt_action(self, action, max_attempts=3, delay=0.05):
        """
        Intenta ejecutar una acción específica con reintentos.
        :param action: Una función lambda o callable que representa la acción a realizar.
        :param max_attempts: Número máximo de intentos permitidos.
        :param delay: Retardo entre intentos fallidos.
        :return: El resultado de la acción si es exitosa.
        :raises: OSError si todos los intentos fallan.
        """
        for attempt in range(1, max_attempts + 1):
            try:
                result = action()
                return result
            except OSError as e:
                logging.warning(f"Intento {attempt}/{max_attempts} fallido: {e}")
                time.sleep(delay)
        raise OSError(f"No se pudo completar la acción después de {max_attempts} intentos.")

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



    def _reset(self):
        """
        Reinicia el sensor AS7265x utilizando el Registro de Configuración.
        """
        try:
            logging.debug("[CONTROLLER] [SENSOR] Ejecutando reinicio del sensor...")
            self.i2c.write_byte_data(self.I2C_ADDR, self.REG_CONFIGURATION, 0x01)  # Reinicio por software
            logging.debug("[CONTROLLER] [SENSOR] Comando de reinicio enviado al sensor.")
            time.sleep(5)  # Esperar para que el reinicio surta efecto
        except Exception as e:
            logging.error(f"[MANAGER] [SENSOR] Error durante el reinicio: {e}")
            raise



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
            logging.info("[CONTROLLER] [SENSOR] Configuraciones ajustadas dinámicamente según los datos.")
        except Exception as e:
            logging.error(f"[CONTROLLER] [SENSOR] Error ajustando configuraciones del sensor: {e}")

