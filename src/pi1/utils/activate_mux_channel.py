from smbus2 import SMBus

MUX_I2C_ADDRESS = 0x70  # Dirección I²C del MUX

def activate_all_channels_sequentially(mux_address):
    """
    Activa cada canal del MUX de forma secuencial para pruebas rápidas.
    """
    with SMBus(1) as bus:
        for channel in range(8):
            bus.write_byte(mux_address, 1 << channel)
            print(f"Canal {channel} activado. Ejecuta pruebas en este canal.")
            input("Presiona Enter para activar el siguiente canal...")

if __name__ == "__main__":
    activate_all_channels_sequentially(MUX_I2C_ADDRESS)
