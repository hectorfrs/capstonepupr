import qwiic_relay
import time
from utils.json_manager import generate_json, save_json

class ValveControl:
    """
    Clase para controlar las válvulas de presión utilizando módulos de relé SparkFun Qwiic.
    """
    def __init__(self, relay_addresses, log_path="data/valve_logs.json"):
        """
        Inicializa los relés y configura los parámetros de control.

        :param relay_addresses: Lista de direcciones I2C de los relés.
        :param log_path: Ruta del archivo donde se guardarán los registros JSON.
        """
        self.relays = []
        self.log_path = log_path

        for address in relay_addresses:
            relay = qwiic_relay.QwiicRelay(address)
            if relay.connected:
                self.relays.append(relay)
                relay.begin()
                print(f"Relay connected at address {hex(address)}.")
            else:
                print(f"Relay at address {hex(address)} not connected.")

    def activate_valve(self, index, duration=2):
        """
        Activa una válvula conectada al relé durante un tiempo especificado.

        :param index: Índice del relé (0 para el primero, 1 para el segundo, etc.).
        :param duration: Tiempo en segundos que la válvula estará activada.
        """
        if index < len(self.relays):
            relay = self.relays[index]
            try:
                relay.turn_on()
                print(f"Valve {index} activated for {duration} seconds.")
                self.log_action(index, "ON", "activate")  # Log JSON para la activación
                time.sleep(duration)
                relay.turn_off()
                print(f"Valve {index} deactivated.")
                self.log_action(index, "OFF", "deactivate")  # Log JSON para la desactivación
            except Exception as e:
                print(f"Error controlling relay at {hex(relay.address)}: {e}")
        else:
            print(f"Relay index {index} is out of range.")

    def log_action(self, valve_index, valve_state, action):
        """
        Genera un registro JSON para la acción de la válvula.

        :param valve_index: Índice de la válvula.
        :param valve_state: Estado de la válvula (ON/OFF).
        :param action: Acción realizada (activate/deactivate).
        """
        log = generate_json(
            sensor_id=f"valve_{valve_index}",
            pressure=None,  # Presión no aplica en este contexto
            valve_state=valve_state,
            action=action,
            metadata={"relay_address": hex(self.relays[valve_index].address)}
        )
        save_json(log, self.log_path)

    def cleanup(self):
        """
        Limpia los pines GPIO utilizados por los relés.
        """
        for relay in self.relays:
            relay.turn_off()
        print("All relays turned off.")


# # Ejemplo de uso

# from lib.valve_control import ValveControl

# # Configuración de direcciones I2C para los relés
# relay_addresses = [0x18, 0x19]  # Ejemplo: direcciones de los relés

# # Inicializar el control de válvulas
# valve_control = ValveControl(relay_addresses)

# # Activar la primera válvula durante 3 segundos
# valve_control.activate_valve(0, duration=3)

# # Activar la segunda válvula durante 5 segundos
# valve_control.activate_valve(1, duration=5)

# # Limpiar los relés al finalizar
# valve_control.cleanup()
