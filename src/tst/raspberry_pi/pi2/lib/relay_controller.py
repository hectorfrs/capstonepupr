# relay_controller_real.py - Controlador de relés utilizando el MUX TCA9548A y el Relay Qwiic Relay.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import qwiic_tca9548a
import qwiic_relay
import time
from modules.logging_manager import LoggingManager
from modules.config_manager import ConfigManager

class RelayControllerReal:
    def __init__(self, config_manager):
        """
        Inicializa el controlador de relés reales utilizando ConfigManager.
        :param config_manager: Instancia de ConfigManager para manejar configuraciones.
        """
        self.config_manager = config_manager
        self.mux = qwiic_tca9548a.QwiicTCA9548A()
        if not self.mux.is_connected():
            raise ConnectionError("No se pudo conectar al MUX TCA9548A.")
        self.relays = {}
        self.initialize_relays()

    def initialize_relays(self):
        """
        Inicializa cada relé basado en la configuración proporcionada.
        """
        relay_config = self.config_manager.get("mux.relays", [])
        if not isinstance(relay_config, list):
            raise ValueError("La configuración de relés debe ser una lista.")

        for relay in relay_config:
            mux_channel = relay.get("mux_channel")
            i2c_address = relay.get("i2c_address")

            if mux_channel is None or i2c_address is None:
                raise ValueError(f"Relay debe tener 'mux_channel' e 'i2c_address' definidos.")

            self.mux.enable_channels(1 << mux_channel)
            relay_instance = qwiic_relay.QwiicRelay(i2c_address)
            if not relay_instance.is_connected():
                raise ConnectionError(f"No se pudo conectar al relé en el canal {mux_channel} (I2C {hex(i2c_address)}).")
            self.relays[mux_channel] = relay_instance
            print(f"[RelayControllerReal] Relay {mux_channel} inicializado en dirección I2C {hex(i2c_address)}.")

    def activate_relay(self, mux_channel, duration, event_id):
        """
        Activa un relé por un tiempo específico.
        :param mux_channel: Canal MUX del relé a activar.
        :param duration: Duración en segundos.
        :param event_id: ID único del evento.
        """
        relay = self.relays.get(mux_channel)
        if not relay:
            raise ValueError(f"Relé en canal {mux_channel} no encontrado.")
        
        print(f"[RelayControllerReal] Activando relay {mux_channel} por {duration} segundos. ID Evento: {event_id}")
        relay.turn_on()
        time.sleep(duration)
        relay.turn_off()
        print(f"[RelayControllerReal] Relay {mux_channel} desactivado. ID Evento: {event_id}")
