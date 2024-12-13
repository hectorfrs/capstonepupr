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
    """
    Procesa los datos en modo continuo utilizando una cinta transportadora.
    """
    read_calibrated = config["system"].get("read_calibrated_data", True)
    conveyor_active = True
    successful_reads = 0
    failed_reads = 0
    error_details = []

    while conveyor_active:
        for idx, sensor in enumerate(sensors):  # sensors debe ser una lista
            try:
                start_time = time.time()
                mux.enable_channel(idx)
                logging.info(f"[CONVEYOR] [CANAL {idx}] Habilitado para lectura.")

                if read_calibrated:
                    logging.info(f"[CONVEYOR] [SENSOR] Leyendo datos calibrados del sensor {idx}.")
                    spectrum = sensor.read_calibrated_spectrum()
                else:
                    logging.info(f"[CONVEYOR] [SENSOR] Leyendo datos crudos del sensor {idx}.")
                    spectrum = sensor.read_raw_spectrum()

                # Identificar el tipo de plástico
                if spectrum:
                    logging.info(f"[CONVEYOR] [SENSOR] Datos obtenidos correctamente: {spectrum}")
                    plastic_type = identify_plastic_type(spectrum)
                    logging.info(f"[CONVEYOR] [SENSOR] Tipo de plástico identificado: {plastic_type}")
                else:
                    logging.info(f"[CONVEYOR] [SENSOR] No se obtuvieron datos del sensor {idx}.")
                    plastic_type = "Desconocido"

                successful_reads += 1
                

            except KeyboardInterrupt:
                logging.info("[CONVEYOR] Proceso detenido manualmente.")

            except Exception as e:
                failed_reads += 1
                error_details.append({"channel": idx, "error_message": str(e)})
                logging.error(f"[CONVEYOR] [SENSOR] Error en sensor {idx}: {e}")

            finally:
                mux.disable_all_channels()
                elapsed_time = time.time() - start_time
                logging.info(f"[CONVEYOR] [MUX] Todos los canales deshabilitados. Tiempo de ejecución: {elapsed_time:.2f} segundos.")
                logging.info("=" * 50)

        # Simular condición de parada del conveyor (reemplazar por la lógica real)
        conveyor_active = config["system"].get("stop_conveyor", False)

    return successful_reads, failed_reads, error_details
