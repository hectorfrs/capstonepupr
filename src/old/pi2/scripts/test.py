# test.py - Prueba de funcionamiento del relé Qwiic Relay (Qwiic Relay - SPX-15093)
import qwiic_tca9548a
import qwiic_relay
import time

# Inicializar el MUX
mux = qwiic_tca9548a.QwiicTCA9548A()
if not mux.is_connected():
    print("[ERROR] MUX TCA9548A no detectado. Verifica conexiones.")
    exit(1)

# Configuración del canal MUX y dirección I2C del relé
channel = 0  # Canal del MUX donde está conectado el relé
relay_address = 0x18  # Dirección I2C del relé

# Habilitar el canal del MUX
mux.enable_channels(1 << channel)
print(f"[MUX] Canal {channel} habilitado.")
time.sleep(0.5)

# Inicializar el relé
relay = qwiic_relay.QwiicRelay(address=relay_address)

if relay.is_connected():
    print(f"[RELAY] Relé detectado en dirección {hex(relay_address)}.")
    print(f"[RELAY] Versión del firmware: {relay.get_version()}")

    # Encender el relé
    print("[RELAY] Encendiendo el relé...")
    relay.set_relay_on()
    time.sleep(2)

    # Verificar el estado del relé
    if relay.get_relay_state():
        print("[RELAY] El relé está encendido correctamente.")
    else:
        print("[ERROR] El relé no se encendió correctamente.")

    # Apagar el relé
    print("[RELAY] Apagando el relé...")
    relay.set_relay_off()
    time.sleep(1)

    # Verificar el estado del relé
    if not relay.get_relay_state():
        print("[RELAY] El relé se ha apagado correctamente.")
    else:
        print("[ERROR] El relé no se apagó correctamente.")
else:
    print(f"[ERROR] Relé no detectado en dirección {hex(relay_address)}. Verifica conexiones.")

# Desactivar el canal del MUX
mux.disable_channels(1 << channel)
print(f"[MUX] Canal {channel} deshabilitado.")
