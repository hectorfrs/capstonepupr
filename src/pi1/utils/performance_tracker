# performance_tracker.py - Clase para rastrear estadísticas de rendimiento y procesamiento.
from datetime import timedelta, datetime
import logging


class PerformanceTracker:
    """
    Clase para rastrear estadísticas de rendimiento y procesamiento.
    """
    def __init__(self, log_interval=60):
        """
        Inicializa el rastreador de rendimiento.

        :param log_interval: Intervalo en segundos para registrar métricas en los logs.
        """
        self.total_processing_time = timedelta()
        self.num_readings = 0
        self.last_log_time = datetime.now()
        self.log_interval = log_interval

    def add_reading(self, processing_time):
        """
        Agrega una lectura al rastreador de rendimiento.

        :param processing_time: Tiempo de procesamiento en milisegundos.
        """
        self.total_processing_time += timedelta(milliseconds=processing_time)
        self.num_readings += 1

    def get_average_time(self):
        """
        Calcula el tiempo promedio de procesamiento.

        :return: Tiempo promedio en milisegundos o None si no hay lecturas.
        """
        if self.num_readings == 0:
            return None
        average_time = self.total_processing_time / self.num_readings
        return average_time.total_seconds() * 1000  # Convertir a milisegundos

    def log_metrics(self):
        """
        Registra las métricas de rendimiento en los logs.
        """
        now = datetime.now()
        if (now - self.last_log_time).total_seconds() >= self.log_interval:
            average_time = self.get_average_time()
            if average_time:
                logging.info(f"Tiempo promedio de procesamiento: {average_time:.2f} ms")
                logging.info(f"Total de lecturas procesadas: {self.num_readings}")
            else:
                logging.info("No hay lecturas para calcular métricas.")
            self.last_log_time = now

    def reset(self):
        """
        Resetea los datos del rastreador de rendimiento.
        """
        self.total_processing_time = timedelta()
        self.num_readings = 0
        logging.info("Rastreador de rendimiento reseteado.")
