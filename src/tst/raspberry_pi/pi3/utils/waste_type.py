# waste_type.py - Simulación de detección y clasificación de residuos
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import random
from datetime import datetime

class WasteTypeDetector:
    """
    Simula la detección y clasificación de residuos, generando datos similares a los producidos por AWS Rekognition.
    """
    def __init__(self):
        self.plastic_types = ["PET", "HDPE", "PVC", "LDPE", "PP", "PS", "Other"]
        self.organic_waste_items = ["orange", "banana", "bread", "apple"]
        self.solid_waste_items = ["cardboard", "paper", "bottle"]
        self.hazardous_items = ["batteries"]

    def generate_waste_data(self):
        """
        Simula la generación de datos de clasificación de residuos.
        """
        # Clasificación aleatoria de plásticos y residuos
        classification = {ptype: random.randint(0, 3) for ptype in self.plastic_types}
        organic_waste = random.randint(0, 2)
        solid_waste = random.randint(0, 2)
        hazardous_waste = random.randint(0, 1)
        other_waste = random.randint(0, 1)

        # Simula elementos detectados
        detected_items = [
            {"Name": random.choice(self.plastic_types + self.organic_waste_items + 
                                   self.solid_waste_items + self.hazardous_items), 
             "Confidence": round(random.uniform(70, 100), 2)}
            for _ in range(random.randint(1, 5))
        ]

        # Simula peso asociado a los residuos detectados (en gramos)
        weight_data = {ptype: random.randint(10, 300) * count for ptype, count in classification.items()}
        total_weight = sum(weight_data.values())

        # Estructura de datos final
        waste_data = {
            "classification": classification,
            "organic_waste": organic_waste,
            "solid_waste": solid_waste,
            "hazardous_waste": hazardous_waste,
            "other_waste": other_waste,
            "detected_items": detected_items,
            "weight_data": weight_data,
            "total_weight": total_weight,
            "event_date": datetime.now().strftime("%Y%m%d"),
            "event_time": datetime.now().strftime("%H:%M:%S")
        }
        return waste_data

# Ejemplo de uso
# if __name__ == "__main__":
#     import json
#     import time
#     import logging

#     # Configuración de logging
#     logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

#     detector = WasteTypeDetector()

#     try:
#         while True:
#             # Generar datos simulados de residuos
#             waste_data = detector.generate_waste_data()
#             logging.info(f"[WASTE DETECTOR] Datos simulados de residuos:\n{json.dumps(waste_data, indent=4)}")

#             # Simular detecciones periódicas
#             time.sleep(2)

#     except KeyboardInterrupt:
#         logging.info("[WASTE DETECTOR] Simulación terminada.")
