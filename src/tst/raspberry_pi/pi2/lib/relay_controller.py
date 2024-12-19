# relay_controller.py
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import smbus2
import time
import logging

class RelayController:
    """
    Controlador para manejar relés a través de un MUX I2C.
    """

    def __init__(self, config):
        """
        Inicializa el controlador de relés.
        
        :param config: Configuración proveniente de config.yaml.
        """
        self.logger = logging.getLogger("[RELAY_CONTROLLER]")
        self.relays = config.get("mux", {}).get("relays", [])
        self.activation_time_min = config.get("mux", {}).get("activation_time_min", 0.5)
        self.activation_time_max = config.get("mux", {}).get("activation_time_max", 3)

        # Inicializar bus I2C
        self.i2c_bus = config.get("mux", {}).get("i2c_bus", 1)
        self.bus = smbus2.SMBus(self.i2c_bus)

        self.logger.info("[RelayController] Controlador inicializado.")

    def activate_relay(self, relay_index, duration, event_id=None):
        """
        Activa un relé específico por un tiempo determinado.
        
        :param relay_index: Índice del relé (0 para PET, 1 para HDPE, etc.).
        :param duration: Duración de la activación en segundos.
        :param event_id: ID del evento asociado.
        """
        if relay_index < 0 or relay_index >= len(self.relays):
            self.logger.error(f"[RelayController] Índice de relay inválido: {relay_index}.")
            return

        relay = self.relays[relay_index]
        mux_channel = relay.get("mux_channel")
        i2c_address = relay.get("i2c_address")

        if mux_channel is None or i2c_address is None:
            self.logger.error(f"[RelayController] Configuración faltante para el relay {relay_index}.")
            return

        # Activar el canal del MUX
        try:
            self.logger.info(f"[RelayController] Activando relay {relay_index} en canal {mux_channel}. ID Evento: {event_id}")
            self._set_mux_channel(mux_channel)

            # Enviar comando de activación
            self.bus.write_byte(i2c_address, 0x01)  # Comando de activación (ejemplo)

            # Mantener activo el relé por el tiempo especificado
            time.sleep(duration)

            # Desactivar el relé
            self.bus.write_byte(i2c_address, 0x00)  # Comando de desactivación (ejemplo)
            self.logger.info(f"[RelayController] Relay {relay_index} desactivado. ID Evento: {event_id}")
        except Exception as e:
            self.logger.error(f"[RelayController] Error al controlar el relay {relay_index}: {e}")

    def _set_mux_channel(self, channel):
        """
        Selecciona un canal en el MUX I2C.
        
        :param channel: Canal a activar.
        """
        try:
            self.bus.write_byte(0x70, 1 << channel)
            self.logger.info(f"[RelayController] Canal del MUX activado: {channel}.")
        except Exception as e:
            self.logger.error(f"[RelayController] Error al configurar el canal del MUX: {e}")
