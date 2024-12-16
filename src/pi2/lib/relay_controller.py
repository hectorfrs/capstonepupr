# relay_controller.py - Controlador de relay para Raspberry Pi.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024

import qwiic_tca9548a
import qwiic_relay
import time
import sys
import logging

class RelayController:
    def __init__(self, relay_config):
        """
        Inicializa los Relays y el MUX.
        Args:
            relay_config (dict): Diccionario con la configuración de los Relays y canales del MUX.
                                Formato: {relay_index: {"mux_channel": int, "i2c_address": int}}
        """
        # Inicializar el MUX
        self.mux = qwiic_tca9548a.QwiicTCA9548A()
        if not self.mux.is_connected():
            raise Exception("[CONTROLLER] [RELAY] MUX TCA9548A no detectado.")
        logging.info("[CONTROLLER] [RELAY] MUX TCA9548A conectado correctamente.")

        # Inicializar los Relays
        self.relays = {}
        for index, config in relay_config.items():
            mux_channel = config["mux_channel"]
            i2c_address = config["i2c_address"]
            self._select_mux_channel(mux_channel)
            relay = qwiic_relay.QwiicRelay(address=i2c_address)
            if relay.begin() == False:
                raise Exception(f"[CONTROLLER] [RELAY] Error al inicializar Relay {index} en canal MUX {mux_channel}, dirección {hex(i2c_address)}")
                print("The Qwiic Relay isn't connected to the system. Please check your connection", \
            file=sys.stderr)
            if relay.connected:
                self.relays[index] = {"mux_channel": mux_channel, "relay": relay}
                logging.info(f"[CONTROLLER] [RELAY] Relay {index} conectado en canal MUX {mux_channel}, dirección {hex(i2c_address)}")
            else:
                raise Exception(f"[CONTROLLER] [RELAY] Error al conectar Relay {index} en canal MUX {mux_channel}, dirección {hex(i2c_address)}")

    def _select_mux_channel(self, channel):
        """
        Activa el canal especificado en el MUX.
        Args:
            channel (int): Número del canal a activar (0-7).
        """
        if channel < 0 or channel > 7:
            raise ValueError(f"[CONTROLLER] [RELAY] Canal MUX inválido: {channel}")
        self.mux.enable_channels(1 << channel)
        logging.info(f"[CONTROLLER] [RELAY] Canal MUX {channel} activado.")

    def activate_relay(self, relay_index, duration):
        """
        Activa un Relay específico durante un tiempo determinado.
        Args:
            relay_index (int): Índice del Relay.
            duration (float): Tiempo en segundos para activar el Relay.
        """
        if relay_index not in self.relays:
            raise IndexError(f"Índice de Relay inválido: {relay_index}")
        relay_info = self.relays[relay_index]
        self._select_mux_channel(relay_info["mux_channel"])
        relay = relay_info["relay"]
        logging.info(f"[CONTROLLER] [RELAY] Activando Relay {relay_index} en dirección {hex(relay.address)} por {duration} segundos.")
        relay.turn_on()
        time.sleep(duration)
        relay.turn_off()
        logging.info(f"[CONTROLLER] [RELAY] Relay {relay_index} desactivado.")
