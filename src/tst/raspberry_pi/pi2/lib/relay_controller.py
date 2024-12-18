# relay_controller.py - Controlador de relés utilizando el MUX TCA9548A y el Relay Qwiic Relay.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import qwiic_tca9548a
import qwiic_relay
import time
from modules.logging_manager import LoggingManager
from modules.config_manager import ConfigManager

class RelayController:
    """
    Controlador para gestionar relés utilizando un MUX I2C TCA9548A.
    """
    def __init__(self, config_manager, enable_relays=True):
        """
        Inicializa los relés y el MUX utilizando la configuración desde config.yaml.
        :param config_manager: Instancia de ConfigManager para configuraciones centralizadas.
        :param enable_relays: Habilita o deshabilita la funcionalidad de los relés.
        """
        self.config_manager = config_manager
        self.relay_config = config_manager.get("mux.relays", [])
        self.enable_relays = enable_relays

        # Configurar logger centralizado
        self.logger = setup_logger("[RELAY_CONTROLLER]", config_manager.get("logging", {}))

        if not self.enable_relays:
            self.logger.warning("La funcionalidad de los relés está deshabilitada.")
            return

        # Inicializar el MUX
        self.mux = qwiic_tca9548a.QwiicTCA9548A()
        if not self.mux.is_connected():
            self.logger.critical("[MUX] TCA9548A no detectado.")
            raise Exception("[MUX] TCA9548A no detectado.")
        self.logger.info("[MUX] TCA9548A conectado correctamente.")

        # Inicializar los relés
        self.relays = {}
        for index, config in enumerate(self.relay_config):
            mux_channel = config["mux_channel"]
            i2c_address = config["i2c_address"]

            self._select_mux_channel(mux_channel)
            relay = qwiic_relay.QwiicRelay(address=i2c_address)

            if relay.is_connected():
                self.relays[index] = {"mux_channel": mux_channel, "relay": relay}
                self.logger.info(f"[RELAY] Relé {index} conectado en canal MUX {mux_channel}, dirección {hex(i2c_address)}")
            else:
                self.logger.error(f"[RELAY] Error al conectar Relé {index} en canal MUX {mux_channel}, dirección {hex(i2c_address)}")

    def _select_mux_channel(self, channel):
        """
        Activa el canal especificado en el MUX.
        :param channel: Número del canal a activar (0-7).
        """
        if not self.enable_relays:
            self.logger.warning("La funcionalidad de los relés está deshabilitada.")
            return

        if channel < 0 or channel > 7:
            self.logger.error(f"[MUX] Canal inválido: {channel}")
            raise ValueError(f"[MUX] Canal inválido: {channel}")

        self.mux.enable_channels(1 << channel)
        self.logger.info(f"[MUX] Canal {channel} activado.")

    def activate_relay(self, relay_index, duration):
        """
        Activa un relé específico durante un tiempo determinado.
        :param relay_index: Índice del relé.
        :param duration: Tiempo en segundos para activar el relé.
        """
        if not self.enable_relays:
            self.logger.warning("La funcionalidad de los relés está deshabilitada. Activación omitida.")
            return

        if relay_index not in self.relays:
            self.logger.error(f"[RELAY] Índice de relé inválido: {relay_index}")
            raise IndexError(f"[RELAY] Índice de relé inválido: {relay_index}")

        relay_info = self.relays[relay_index]
        self._select_mux_channel(relay_info["mux_channel"])
        relay = relay_info["relay"]

        self.logger.info(f"[RELAY] Activando relé {relay_index} en dirección {hex(relay.address)} por {duration} segundos.")
        relay.set_relay_on()
        time.sleep(duration)
        relay.set_relay_off()
        self.logger.info(f"[RELAY] Relé {relay_index} desactivado.")
