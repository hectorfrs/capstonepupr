import boto3
import logging

class GreengrassManager:
    """
    Clase para manejar interacciones con AWS Greengrass.
    """

    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.client = boto3.client(
            'lambda',
            region_name=self.config['aws']['region']
        )
        logging.info("Greengrass Manager inicializado.")

    @staticmethod
    def load_config(config_path):
        """
        Carga la configuración desde un archivo YAML.
        """
        import yaml
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def invoke_function(self, payload):
        """
        Invoca una función de Lambda en Greengrass.

        :param payload: Datos a enviar a la función.
        :return: Respuesta de la función Lambda.
        """
        try:
            response = self.client.invoke(
                FunctionName=self.config['greengrass']['functions'][0]['name'],
                Payload=str(payload).encode('utf-8')
            )
            return response['Payload'].read().decode('utf-8')
        except Exception as e:
            logging.error(f"Error al invocar función de Greengrass: {e}")
            return None
