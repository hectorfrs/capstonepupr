import cv2
import boto3
import threading
import time
import os
import yaml

class CameraModule:
    def __init__(self, config_path='config/pi3_config.yaml'):
        """
        Inicializa el módulo de la cámara.

        :param config_path: Ruta al archivo de configuración YAML.
        """
        # Cargar la configuración
        self.load_config(config_path)
        # Inicializar la cámara
        self.init_camera()
        # Inicializar cliente de AWS Rekognition
        self.init_aws_client()

    def load_config(self, config_path):
        """
        Carga la configuración desde el archivo YAML.
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Archivo de configuración no encontrado en {config_path}")
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        print("Configuración de la cámara cargada.")

        # Extraer configuraciones relevantes
        camera_config = self.config['camera']
        self.width = camera_config['resolution']['width']
        self.height = camera_config['resolution']['height']
        self.frame_rate = camera_config['frame_rate']

        aws_config = self.config['aws']
        self.aws_region = aws_config.get('region', 'us-east-1')  # Región por defecto
        self.aws_access_key = aws_config.get('access_key')
        self.aws_secret_key = aws_config.get('secret_key')

    def init_camera(self):
        """
        Inicializa la cámara utilizando OpenCV.
        """
        # Inicializar la captura de video
        self.cap = cv2.VideoCapture(0)  # 0 es el ID de la cámara por defecto
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
        print("Cámara inicializada.")

    def init_aws_client(self):
        """
        Inicializa el cliente de AWS Rekognition.
        """
        self.rekognition_client = boto3.client(
            'rekognition',
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key
        )
        print("Cliente de AWS Rekognition inicializado.")

    def capture_image(self):
        """
        Captura una imagen de la cámara y la devuelve.
        """
        ret, frame = self.cap.read()
        if ret:
            print("Imagen capturada.")
            return frame
        else:
            print("Error al capturar imagen.")
            return None

    def save_image(self, frame, filename='captured_image.jpg'):
        """
        Guarda una imagen en el sistema de archivos.

        :param frame: Imagen a guardar.
        :param filename: Nombre del archivo.
        """
        cv2.imwrite(filename, frame)
        print(f"Imagen guardada como {filename}.")

    def analyze_image(self, frame):
        """
        Envía una imagen a AWS Rekognition para análisis.

        :param frame: Imagen a analizar.
        :return: Resultado del análisis.
        """
        # Codificar la imagen en formato JPEG
        _, jpeg_data = cv2.imencode('.jpg', frame)
        response = self.rekognition_client.detect_labels(
            Image={'Bytes': jpeg_data.tobytes()},
            MaxLabels=10,
            MinConfidence=75
        )
        print("Imagen analizada con AWS Rekognition.")
        return response

    def start_video_stream(self):
        """
        Inicia un hilo para capturar y analizar imágenes continuamente.
        """
        self.streaming = True
        self.thread = threading.Thread(target=self.stream_loop)
        self.thread.start()
        print("Transmisión de video iniciada.")

    def stream_loop(self):
        """
        Bucle para capturar y analizar imágenes en tiempo real.
        """
        while self.streaming:
            frame = self.capture_image()
            if frame is not None:
                # Analizar la imagen
                analysis_result = self.analyze_image(frame)
                # Aquí puedes procesar los resultados según tus necesidades
                print(f"Resultados del análisis: {analysis_result}")
            time.sleep(1 / self.frame_rate)  # Controlar la tasa de captura

    def stop_video_stream(self):
        """
        Detiene la transmisión de video.
        """
        self.streaming = False
        self.thread.join()
        print("Transmisión de video detenida.")

    def release_camera(self):
        """
        Libera los recursos de la cámara.
        """
        self.cap.release()
        print("Cámara liberada.")

# # Ejemplo de uso:

# from lib.camera_module import CameraModule

# # Inicializar el módulo de la cámara
# camera_module = CameraModule(config_path='config/pi3_config.yaml')

# try:
#     # Capturar y analizar una imagen
#     frame = camera_module.capture_image()
#     if frame is not None:
#         camera_module.save_image(frame, filename='test_image.jpg')
#         analysis_result = camera_module.analyze_image(frame)
#         print(f"Resultados del análisis: {analysis_result}")
#     else:
#         print("No se pudo capturar la imagen.")

#     # Iniciar transmisión de video y análisis en tiempo real
#     camera_module.start_video_stream()

#     # Ejecutar durante 10 segundos
#     time.sleep(10)

#     # Detener la transmisión
#     camera_module.stop_video_stream()

# finally:
#     # Liberar recursos al finalizar
#     camera_module.release_camera()
