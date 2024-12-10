from smbus2 import SMBus
from lib.spectrometer import Spectrometer
import logging


class CustomAS7265x(Spectrometer):
    def __init__(self, name, channel, integration_time=100, gain=3, led_intensity=0, read_interval=3, mux_manager=None, i2c_bus=1, i2c_address=0x49):
        """
        Constructor para el sensor AS7265x.

        :param name: Nombre del sensor.
        :param channel: Canal del MUX asociado.
        :param integration_time: Tiempo de integración en milisegundos.
        :param gain: Ganancia del sensor.
        :param led_intensity: Intensidad del LED (0-255).
        :param read_interval: Intervalo de lectura en segundos.
        :param mux_manager: Administrador del MUX.
        :param i2c_bus: Número del bus I2C.
        :param i2c_address: Dirección I2C del sensor (predeterminada 0x49).
        """
        self.name = name
        self.channel = channel
        self.integration_time = integration_time
        self.gain = gain
        self.led_intensity = led_intensity
        self.read_interval = read_interval
        self.mux_manager = mux_manager
        self.i2c_bus = i2c_bus  # Asigna el número de bus I2C
        self.i2c_address = i2c_address  # Dirección I2C del sensor
        self.bus = SMBus(self.i2c_bus)  # Inicializa el bus I2C

        # Mensajes de inicialización para depuración
        logging.info(f"Inicializando {name} en el canal {channel} con:")
        logging.info(f"  - Tiempo de integración: {integration_time} ms")
        logging.info(f"  - Ganancia: {gain}")
        logging.info(f"  - Intensidad LED: {led_intensity}")
        logging.info(f"  - Intervalo de lectura: {read_interval} s")

        # Llama al constructor de la clase base
        super().__init__(i2c_bus=self.i2c_bus)

        # Configurar el sensor
        self.configure_sensor()


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
        retry_attempts = 3
        while retry_attempts > 0:
            try:
                logging.info(f"Configurando el sensor AS7265x en la dirección {hex(self.i2c_address)}...")
                self.set_integration_time(self.integration_time)
                self.set_gain(self.gain)
                logging.info("Configuración del sensor completada.")
                break
            except OSError as e:
                logging.warning(f"Error configurando el sensor: {e}. Reintentando...")
                retry_attempts -= 1
                time.sleep(1)  # Espera antes de reintentar
            except Exception as e:
                logging.error(f"Error configurando el sensor: {e}")
                raise
        else:
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
