import logging
import time

from classes.AS7265x_Manager import AS7265xManager
from classes.TCA9548A_Manager import TCA9548AManager
from utils.identify_plastic_type import identify_plastic_type


def process_individual(config, sensors, mux):
    """
    Procesa los sensores individualmente en modo individual.
    """
    successful_reads = 0
    failed_reads = 0
    error_details = []
    plastic_spectra = config.get("plastic_spectra", {})                                             # Cargar espectros desde config.yaml
    mux_channels = [entry['channel'] for entry in config['mux']['channels']]                        # Cargar solo canales configurados
    sensor_names = {entry['channel']: entry['sensor_name'] for entry in config['mux']['channels']}  # Asociar sensores
    
    if not mux_channels:
        logging.error("[MUX] No se configuraron canales en mux_channels.")
        return 0, 0, [{"error_message": "mux_channels no configurado en config.yaml."}]

    if len(sensors) != len(mux_channels):
        logging.error(f"[INDIVIDUAL] Desalineación: {len(sensors)} sensores, {len(mux_channels)} canales configurados.")

    for idx, sensor in enumerate(sensors):
        start_time = time.time()  # Inicio del tiempo para este sensor
        try:
            if idx >= len(mux_channels):
                raise IndexError(f"El índice {idx} excede el tamaño de mux_channels ({len(mux_channels)}).")
            
            channel = mux_channels[idx]
            mux.enable_channel(channel)
            logging.info(f"[INDIVIDUAL] [SENSOR] Leyendo datos del sensor en canal {channel}...")

            # Realizar lectura calibrada o cruda
            spectrum = sensor.read_calibrated_spectrum()
            raw_data = extract_spectrum_values(spectrum)
            identified_plastic, distance = identify_plastic_type(raw_data, plastic_spectra)
            logging.info(f"[INDIVIDUAL] [SENSOR] Plástico identificado en canal {channel}: {identified_plastic} (distancia: {distance:.2f})")
            
            successful_reads += 1
        except IndexError as ie:
            logging.error(f"[INDIVIDUAL] [SENSOR] Índice fuera de rango: {ie}")
            failed_reads += 1
            #error_details.append({"channel": "Desconocido", "error_message": str(ie)})
            error_details.append({
            "channel": mux_channels[idx] if idx < len(mux_channels) else "Desconocido",
            "error_message": str(e)
            })
        except Exception as e:
            logging.error(f"[INDIVIDUAL] [SENSOR] Error en sensor {idx}: {e}")
            failed_reads += 1
            error_details.append({"channel": idx, "error_message": str(e)})
        finally:
            mux.disable_all_channels()
            elapsed_time = time.time() - start_time  # Fin del tiempo para este sensor
            logging.info("[MUX] Todos los canales deshabilitados.")
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
        if channel >= len(sensors) or sensors[channel] is None:
            logging.warning(f"[CONVEYOR] [CANAL {channel}] No se encontró un sensor configurado.")
            continue
        try:
            start_time = time.time()
            if channel >= len(sensors) or sensors[channel] is None:
                logging.warning(f"[CONVEYOR] [CANAL {channel}] No se encontró un sensor configurado.")
                continue

            # Habilitar el canal
            mux.enable_channel(channel)
            logging.info(f"[MUX] [CANAL {channel}] Habilitado.")
            logging.info(f"[CONVEYOR] [CANAL {channel}] Habilitado para lectura.")

            # Leer espectro calibrado o crudo
            read_calibrated = config["system"].get("read_calibrated_data", True)
            if read_calibrated:
                logging.info(f"[CONVEYOR] [SENSOR] Leyendo datos calibrados del sensor en canal {channel}.")
                spectrum = sensors[channel].read_calibrated_spectrum()
            else:
                logging.info(f"[CONVEYOR] [SENSOR] Leyendo datos crudos del sensor en canal {channel}.")
                spectrum = sensors[channel].read_raw_spectrum()

            if not spectrum:
                raise ValueError("No se obtuvo espectro válido del sensor.")

            # Procesar datos y determinar tipo de plástico
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
            successful_reads += 1

        except IndexError:
            logging.error(f"[CONVEYOR] [SENSOR] Error en sensor {channel}: Índice fuera de rango. Verifique la configuración.")
            failed_reads += 1
            error_details.append({"channel": channel, "error_message": "Índice fuera de rango."})

        except Exception as e:
            logging.error(f"[CONVEYOR] [SENSOR] Error en sensor {channel}: {e}")
            failed_reads += 1
            #error_details.append({"channel": channel, "error_message": str(e)})
            error_details.append({
            "channel": mux_channels[idx] if idx < len(mux_channels) else "Desconocido",
            "error_message": str(e)
            })

        finally:
            mux.disable_all_channels()
            logging.info("[MUX] Todos los canales deshabilitados.")
            elapsed_time = time.time() - start_time
            logging.info(f"[CONVEYOR] [MUX] Todos los canales deshabilitados. Tiempo de ejecución: {elapsed_time:.2f} segundos.")
            logging.info("=" * 50)

    return successful_reads, failed_reads, error_details