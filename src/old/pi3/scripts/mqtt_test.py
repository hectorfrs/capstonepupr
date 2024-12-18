import time
import json
import uuid
from utils.mqtt_handler import MQTTHandler

mqtt_handler = MQTTHandler(config)
mqtt_handler.connect()

while True:
    message = {
        "id": str(uuid.uuid4()),
        "status": "material_detected",
        "material": "PET",
        "confidence": 95.6,
        "timestamp": time.time()
    }
    mqtt_handler.publish("material/entrada", json.dumps(message))
    time.sleep(5)
