import boto3
import yaml


class GreengrassManager:
    """
    Clase para manejar la interacción con AWS IoT Greengrass.
    Permite invocar funciones Lambda locales para procesamiento de datos.
    """

    def __init__(self, config_path="config/pi1_config.yaml"):
        """
        Inicializa el GreengrassManager usando la configuración YAML.

        :param config_path: Ruta al archivo YAML con la configuración.
        """
        self.config = self.load_config(config_path)
        self.group_name = self.config['greengrass']['group_name']
        self.functions = self.config['greengrass']['functions']

        # Inicializar cliente de Lambda para Greengrass
        self.lambda_client = boto3.client('lambda')

    @staticmethod
    def load_config(config_path):
        """
        Carga la configuración desde un archivo YAML.

        :param config_path: Ruta al archivo YAML.
        :return: Diccionario con la configuración cargada.
        """
        with open(config_path, "r") as file:
            return yaml.safe_load(file)

    def invoke_function(self, function_name, payload):
        """
        Invoca una función Lambda localmente en Greengrass.

        :param function_name: Nombre de la función Lambda definida en el YAML.
        :param payload: Datos en formato JSON para enviar a la función Lambda.
        :return: Respuesta de la función Lambda.
        """
        # Buscar la ARN de la función por su nombre
        function_arn = None
        for function in self.functions:
            if function['name'] == function_name:
                function_arn = function['arn']
                break

        if not function_arn:
            raise ValueError(f"No se encontró una función Lambda llamada '{function_name}' en el archivo de configuración.")

        # Invocar la función Lambda en Greengrass
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_arn,
                InvocationType='RequestResponse',
                Payload=str(payload)
            )
            result = response['Payload'].read()
            print(f"Respuesta de la función Lambda '{function_name}': {result}")
            return result
        except Exception as e:
            print(f"Error al invocar la función Lambda '{function_name}': {e}")
            raise

# # Ejemplo de uso:

# # Invocar Funcion Lambda Localmente

# from utils.greengrass import GreengrassManager

# def main():
#     # Inicializar el administrador de Greengrass
#     greengrass_manager = GreengrassManager(config_path="config/pi1_config.yaml")

#     # Datos para enviar a la función Lambda
#     payload = {
#         "sensor_id": "AS7265x_1",
#         "spectral_data": {
#             "violet": 150,
#             "blue": 210,
#             "green": 180,
#             "yellow": 130,
#             "orange": 110,
#             "red": 90
#         },
#         "detected_material": "PET"
#     }

#     # Invocar la función Lambda "DetectPlasticType"
#     response = greengrass_manager.invoke_function("DetectPlasticType", payload)
#     print("Respuesta de Lambda:", response)


# if __name__ == "__main__":
#     main()
