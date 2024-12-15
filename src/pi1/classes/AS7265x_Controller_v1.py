from smbus2 import SMBus
import time
import logging

# Configuración del logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Dirección del sensor
SENSOR_ADDRESS = 0x49

# ------------------- Registros del AS7265x -------------------

# Estado y Control
REG_STATUS = 0x00              # Indica el estado del sensor (bits para busy, data ready, error)
REG_WRITE = 0x01               # Registro de escritura para datos de control
REG_READ = 0x02                # Registro de lectura para datos de respuesta

# Información del Dispositivo
DEVICE_TYPE = 0x03             # Indica el tipo de dispositivo conectado (AS72651, AS72652, AS72653)
HW_VERSION = 0x04              # Versión de hardware del dispositivo

# Configuración
INTEGRATION_TIME = 0x05        # Configura el tiempo de integración en escalas de 2.8 ms
GAIN_SETTING = 0x04            # Configura la ganancia (1x, 3.7x, 16x, 64x)
MODE_CONTROL = 0x07            # Configura el modo operativo: apagado, continuo o automático

# Datos
DATA_REGISTER_START = 0x08     # Dirección inicial de los datos crudos del espectrómetro
DATA_REGISTER_END = 0x0F       # Dirección final de los datos crudos del espectrómetro

# Selección de Dispositivos Internos
DEVICE_SELECT = 0x4F           # Selección del dispositivo interno: UV, VIS o NIR

# Sensores Adicionales
TEMP_SENSOR = 0x50             # Lectura del sensor de temperatura

# Control de LEDs e Interrupciones
LED_CONTROL = 0x51             # Control de los LEDs de iluminación
INTERRUPT_CONTROL = 0x52       # Configuración de interrupciones: habilitar o deshabilitar

# Dispositivos internos
DEVICES = {"AS72651": 0b00, "AS72652": 0b01, "AS72653": 0b10}  # UV, VIS, NIR

class SENSOR_AS7265x:

    def __init__(self, i2c_bus=1, address=0x49):
        self.bus = smbus.SMBus(i2c_bus)
        self.address = address

    # ------------------- Operaciones Básicas -------------------
    def write_register(self, register, value):
        """Escribe en un registro con reintentos y logging."""
        retries = 3
        for attempt in range(retries):
            try:
                self.bus.write_byte_data(self.address, register, value)
                logging.debug(f"[CONTROLLER] [SENSOR] Escrito en registro {hex(register)}: {hex(value)}")
                return
            except Exception as e:
                logging.warning(f"Error escribiendo en registro {hex(register)} (Intento {attempt + 1}/{retries}): {e}")
                time.sleep(0.1)
        raise Exception(f"Fallo al escribir en el registro {hex(register)} tras {retries} intentos.")

    def read_register(self, register):
        """Lee un registro con reintentos y logging."""
        retries = 3
        for attempt in range(retries):
            try:
                value = self.bus.read_byte_data(self.address, register)
                logging.debug(f"Leído de registro {hex(register)}: {hex(value)}")
                return value
            except Exception as e:
                logging.warning(f"Error leyendo de registro {hex(register)} (Intento {attempt + 1}/{retries}): {e}")
                time.sleep(0.1)
        raise Exception(f"Fallo al leer el registro {hex(register)} tras {retries} intentos.")

    # ------------------- Funciones de Configuración -------------------
    def reset_sensor(self):
        """Resetea el sensor escribiendo en el registro de control."""
        self.write_register(0x04, 0x01)
        logging.info("Sensor reseteado.")
        time.sleep(1)  # Tiempo para reiniciar

    def configure_integration_time(self, time_ms):
        """Configura el tiempo de integración en el sensor."""
        integration_time = int(time_ms / 2.8)
        self.write_register(0x05, integration_time)
        logging.info(f"Tiempo de integración configurado: {time_ms} ms")

    def configure_gain(self, gain):
        """Configura la ganancia del sensor."""
        valid_gains = {1: 0x00, 3.7: 0x01, 16: 0x02, 64: 0x03}
        if gain not in valid_gains:
            raise ValueError("Ganancia no válida. Opciones: 1, 3.7, 16, 64")
        self.write_register(0x04, valid_gains[gain])
        logging.info(f"Ganancia configurada: {gain}x")

    def configure_mode(self, mode):
        """Configura el modo operativo del sensor."""
        valid_modes = {0: 0x00, 1: 0x01, 2: 0x02}
        if mode not in valid_modes:
            raise ValueError("Modo no válido. Opciones: 0 (apagado), 1 (continuo), 2 (automático)")
        self.write_register(0x07, valid_modes[mode])
        logging.info(f"Modo configurado: {mode}")

    def select_device(self, device_id):
        """Selecciona el dispositivo interno (UV, VIS, NIR)."""
        self.write_register(0x4F, device_id)
        selected = self.read_register(0x4F)
        if selected != device_id:
            raise Exception(f"Fallo al seleccionar el dispositivo interno. Esperado: {device_id}, Obtenido: {selected}")
        logging.info(f"Dispositivo interno seleccionado: {device_id}")

    # ------------------- Funciones de Lectura -------------------
    def read_raw_data(self):
        """Lee los datos crudos del sensor."""
        data = []
        for reg in range(0x08, 0x10):
            value = self.read_register(reg)
            data.append(value)
        logging.info(f"Datos crudos leídos: {data}")
        return data

    def read_status(self):
        """Lee el estado del sensor."""
        status = self.read_register(0x00)
        logging.info(f"Estado del sensor (REG_STATUS): {bin(status)}")
        return status

    def read_temperature(self):
        """Lee la temperatura del sensor."""
        temp = self.read_register(0x50)
        logging.info(f"Temperatura del sensor: {temp}°C")
        return temp

    # ------------------- Funciones de Diagnóstico -------------------
    def run_diagnostics(self):
        """Ejecuta diagnósticos básicos en el sensor."""
        logging.info("Iniciando diagnóstico del sensor...")
        self.read_status()
        self.read_temperature()
        self.read_raw_data()

    # ------------------- Control de LEDs -------------------
    def control_led(self, enable):
        """Controla el estado de los LEDs del sensor."""
        value = 0xFF if enable else 0x00
        self.write_register(0x51, value)
        logging.info(f"LEDs {'encendidos' if enable else 'apagados'}.")

# ------------------- Ejemplo de Uso -------------------
# if __name__ == "__main__":
#     sensor = AS7265xController()
#     try:
#         sensor.reset_sensor()
#         sensor.configure_integration_time(100)
#         sensor.configure_gain(3.7)
#         sensor.configure_mode(1)
#         sensor.select_device(0x00)  # Selecciona NIR
#         sensor.run_diagnostics()
#         sensor.control_led(True)
#     except Exception as e:
#         logging.error(f"Error durante la ejecución: {e}")
