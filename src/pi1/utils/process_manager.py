import logging
import time

from classes.AS7265x_Manager import AS7265xManager
from classes.TCA9548A_Manager import TCA9548AManager
from utils.identify_plastic_type import identify_plastic_type


def process_individual(config, sensors, mux):
    """
    Proceso individual para leer datos de los sensores.
    """
    successful_reads = 0
    failed_reads = 0
    error_details = []
    plastic_spectra = config.get("plastic_spectra", {})
    mux_channels = [entry['channel'] for entry in config['mux']['channels']]

    for idx, sensor in enumerate(sensors):
        try:
            start_time = time.time()
            mux.enable_channel(mux_channels[idx])
            logging.info("=" * 50)
            logging.info(f"[CANAL {mux_channels[idx]}] Habilitado para lectura.")
            
            # Leer configuración para datos calibrados o crudos
            read_calibrated = config["system"].get("read_calibrated_data", True)

            if read_calibrated:
                logging.info(f"[SENSOR] Realizando lectura calibrada del sensor {idx} en canal {mux_channels[idx]}")
                spectrum = sensor.read_calibrated_spectrum()
            else:
                logging.info(f"[SENSOR] Realizando lectura datos crudos del sensor {idx} en canal {mux_channels[idx]}")
                spectrum = sensor.read_raw_spectrum()

            # Identificar el tipo de plástico
            plastic_type = identify_plastic_type(spectrum)
            logging.info(f"[INDIVIDUAL] [SENSOR] Tipo de plástico identificado: {plastic_type}")

            successful_reads += 1        

        except Exception as e:
            failed_reads += 1
            error_details.append({"channel": mux_channels[idx], "error_message": str(e)})
            logging.error(
                f"[INDIVIDUAL] [SENSOR] Error al procesar el sensor {idx} en canal {mux_channels[idx]}: {e}")
        finally:
            mux.disable_all_channels()
            elapsed_time = time.time() - start_time
            logging.info(f"[INDIVIDUAL] [SENSOR] Captura completada. [MUX] Todos los canales deshabilitados.")
            logging.info(f"Tiempos de ejecución: {elapsed_time:.2f} segundos.")

    return successful_reads, failed_reads, error_details


def process_with_conveyor(config, sensors, mux):
    successful_reads = 0
    failed_reads = 0
    error_details = []
    plastic_spectra = config.get("plastic_spectra", {})                                             # Cargar espectros desde config.yaml
    mux_channels = [entry['channel'] for entry in config['mux']['channels']]                        # Cargar solo canales configurados
    sensor_names = {entry['channel']: entry['sensor_name'] for entry in config['mux']['channels']}  # Asociar sensores

    for channel in mux_channels:
        try:
            mux.enable_channel(channel)
            logging.info(f"[MUX] [CANAL {channel}] Habilitado.")
            logging.info(f"[CONVEYOR] [CANAL {channel}] Habilitado para lectura.")

            # Leer espectro crudo o calibrado
            read_calibrated = config["system"].get("read_calibrated_data", True)
            if read_calibrated:
                logging.info(f"[CONVEYOR] [SENSOR] Leyendo datos calibrados del sensor en canal {channel}.")
                spectrum = sensors[channel].read_calibrated_spectrum()
            else:
                logging.info(f"[CONVEYOR] [SENSOR] Leyendo datos crudos del sensor en canal {channel}.")
                spectrum = sensors[channel].read_raw_spectrum()

            # Validar espectro y determinar tipo de plástico
            if spectrum:
                raw_data = {
                    "Violet": spectrum[0]['calibrated_value'],
                    "Blue": spectrum[1]['calibrated_value'],
                    "Green": spectrum[2]['calibrated_value'],
                    "Yellow": spectrum[3]['calibrated_value'],
                    "Orange": spectrum[4]['calibrated_value'],
                    "Red": spectrum[5]['calibrated_value']
                }
                identified_plastic, distance = identify_plastic_type(raw_data, plastic_spectra)
                logging.info(f"[CONVEYOR] [SENSOR] Plástico identificado en canal {channel}: {identified_plastic} (distancia: {distance:.2f})")
            else:
                logging.warning(f"[CONVEYOR] [SENSOR] No se obtuvo espectro válido para el canal {channel}.")

        except Exception as e:
            logging.error(f"[CONVEYOR] [SENSOR] Error en sensor {channel}: {e}")
        finally:
            mux.disable_all_channels()
            logging.info("[MUX] Todos los canales deshabilitados.")
            elapsed_time = time.time()
            logging.info(f"[CONVEYOR] [MUX] Todos los canales deshabilitados. Tiempo de ejecución: {elapsed_time:.2f} segundos.")

            logging.info("=" * 50)

        # Simular condición de parada del conveyor (reemplazar por la lógica real)
        conveyor_active = config["system"].get("stop_conveyor", False)

    return successful_reads, failed_reads, error_details
