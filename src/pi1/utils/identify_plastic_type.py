import math

def identify_plastic_type(raw_data, plastic_spectra):
    """
    Identifica el tipo de plástico basado en los datos crudos y espectros de referencia.
    :param raw_data: Datos crudos del sensor.
    :param plastic_spectra: Diccionario con los espectros de plásticos.
    :return: Nombre del plástico identificado y distancia mínima.
    """
    min_distance = float('inf')
    identified_plastic = None

    for plastic, spectrum in plastic_spectra.items():
        distance = math.sqrt(sum((raw_data[color] - spectrum[color]) ** 2 for color in raw_data))
        if distance < min_distance:
            min_distance = distance
            identified_plastic = plastic

    return identified_plastic, min_distance
