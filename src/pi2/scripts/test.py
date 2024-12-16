import qwiic_tca9548a
import qwiic_relay
import time

# Inicializa el MUX
mux = qwiic_tca9548a.QwiicTCA9548A()
if not mux.is_connected():
    print("[ERROR] MUX TCA9548A no detectado. Verifica conexiones.")
    exit(1)

# Definir el canal MUX y dirección I2C del relé
channel = 1  # Canal del MUX donde está conectado el relé
relay_address = 0x18  # Dirección I2C del relé

# Habilitar el canal MUX
mux.enable_channels(1 << channel)
print(f"[MUX] Canal {channel} habilitado.")
time.sleep(10)  
# Inicializar el relé
relay = qwiic_relay.QwiicRelay(address=relay_address)

if relay.connected:
    print(f"[RELAY] Relé detectado en canal {channel}, dirección {hex(relay_address)}.")

    # Comandos de prueba para el relé
    print("[RELAY] Encendiendo el relé...")
    relay.turn_on()
    time.sleep(2)  # Mantener el relé encendido por 2 segundos

    if relay.is_relay_on():
        print("[RELAY] El relé está encendido correctamente.")

    print("[RELAY] Apagando el relé...")
    relay.turn_off()
    time.sleep(1)

    if not relay.is_relay_on():
        print("[RELAY] El relé se ha apagado correctamente.")

else:
    print(f"[ERROR] No se pudo detectar el relé en dirección {hex(relay_address)}. Verifica las conexiones.")

# Deshabilitar el canal MUX
mux.disable_channels(1 << channel)
print(f"[MUX] Canal {channel} deshabilitado.")
