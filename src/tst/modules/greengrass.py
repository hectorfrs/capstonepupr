# greengrass.py - Clase para manejar la interacción con AWS IoT Greengrass.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import boto3
import yaml
from modules.logging_manager import setup_logger

class GreengrassManager:
    """
    Clase para manejar la interacción con AWS IoT Greengrass.
    Permite invocar funciones Lambda locales para procesamiento de datos.
    """

    def __init__(self, config, config_path):
        """
        Inicializa el GreengrassManager usando la configuración YAML.

        :param config: Configuración cargada desde el archivo YAML.
        :param config_path: Ruta al archivo YAML con la configuración.
        """
        # Configurar logger centralizado
        self.logger = setup_logger("[GREENGRASS]", config.get("logging", {}))

        # Cargar configuración
        self.config = self.load_config(config_path)
        self.region = self.config['aws']['region']
        self.group_name = self.config['greengrass']['group_name']
        self.functions = self.config['greengrass']['functions']

        # Inicializar cliente de Lambda para Greengrass
        self.lambda_client = boto3.client('lambda', region_name=self.region)

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
            self.logger.error(f"No se encontró una función Lambda llamada '{function_name}' en la configuración.")
            raise ValueError(f"No se encontró una función Lambda llamada '{function_name}' en el archivo de configuración.")

        # Invocar la función Lambda en Greengrass
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_arn,
                InvocationType='RequestResponse',
                Payload=str(payload)
            )
            result = response['Payload'].read()
            self.logger.info(f"Respuesta de la función Lambda '{function_name}': {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error al invocar la función Lambda '{function_name}': {e}")
            raise
