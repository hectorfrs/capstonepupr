import qwiic_tca9548a
import qwiic_relay
import time

# Inicializa el MUX
mux = qwiic_tca9548a.QwiicTCA9548A()
if not mux.is_connected():
    print("[ERROR] MUX TCA9548A no detectado. Verifica conexiones.")
    exit(1)

# Configuración del canal MUX y dirección I2C del relé
channel = 1  # Canal del MUX donde está conectado el relé
relay_address = 0x18  # Dirección I2C del relé

# Activar el canal del MUX
mux.enable_channels(1 << channel)
print(f"[MUX] Canal {channel} habilitado.")
time.sleep(0.5)

# Inicializar el relé en la dirección I2C especificada
relay = qwiic_relay.QwiicRelay(address=relay_address)

if relay.connected:
    print(f"[RELAY] Relé detectado en dirección {hex(relay_address)}.")

    # Encender el relé
    print("[RELAY] Encendiendo el relé...")
    if relay.begin() == False:
        print("The Qwiic Relay isn't connected to the system. Please check your connection", \
            file=sys.stderr)

    relay.set_relay_on()
    relay.get_version()
    time.sleep(2)

    # Verificar si el relé está encendido
    if relay.is_connected():
        print("[RELAY] El relé está encendido correctamente.")

    # Apagar el relé
    print("[RELAY] Apagando el relé...")
    relay.set_relay_off()
    time.sleep(1)

    # Verificar si el relé está apagado
    if relay.get_relay_state() is True:
        print ("[RELAY] El relé esta encendido.")
    else:
        print("[RELAY] El relé se ha apagado.")
else:
    print(f"[ERROR] Relé no detectado en dirección {hex(relay_address)}. Verifica conexiones.")

# Desactivar el canal del MUX
mux.disable_channels(1 << channel)
print(f"[MUX] Canal {channel} deshabilitado.")
