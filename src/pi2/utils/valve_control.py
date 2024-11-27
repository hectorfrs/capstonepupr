import smbus


class ValveController:
    """
    Clase para controlar válvulas utilizando un módulo de relé.
    """
    def __init__(self, relay_addresses, i2c_bus=1, trigger_level="high"):
        """
        Inicializa el controlador de válvulas.

        :param relay_addresses: Diccionario con direcciones I2C de los relés.
        :param i2c_bus: Número del bus I2C.
        :param trigger_level: Nivel de disparo del relé ("high" o "low").
        """
        self.bus = smbus.SMBus(i2c_bus)
        self.relay_addresses = relay_addresses
        self.trigger_level = 1 if trigger_level.lower() == "high" else 0

    def activate_valve(self, valve_name):
        """
        Activa la válvula especificada.

        :param valve_name: Nombre de la válvula (clave en relay_addresses).
        """
        if valve_name not in self.relay_addresses:
            raise ValueError(f"Válvula {valve_name} no configurada.")
        print(f"Activando válvula {valve_name}...")
        self.bus.write_byte(self.relay_addresses[valve_name], self.trigger_level)
        print(f"Válvula {valve_name} activada.")

    def deactivate_valve(self, valve_name):
        """
        Desactiva la válvula especificada.

        :param valve_name: Nombre de la válvula (clave en relay_addresses).
        """
        if valve_name not in self.relay_addresses:
            raise ValueError(f"Válvula {valve_name} no configurada.")
        print(f"Desactivando válvula {valve_name}...")
        self.bus.write_byte(self.relay_addresses[valve_name], 1 - self.trigger_level)
        print(f"Válvula {valve_name} desactivada.")
