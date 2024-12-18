# greengrass.py - Clase para manejar la interacción con AWS IoT Greengrass.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import uuid

class GreengrassManager:
    """
    Clase para manejar la interacción con AWS IoT Greengrass.
    Permite invocar funciones Lambda locales para procesamiento de datos.
    """

    def __init__(self, config_manager, mqtt_handler=None):
        """
        Inicializa el GreengrassManager usando la configuración centralizada.

        :param config_manager: Instancia de ConfigManager para manejar configuraciones centralizadas.
        :param mqtt_handler: Instancia opcional de MQTTHandler para publicar eventos relacionados con Greengrass.
        """
        from modules.logging_manager import LoggingManager
        import boto3

        self.config_manager = config_manager
        self.mqtt_handler = mqtt_handler
        self.enable_greengrass = self.config_manager.get("system.enable_greengrass", True)
        self.logger = LoggingManager(config_manager).setup_logger("[GREENGRASS_MANAGER]")

        # Cargar configuración específica de Greengrass
        self.config = self.config_manager.get("greengrass", {})
        self.region = self.config.get("region", "us-east-1")
        self.group_name = self.config.get("group_name", "default_group")
        self.functions = self.config.get("functions", [])

        if not self.enable_greengrass:
            self.logger.warning("Greengrass está deshabilitado en la configuración.")

        # Inicializar cliente de Lambda para Greengrass
        self.lambda_client = boto3.client('lambda', region_name=self.region)

    def invoke_function(self, function_name, payload):
        """
        Invoca una función Lambda localmente en Greengrass.

        :param function_name: Nombre de la función Lambda definida en la configuración.
        :param payload: Datos en formato JSON para enviar a la función Lambda.
        :return: Respuesta de la función Lambda.
        """
        if not self.enable_greengrass:
            self.logger.warning("Greengrass está deshabilitado. Invocación omitida.")
            return None

        # Buscar la ARN de la función por su nombre
        function_arn = None
        for function in self.functions:
            if function['name'] == function_name:
                function_arn = function['arn']
                break

        if not function_arn:
            self.logger.error(f"No se encontró una función Lambda llamada '{function_name}' en la configuración.")
            raise ValueError(f"No se encontró una función Lambda llamada '{function_name}' en el archivo de configuración.")

        # Agregar ID único al payload para trazabilidad
        payload_with_id = payload.copy() if isinstance(payload, dict) else {"data": payload}
        payload_with_id["id"] = str(uuid.uuid4())

        # Invocar la función Lambda en Greengrass
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_arn,
                InvocationType='RequestResponse',
                Payload=str(payload_with_id)
            )
            result = response['Payload'].read()
            self.logger.info(f"Respuesta de la función Lambda '{function_name}': {result}")

            # Publicar el evento en MQTT si está habilitado
            if self.mqtt_handler and self.mqtt_handler.is_connected():
                self.mqtt_handler.publish("greengrass/events", {
                    "function_name": function_name,
                    "payload": payload_with_id,
                    "response": result
                })

            return result
        except Exception as e:
            self.logger.error(f"Error al invocar la función Lambda '{function_name}': {e}")
            raise
