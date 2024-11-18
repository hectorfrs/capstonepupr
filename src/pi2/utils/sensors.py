def read_pressure_data(sensor_name):
    print(f"Reading pressure sensor: {sensor_name}")
    if sensor_name == "SparkFun Qwiic Micropresión":
        return {"type": "pressure", "value": 12.5}  # Valor simulado para presión en PSI
    else:
        return {"type": "Unknown", "value": 0.0}
