from smbus2 import SMBus
from lib.spectrometer import Spectrometer
import logging


class CustomAS7265x(Spectrometer):
    def __init__(self, name, channel, i2c_address, integration_time=100, gain=3, led_intensity=0, read_interval=3, mux_manager=None, i2c_bus=1, operating_mode=0, enable_interrupts=True):
        """
        Constructor para el sensor AS7265x.

        :param name: Nombre del sensor.
        :param channel: Canal del MUX asociado.
        :param i2c_address: Dirección I2C del sensor.
        :param integration_time: Tiempo de integración en milisegundos.
        :param gain: Ganancia del sensor.
        :param led_intensity: Intensidad del LED (0-255).
        :param read_interval: Intervalo de lectura en segundos.
        :param mux_manager: Administrador del MUX.
        :param i2c_bus: Número del bus I2C.
        :param operating_mode: Modo de operación del sensor (0-3).
        :param enable_interrupts: Habilitar interrupciones (True/False).
        """
        self.name = name
        self.channel = channel
        self.i2c_address = i2c_address  
        self.integration_time = integration_time
        self.gain = gain
        self.led_intensity = led_intensity
        self.read_interval = read_interval
        self.mux_manager = mux_manager
        self.i2c_bus = i2c_bus
        self.operating_mode = operating_mode
        self.enable_interrupts = enable_interrupts

        # Inicializar el bus I2C
        self.bus = SMBus(self.i2c_bus)

        # Inicializar la clase base con el número del bus
        super().__init__(i2c_bus)

        # Configurar el sensor
        self.configure_sensor()



    def configure_sensor(self):
        """
        Configura el sensor AS7265x con el tiempo de integración y ganancia especificados.
        """
        self.mux_manager.select_channel(self.channel)  # Asegúrate de que el canal esté seleccionado

        if not self.is_connected():
            logging.error(f"Sensor no detectado en {hex(self.i2c_address)}. Saltando configuración.")
            return

        retry_attempts = 3
        while retry_attempts > 0:
            try:
                logging.info(f"Configurando el sensor AS7265x en la dirección {hex(self.i2c_address)}...")
                self.set_integration_time(self.integration_time)
                self.set_gain(self.gain)
                logging.info("Configuración del sensor completada.")
                return
            except OSError as e:
                logging.warning(f"Error configurando el sensor: {e}. Reintentando...")
                retry_attempts -= 1
                time.sleep(1)  # Espera antes de reintentar
            except Exception as e:
                logging.error(f"Error configurando el sensor: {e}")
            except OSError as e:
                if e.errno == 121:  # Remote I/O Error
                    # Manejo del error, como reintentar la lectura o registrar el fallo
                    logging.error(f"Remote I/O Error: {e}")
                    retry_attempts -= 1
                    time.sleep(1)  # Espera antes de reintentar
            raise

        raise RuntimeError(f"No se pudo configurar el sensor {self.name} tras varios intentos.")
    
    def set_operating_mode(self, mode):
        """
        Configura el modo de operación del sensor.

        :param mode: Modo de operación (0-3).
        """
        if mode < 0 or mode > 3:
            raise ValueError("El modo de operación debe estar entre 0 y 3.")
        self.write_register(0x07, mode)  # Registro ficticio para el modo de operación
        logging.info(f"Modo de operación configurado: {mode}")

    def enable_sensor_interrupts(self):
        """
        Habilita las interrupciones del sensor.
        """
        self.write_register(0x08, 1)  # Registro ficticio para habilitar interrupciones
        logging.info("Interrupciones del sensor habilitadas.")

    def disable_sensor_interrupts(self):
        """
        Deshabilita las interrupciones del sensor.
        """
        self.write_register(0x08, 0)  # Registro ficticio para deshabilitar interrupciones
        logging.info("Interrupciones del sensor deshabilitadas.")
    
    def is_connected(self):
        """
        Verifica si el sensor AS7265x está conectado al bus I2C.
        
        :return: True si el sensor está conectado, False en caso contrario.
        """
        try:
            self.bus.read_byte(self.i2c_address)  # Intentar leer un byte
            return True
        except OSError:
            return False

    def configure_sensor(self):
        """
        Configura el sensor AS7265x con el tiempo de integración y ganancia especificados.
        """
        self.mux_manager.select_channel(self.channel)  # Asegúrate de que el canal esté seleccionado

        if not self.is_connected():
            logging.error(f"Sensor no detectado en {hex(self.i2c_address)}. Saltando configuración.")
            return

        retry_attempts = 3
        while retry_attempts > 0:
            try:
                logging.info(f"Configurando el sensor AS7265x en la dirección {hex(self.i2c_address)}...")
                self.set_integration_time(self.integration_time)
                self.set_gain(self.gain)
                logging.info("Configuración del sensor completada.")
                return
            except OSError as e:
                logging.warning(f"Error configurando el sensor: {e}. Reintentando...")
                retry_attempts -= 1
                time.sleep(1)  # Espera antes de reintentar
            except Exception as e:
                logging.error(f"Error configurando el sensor: {e}")
                raise

        raise RuntimeError(f"No se pudo configurar el sensor {self.name} tras varios intentos.")

    
    def set_integration_time(self, time_ms):
        """
        Establece el tiempo de integración del sensor.

        :param time_ms: Tiempo de integración en milisegundos (0-255 ms).
        """
        register_value = int(time_ms / 2.8)  # Conversión según la documentación
        self.write_register(0x04, register_value)
        logging.info(f"Tiempo de integración configurado: {time_ms} ms.")

    def set_gain(self, gain_level):
        """
        Establece la ganancia del sensor.

        :param gain_level: Nivel de ganancia (0: 1x, 1: 3.7x, 2: 16x, 3: 64x).
        """
        if gain_level < 0 or gain_level > 3:
            raise ValueError("El nivel de ganancia debe estar entre 0 y 3.")
        self.write_register(0x05, gain_level)
        logging.info(f"Ganancia configurada: {gain_level}x.")

    def write_register(self, register, value):
        """
        Escribe un valor en un registro del sensor.

        :param register: Registro a escribir.
        :param value: Valor a escribir.
        """
        self.bus.write_byte_data(self.i2c_address, register, value)
        logging.info(f"Escribiendo {value} en el registro {hex(register)}.")

    def read_register(self, register):
        """
        Lee un valor de un registro del sensor.

        :param register: Registro a leer.
        :return: Valor leído.
        """
        value = self.bus.read_byte_data(self.i2c_address, register)
        logging.info(f"Valor leído del registro {hex(register)}: {value}")
        return value

    def read_advanced_spectrum(self):
        """
        Lee los datos espectrales directamente desde registros.

        :return: Diccionario con valores espectrales.
        """
        logging.info("Leyendo datos espectrales avanzados...")
        spectrum = {
            "violet": self.read_register(0x08),
            "blue": self.read_register(0x0A),
            "green": self.read_register(0x0C),
            "yellow": self.read_register(0x0E),
            "orange": self.read_register(0x10),
            "red": self.read_register(0x12),
        }
        logging.info(f"Espectro avanzado: {spectrum}")
        return spectrum
    
    def read_temperature(self):
        """
        Lee la temperatura del sensor.
        """
        try:
            temperature = self.read_register(0x06)  # Registro según la documentación
            print(f"Temperatura leída: {temperature} °C")
            return temperature
        except Exception as e:
            print(f"Error leyendo la temperatura: {e}")
            raise
    
    def is_critical(self):
        """
        Determina si el sensor está en un estado crítico.

        :return: True si el sensor está en un estado crítico, False en caso contrario.
        """
        try:
            # Verificar temperatura
            temperature = self.read_temperature()
            if not (-40 <= temperature <= 85):  # Según especificación del sensor
                logging.critical(f"Temperatura crítica detectada en {self.name}: {temperature} °C")
                return True
            
            # Verificar errores de lectura
            read_error_register = 0x07  # Registro de error según la documentación
            error_status = self.read_register(read_error_register)
            if error_status != 0:  # Cualquier valor diferente de 0 indica un error
                logging.critical(f"Error de lectura detectado en {self.name}: {error_status}")
                return True
            
            # (Opcional) Agregar verificaciones adicionales según sea necesario

            return False  # No se detectaron problemas críticos
        except Exception as e:
            logging.critical(f"Error evaluando estado crítico en {self.name}: {e}")
            return True
    
    def power_off(self):
        """
        Apaga el sensor para ahorrar energía.
        """
        try:
            # Simula el apagado del sensor
            logging.info(f"Apagando el sensor {self.name} para ahorro de energía.")
            # Aquí se puede implementar el apagado real si es necesario
        except Exception as e:
            logging.error(f"Error apagando el sensor {self.name}: {e}")
