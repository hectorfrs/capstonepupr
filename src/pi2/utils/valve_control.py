import RPi.GPIO as GPIO
import time

# Definir los pines GPIO para controlar los Relays de ambas válvulas con redundancia
RELAY_PIN_1_PRIMARY = 17  # Relay principal para la válvula 1
RELAY_PIN_1_BACKUP = 18   # Relay de respaldo para la válvula 1
RELAY_PIN_2_PRIMARY = 27  # Relay principal para la válvula 2
RELAY_PIN_2_BACKUP = 22   # Relay de respaldo para la válvula 2

def setup_valves():
    """
    Configura los pines GPIO para controlar los 4 Relays (2 por válvula con redundancia).
    """
    GPIO.setmode(GPIO.BCM)  # Utiliza el modo BCM para numeración de pines
    
    # Configurar los pines para los relés de la válvula 1
    GPIO.setup(RELAY_PIN_1_PRIMARY, GPIO.OUT)
    GPIO.setup(RELAY_PIN_1_BACKUP, GPIO.OUT)
    GPIO.output(RELAY_PIN_1_PRIMARY, GPIO.LOW)  # Inicialmente apagado
    GPIO.output(RELAY_PIN_1_BACKUP, GPIO.LOW)   # Inicialmente apagado

    # Configurar los pines para los relés de la válvula 2
    GPIO.setup(RELAY_PIN_2_PRIMARY, GPIO.OUT)
    GPIO.setup(RELAY_PIN_2_BACKUP, GPIO.OUT)
    GPIO.output(RELAY_PIN_2_PRIMARY, GPIO.LOW)  # Inicialmente apagado
    GPIO.output(RELAY_PIN_2_BACKUP, GPIO.LOW)   # Inicialmente apagado

def activate_relay(pin):
    """
    Intenta activar un relé y devuelve True si tiene éxito, False si falla.
    """
    try:
        GPIO.output(pin, GPIO.HIGH)  # Activar el relé
        print(f"Relay {pin} activated.")
        return True
    except Exception as e:
        print(f"Failed to activate Relay {pin}: {e}")
        return False

def adjust_valves(valve, pressure_data):
    """
    Controla los relés de ambas válvulas con redundancia basado en los datos del sensor de presión.
    
    :param valve: Nombre de las válvulas que están controladas por los relés.
    :param pressure_data: Datos de presión que dictan si los relés se activan o no.
    """
    setup_valves()  # Configura los GPIO para controlar los 4 relés
    
    # Controlar la válvula 1
    if pressure_data['value'] < 10:
        print("Opening valve 1.")
        if not activate_relay(RELAY_PIN_1_PRIMARY):  # Intentar activar el relé principal
            print("Primary Relay 1 failed. Activating backup.")
            activate_relay(RELAY_PIN_1_BACKUP)  # Activar el relé de respaldo
    else:
        print("Closing valve 1.")
        GPIO.output(RELAY_PIN_1_PRIMARY, GPIO.LOW)  # Cerrar el relé principal
        GPIO.output(RELAY_PIN_1_BACKUP, GPIO.LOW)   # Cerrar el relé de respaldo
    
    # Controlar la válvula 2
    if pressure_data['value'] < 10:
        print("Opening valve 2.")
        if not activate_relay(RELAY_PIN_2_PRIMARY):  # Intentar activar el relé principal
            print("Primary Relay 2 failed. Activating backup.")
            activate_relay(RELAY_PIN_2_BACKUP)  # Activar el relé de respaldo
    else:
        print("Closing valve 2.")
        GPIO.output(RELAY_PIN_2_PRIMARY, GPIO.LOW)  # Cerrar el relé principal
        GPIO.output(RELAY_PIN_2_BACKUP, GPIO.LOW)   # Cerrar el relé de respaldo

    # Registrar el estado de los relés
    time.sleep(1)  # Simulación de operación de las válvulas por 1 segundo
    GPIO.cleanup()  # Limpiar los pines GPIO después de usarlos
