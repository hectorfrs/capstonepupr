import logging
import time

from classes.AS7265x_Manager import AS7265xManager
from classes.TCA9548A_Manager import TCA9548AManager

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

            read_calibrated = config["system"].get("read_calibrated_data", True)

            if read_calibrated:
                logging.info(f"[SENSOR] Realizando lectura calibrada del sensor {idx} en canal {mux_channels[idx]}")
                spectrum = sensor.read_calibrated_spectrum()
                successful_reads += 1
            else:
                logging.info(f"[SENSOR] Realizando lectura datos crudos del sensor {idx} en canal {mux_channels[idx]}")
                spectrum = sensor.read_raw_spectrum()

        except Exception as e:
            failed_reads += 1
            error_details.append({"channel": mux_channels[idx], "error_message": str(e)})
            logging.error(
                f"[SENSOR] Error al procesar el sensor {idx} en canal {mux_channels[idx]}: {e}")
        finally:
            mux.disable_all_channels()
            elapsed_time = time.time() - start_time
            logging.info(f"[SENSOR] Captura completada. [MUX] Todos los canales deshabilitados.")
            logging.info(f"Tiempos de ejecución: {elapsed_time:.2f} segundos.")

    return successful_reads, failed_reads, error_details


def process_with_conveyor(config, sensors, mux):
    """
    Proceso continuo con conveyor para leer datos de los sensores.
    """
    logging.info("[CONVEYOR] Iniciando proceso continuo...")
    successful_reads = 0
    failed_reads = 0
    error_details = []

    mux_channels = [entry['channel'] for entry in config['mux']['channels']]
    try:
        while True:
            for idx, sensor in enumerate(sensors):
                start_time = time.time()
                mux.enable_channel(mux_channels[idx])
                logging.info(f"[CONVEYOR][CANAL {mux_channels[idx]}] Habilitado para lectura.")

                try:
                    spectrum = sensor.read_calibrated_spectrum()
                    successful_reads += 1
                except Exception as e:
                    failed_reads += 1
                    error_details.append({"channel": mux_channels[idx], "error_message": str(e)})
                    logging.error(
                        f"[CONVEYOR][SENSOR] Error al procesar el sensor {idx} en canal {mux_channels[idx]}: {e}")
                finally:
                    mux.disable_all_channels()
                    elapsed_time = time.time() - start_time
                    logging.info(f"[CONVEYOR][SENSOR] Captura completada. [MUX] Todos los canales deshabilitados.")
                    logging.info(f"Tiempos de ejecución: {elapsed_time:.2f} segundos.")

    except KeyboardInterrupt:
        logging.info("[CONVEYOR] Proceso detenido manualmente.")
    
    return successful_reads, failed_reads, error_details
