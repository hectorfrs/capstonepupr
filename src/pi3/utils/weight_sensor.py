# weight_sensor.py - Simulador de sensores de peso para los buckets.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import random
import logging

class WeightSensor:
    """
    Simulador de sensores de peso para los buckets de materiales.
    """
    def __init__(self, buckets):
        """
        Inicializa los sensores de peso con buckets vacíos.

        :param buckets: Diccionario con los nombres de los buckets y su peso inicial.
        """
        self.buckets = buckets
        self.weight_limits = {
            "Bucket 1 (PET)": 1000,  # Peso máximo en gramos
            "Bucket 2 (HDPE)": 1000  # Peso máximo en gramos
        }
        self.weight_increments = {
            "Bucket 1 (PET)": (8, 12),   # Incremento aleatorio por botella PET
            "Bucket 2 (HDPE)": (18, 22)  # Incremento aleatorio por botella HDPE
        }
        if self.buckets[bucket] >= self.weight_limits[bucket]:
            logging.warning(f"[WEIGHT SENSOR] ALERTA: {bucket} está lleno (peso: {self.weight_limits[bucket]}g)")


    def simulate_weight(self):
        """
        Simula el incremento de peso al agregar una botella al bucket.
        """
        for bucket in self.buckets.keys():
            if self.buckets[bucket] < self.weight_limits[bucket]:
                increment = random.uniform(*self.weight_increments[bucket])
                self.buckets[bucket] = min(self.buckets[bucket] + increment, self.weight_limits[bucket])
                logging.info(f"[WEIGHT SENSOR] {bucket}: +{increment:.2f}g (Total: {self.buckets[bucket]:.2f}g)")
            else:
                logging.warning(f"[WEIGHT SENSOR] {bucket} alcanzó el peso máximo: {self.weight_limits[bucket]}g")

    def get_weights(self):
        """
        Devuelve los pesos actuales de los buckets.

        :return: Diccionario con los pesos actuales.
        """
        return self.buckets
