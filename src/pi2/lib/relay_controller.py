# relay_controller.py - Controlador de relay para Raspberry Pi.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024

import qwiic_relay
import time
import sys
import logging

class RelayController:
    def __init__(self, relay_addresses):
        """
        Inicializa los relays con las direcciones I2C proporcionadas.
        Args:
            relay_addresses (list): Lista de direcciones I2C para los relays.
        """
        self.relays = []
        for address in relay_addresses:
            relay = qwiic_relay.QwiicRelay(address=address)
            if relay.connected:
                self.relays.append(relay)
                logging.info(f"[CONTROLLER] [RELAY] Relay conectado en dirección: {hex(address)}")
            else:
                raise Exception(f"[CONTROLLER] [RELAY] Error al conectar relay en dirección: {hex(address)}")

    def activate_relay(self, relay_index, duration):
        """
        Activa un relay específico durante un tiempo determinado.
        Args:
            relay_index (int): Índice del relay en la lista (0 para el primer relay, 1 para el segundo).
            duration (float): Tiempo en segundos para activar el relay.
        """
        if relay_index < 0 or relay_index >= len(self.relays):
            raise IndexError(f"[CONTROLLER] [RELAY] Índice de relay inválido: {relay_index}")
        relay = self.relays[relay_index]
        logging.info(f"[CONTROLLER] [RELAY] Activando relay en dirección {hex(relay.address)} por {duration} segundos.")
        relay.turn_on()
        time.sleep(duration)
        relay.turn_off()
        logging.info(f"[CONTROLLER] [RELAY] Relay en dirección {hex(relay.address)} desactivado.")
