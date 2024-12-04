from smbus2 import SMBus

MUX_I2C_ADDRESS = 0x70  # Dirección I²C del MUX
CHANNEL_TO_ENABLE = 0    # Cambia el número de canal según sea necesario (0 a 7)

def enable_mux_channel(mux_address, channel):
    """
    Activa un canal específico del MUX.
    """
    with SMBus(1) as bus:  # Cambia '1' si estás usando otro bus I²C
        bus.write_byte(mux_address, 1 << channel)
        print(f"Canal {channel} activado en MUX (dirección {hex(mux_address)})")

if __name__ == "__main__":
    enable_mux_channel(MUX_I2C_ADDRESS, CHANNEL_TO_ENABLE)
