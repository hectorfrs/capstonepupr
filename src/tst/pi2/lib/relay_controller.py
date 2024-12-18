# relay_controller.py - Controlador de relés utilizando el MUX TCA9548A y el Relay Qwiic Relay.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import qwiic_tca9548a
import qwiic_relay
import time
import logging

class RelayController:
    def __init__(self, relay_config):
        """
        Inicializa los relés y el MUX utilizando la configuración desde config.yaml.
        Args:
            relay_config (list): Lista de diccionarios con configuración de los relés.
            Cada elemento tiene: {"mux_channel": int, "i2c_address": int}
        """
        # Inicializar el MUX
        self.mux = qwiic_tca9548a.QwiicTCA9548A()
        if not self.mux.is_connected():
            raise Exception("[MUX] TCA9548A no detectado.")
        print("[MUX] TCA9548A conectado correctamente.")

        # Inicializar los relés
        self.relays = {}
        for index, config in enumerate(relay_config):
            mux_channel = config["mux_channel"]
            i2c_address = config["i2c_address"]

            # Habilitar el canal MUX y verificar el relé
            self._select_mux_channel(mux_channel)
            relay = qwiic_relay.QwiicRelay(address=i2c_address)

            if relay.is_connected():
                self.relays[index] = {"mux_channel": mux_channel, "relay": relay}
                print(f"[RELAY] Relé {index} conectado en canal MUX {mux_channel}, dirección {hex(i2c_address)}")
            else:
                raise Exception(f"[RELAY] Error al conectar Relé {index} en canal MUX {mux_channel}, dirección {hex(i2c_address)}")

    def _select_mux_channel(self, channel):
        """
        Activa el canal especificado en el MUX.
        Args:
            channel (int): Número del canal a activar (0-7).
        """
        if channel < 0 or channel > 7:
            raise ValueError(f"[MUX] Canal inválido: {channel}")
        self.mux.enable_channels(1 << channel)
        print(f"[MUX] Canal {channel} activado.")

    def activate_relay(self, relay_index, duration):
        """
        Activa un relé específico durante un tiempo determinado.
        Args:
            relay_index (int): Índice del relé.
            duration (float): Tiempo en segundos para activar el relé.
        """
        if relay_index not in self.relays:
            raise IndexError(f"[RELAY] Índice de relé inválido: {relay_index}")

        relay_info = self.relays[relay_index]
        self._select_mux_channel(relay_info["mux_channel"])
        relay = relay_info["relay"]

        print(f"[RELAY] Activando relé {relay_index} en dirección {hex(relay.address)} por {duration} segundos.")
        relay.set_relay_on()
        time.sleep(duration)
        relay.set_relay_off()
        print(f"[RELAY] Relé {relay_index} desactivado.")
