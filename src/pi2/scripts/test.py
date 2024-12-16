import qwiic_tca9548a
import time

# Inicializa el MUX
mux = qwiic_tca9548a.QwiicTCA9548A()
if not mux.is_connected():
    print("MUX TCA9548A no detectado. Verifica conexiones.")
    exit(1)

# Habilita un canal del MUX
channel = 1  # Cambia esto según el canal esperado
mux.enable_channels(1 << channel)
print(f"Canal {channel} habilitado en el MUX.")

# Mantén el canal habilitado para escanear con i2cdetect
print("Manteniendo el canal habilitado por 10 segundos. Ejecuta 'i2cdetect -y 1'")
time.sleep(10)
mux.disable_channels()
print("Canal deshabilitado.")
