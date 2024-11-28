import json
import os


class JSONManager:
    """
    Clase para manejar operaciones de lectura, escritura y validación de archivos JSON.
    """

    @staticmethod
    def load_json(file_path):
        """
        Carga el contenido de un archivo JSON.

        :param file_path: Ruta del archivo JSON.
        :return: Datos del archivo JSON como un diccionario.
        :raises FileNotFoundError: Si el archivo no existe.
        :raises json.JSONDecodeError: Si el archivo no contiene un JSON válido.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo JSON no existe: {file_path}")

        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                print(f"JSON cargado exitosamente desde {file_path}")
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al decodificar el archivo JSON: {e}")

    @staticmethod
    def save_json(file_path, data):
        """
        Guarda datos en un archivo JSON.

        :param file_path: Ruta donde se guardará el archivo JSON.
        :param data: Datos a guardar (debe ser serializable en JSON).
        :raises TypeError: Si los datos no son serializables en JSON.
        """
        try:
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)
                print(f"Datos guardados exitosamente en {file_path}")
        except TypeError as e:
            raise ValueError(f"Error al guardar datos en JSON: {e}")

    @staticmethod
    def update_json(file_path, updates):
        """
        Actualiza un archivo JSON con nuevos datos.

        :param file_path: Ruta del archivo JSON existente.
        :param updates: Diccionario con los datos a actualizar.
        :return: Diccionario actualizado.
        :raises FileNotFoundError: Si el archivo no existe.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo JSON no existe: {file_path}")

        try:
            # Cargar datos existentes
            data = JSONManager.load_json(file_path)

            # Actualizar datos
            data.update(updates)

            # Guardar los datos actualizados
            JSONManager.save_json(file_path, data)

            print(f"Archivo JSON actualizado exitosamente: {file_path}")
            return data
        except Exception as e:
            raise ValueError(f"Error al actualizar el archivo JSON: {e}")

    @staticmethod
    def validate_json(data, required_keys):
        """
        Valida que un diccionario JSON contenga todas las claves requeridas.

        :param data: Diccionario de datos JSON.
        :param required_keys: Lista de claves requeridas.
        :return: True si todas las claves están presentes, False de lo contrario.
        """
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValueError(f"Faltan las siguientes claves requeridas en el JSON: {missing_keys}")
        print("El JSON contiene todas las claves requeridas.")
        return True
