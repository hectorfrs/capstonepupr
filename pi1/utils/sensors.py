def read_sensor(sensor_name):
    print(f"Reading sensor: {sensor_name}")
    if sensor_name == "SparkFun AS7263 NIR":
        return {"type": "NIR", "value": 0.47}  # Valor simulado
    elif sensor_name == "SparkFun Triad AS7265x - Unit 1":
        return {"type": "Spectroscopy", "value": 0.88}  # Valor simulado
    elif sensor_name == "SparkFun Triad AS7265x - Unit 2":
        return {"type": "Spectroscopy", "value": 0.92}  # Valor simulado
    else:
        return {"type": "Unknown", "value": 0.0}
