import json
import subprocess


def process_with_greengrass(function_name, payload):
    """
    Procesa los datos localmente utilizando AWS IoT Greengrass.

    :param function_name: El ARN de la función Lambda que se ejecutará localmente.
    :param payload: Diccionario con los datos a enviar a la función Lambda.
    :return: Respuesta del procesamiento local, si está disponible.
    """
    print(f"Invocando función de Greengrass: {function_name}")
    try:
        # Serializar el payload en formato JSON
        payload_json = json.dumps(payload)
        
        # Ejecutar el comando CLI de Greengrass para invocar la función Lambda
        response = subprocess.run(
            [
                "sudo", "/greengrass/v2/bin/greengrass-cli",
                "lambda", "invoke",
                "--arn", function_name
            ],
            input=payload_json.encode('utf-8'),     # Pasar el payload al proceso
            capture_output=True,                    # Capturar salida del comando
            text=True                               # Usar texto en lugar de bytes
        )

        # Verificar si el comando fue exitoso
        if response.returncode != 0:
            raise RuntimeError(f"Error en Greengrass CLI: {response.stderr}")

        # Retornar la respuesta de la función Lambda
        print(f"Respuesta de Greengrass: {response.stdout}")
        return json.loads(response.stdout)

    except Exception as e:
        print(f"Fallo al procesar datos con Greengrass: {e}")
        return None
