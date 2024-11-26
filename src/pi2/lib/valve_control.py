import smbus

class QwiicRelayController:
    def __init__(self, i2c_bus=1, relay_addresses=None):
        """
        Inicializa el controlador de los relés SparkFun Qwiic Single Relay.

        :param i2c_bus: Número del bus I2C donde están conectados los módulos de relé.
        :param relay_addresses: Diccionario con los nombres de las válvulas y sus direcciones I2C.
        """
        if relay_addresses is None:
            relay_addresses = {}
        self.bus = smbus.SMBus(i2c_bus)
        self.relay_addresses = relay_addresses

    def activate_relay(self, valve_name):
        """
        Activa el relé asociado a una válvula específica.

        :param valve_name: Nombre de la válvula a activar.
        """
        if valve_name not in self.relay_addresses:
            print(f"Válvula {valve_name} no encontrada en la configuración.")
            return

        address = self.relay_addresses[valve_name]
        try:
            print(f"Activando relé para la válvula {valve_name} en la dirección {hex(address)}...")
            self.bus.write_byte_data(address, 0x00, 0x01)  # Comando para activar el relé
            print(f"Relé para la válvula {valve_name} activado.")
        except Exception as e:
            print(f"Error al activar el relé para la válvula {valve_name}: {e}")

    def deactivate_relay(self, valve_name):
        """
        Desactiva el relé asociado a una válvula específica.

        :param valve_name: Nombre de la válvula a desactivar.
        """
        if valve_name not in self.relay_addresses:
            print(f"Válvula {valve_name} no encontrada en la configuración.")
            return

        address = self.relay_addresses[valve_name]
        try:
            print(f"Desactivando relé para la válvula {valve_name} en la dirección {hex(address)}...")
            self.bus.write_byte_data(address, 0x00, 0x00)  # Comando para desactivar el relé
            print(f"Relé para la válvula {valve_name} desactivado.")
        except Exception as e:
            print(f"Error al desactivar el relé para la válvula {valve_name}: {e}")


# Ejemplo de Uso:

# from lib.valve_control import QwiicRelayController

# # Configuración de las direcciones I2C de los módulos de relé para las válvulas
# relay_addresses = {
#     "valve_1": 0x18,  # Dirección I2C para la válvula 1
#     "valve_2": 0x19   # Dirección I2C para la válvula 2
# }

# # Inicializar el controlador de relés
# relay_controller = QwiicRelayController(i2c_bus=1, relay_addresses=relay_addresses)

# # Activar la válvula 1
# relay_controller.activate_relay("valve_1")

# # Esperar 5 segundos
# import time
# time.sleep(5)

# # Desactivar la válvula 1
# relay_controller.deactivate_relay("valve_1")
