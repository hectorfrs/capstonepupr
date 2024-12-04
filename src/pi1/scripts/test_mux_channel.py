from smbus2 import SMBus
from lib.mux_manager import MUXManager

def scan_mux_channels(mux_address=0x70, num_channels=8):
    with SMBus(1) as bus:
        mux = MUXController(i2c_bus=1, i2c_address=mux_address)
        for channel in range(num_channels):
            mux.select_channel(channel)
            print(f"Escaneando canal {channel}...")
            devices = []
            for address in range(0x03, 0x77):  # Escanear todas las direcciones posibles
                try:
                    bus.read_byte(address)
                    devices.append(hex(address))
                except OSError:
                    pass
            print(f"Dispositivos en canal {channel}: {devices if devices else 'Ninguno'}")
        mux.disable_all_channels()

if __name__ == "__main__":
    scan_mux_channels()
