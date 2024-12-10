# as7265x.py -  Clase extendida para interactuar con el sensor AS7265x.
from smbus2 import SMBus
from lib.spectrometer import Spectrometer
import yaml
import logging


class CustomAS7265x(Spectrometer):
    """
    Clase extendida para interactuar con el sensor AS7265x.
    Combina configuraciones avanzadas y funciones simplificadas para lecturas espectroscópicas.
    """

    def __init__(self, channel, read_interval, name=None, integration_time=100, gain=3, led_intensity=0, mux_manager=None, config_path="/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml"):
        """
        Inicializa el sensor AS7265x usando valores de configuración YAML.

        :param config_path: Ruta al archivo de configuración YAML.
        """
        # # Cargar configuración desde YAML
        # self.name = name # Guardar el nombre del sensor
        #self.config = self.load_config(config_path)

        # # Extraer parámetros del sensor
        # self.i2c_bus = self.config['mux']['i2c_bus']
        # self.i2c_address = 0x49  # Dirección predeterminada del sensor
        # self.channel = channel
        # self.integration_time = self.config['sensors']['as7265x']['channels']['integration_time']
        # self.gain = self.config['sensors']['as7265x']['default_settings']['gain']
        #self.bus = SMBus(self.i2c_bus)
        #self.i2c_bus = self.config['mux']['i2c_bus']
        self.i2c_address = 0x49  # Dirección predeterminada del sensor
        self.name = name
        self.channel = channel
        self.integration_time = integration_time
        self.gain = gain
        self.led_intensity = led_intensity
        self.read_interval = read_interval
        self.mux_manager = mux_manager
        self.i2c_bus = i2c_bus 
        self.bus = SMBus(self.i2c_bus)  

         # Configura más inicializaciones aquí según sea necesario
        logging.info(f"Inicializando {name} en el canal {channel} con:")
        logging.info(f"  - Tiempo de integración: {integration_time} ms")
        logging.info(f"  - Ganancia: {gain}")
        logging.info(f"  - Intensidad LED: {led_intensity}")
        logging.info(f"  - Intervalo de lectura: {read_interval} s")

        # Inicializar el bus I²C
        self.bus = SMBus(self.i2c_bus)

        # Inicializar la biblioteca SparkFun
        #super().__init__(self.bus)
        # Llama al constructor de la clase base con el número de bus I2C
        super().__init__(i2c_bus=self.config['mux']['i2c_bus'])

        # Establecer el nombre del sensor
        self.name = name if name else f"AS7265x_{hex(self.i2c_address)}"

        # Configurar el sensor
        self.configure_sensor()

    @staticmethod
    def load_config(config_path):
        """
        Carga la configuración desde un archivo YAML.

        :param config_path: Ruta al archivo YAML.
        :return: Diccionario con la configuración cargada.
        """
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    
    def is_connected(self):
        """
        Verifica si el sensor AS7265x está conectado al bus I2C.
        
        :return: True si el sensor está conectado, False en caso contrario.
        """
        try:
            with SMBus(self.i2c_bus) as bus:
                bus.read_byte(self.i2c_address)  # Intentar leer un byte
            return True
        except OSError:
            return False
            
    def configure_sensor(self):
        """
        Configura el sensor AS7265x con el tiempo de integración y ganancia especificados.
        """
        if not self.is_connected():
            logging.error(f"Sensor no detectado en {hex(self.i2c_address)}. Saltando configuración.")
            return

        try:
            logging.info(f"Configurando el sensor AS7265x en la dirección {hex(self.i2c_address)}...")
            self.set_integration_time(self.integration_time)
            logging.info(f"Tiempo de integración configurado: {self.integration_time}")
            self.set_gain(self.gain)
            logging.info("Configuración del sensor completada.")
        except Exception as e:
            logging.error(f"Error configurando el sensor: {e}")
            raise


    def read_data(self):
        """
        Simula la lectura de datos del sensor.
        """
        if not self.is_connected():
            logging.error("El sensor no está conectado. No se pueden leer datos.")
            return {}

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

    def read_calibrated_spectrum(self):
        """
        Lee los datos calibrados del espectro usando la biblioteca SparkFun.

        :return: Diccionario con valores espectrales calibrados.
        """
        logging.info("Leyendo datos calibrados del espectro...")
        calibrated_values = super().get_calibrated_values()
        logging.info(f"Espectro calibrado: {calibrated_values}")
        return calibrated_values

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

# # Ejemplo de Uso:

# # Lecturas Calibradas:

# from lib.as7265x import CustomAS7265x

# def main():
#     # Inicializar el sensor
#     sensor = CustomAS7265x(config_path="config/pi1_config.yaml")

#     # Leer espectro calibrado
#     calibrated_data = sensor.read_calibrated_spectrum()
#     print("Datos calibrados:", calibrated_data)

# if __name__ == "__main__":
#     main()


# # Lecturas Avanzadas:
# from lib.as7265x import CustomAS7265x

# def main():
#     sensor = CustomAS7265x(config_path="config/pi1_config.yaml")

#     # Leer datos espectrales avanzados
#     advanced_data = sensor.read_advanced_spectrum()
#     print("Datos avanzados:", advanced_data)

# if __name__ == "__main__":
#     main()
