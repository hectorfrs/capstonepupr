try:
    from sparkfun_qwiic_tca9548a import QwiicTCA9548A
    print("Módulo importado correctamente.")
except ModuleNotFoundError as e:
    print(f"Error al importar el módulo: {e}")