import json

def process_with_greengrass(group, data):
    """
    Procesa los datos localmente utilizando AWS IoT Greengrass.
    
    :param group: El nombre del grupo de Greengrass al que pertenece el dispositivo.
    :param data: Los datos recolectados que deben ser procesados localmente.
    """
    print(f"Processing data locally with Greengrass group {group}")
    
    # Simulación de procesamiento local con Greengrass
    payload = json.dumps(data)
    print(f"Greengrass is processing: {payload}")
    
    # Aquí puedes interactuar con los componentes de AWS IoT Greengrass
    # y realizar tareas de procesamiento local antes de enviar los datos.
