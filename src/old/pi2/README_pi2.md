
# Raspberry Pi #2 - Control de Válvulas y Lectura de Sensores de Presión

## **Descripción General**
El **Raspberry Pi #2** es responsable de gestionar las válvulas de presión y los sensores conectados al sistema. Este dispositivo opera como un cliente MQTT, enviando datos a un broker local (en Raspberry Pi #3) y, opcionalmente, a AWS IoT Core. También recibe comandos para controlar las válvulas basándose en los datos de otros dispositivos del sistema.

---

## **Características Principales**

1. **Gestión de Válvulas:**
   - Controla válvulas de presión utilizando módulos de relé conectados por I2C.
   - Recibe comandos MQTT para activar y desactivar las válvulas.

2. **Lectura de Sensores de Presión:**
   - Lee datos en tiempo real de sensores conectados al HAT Qwiic.
   - Publica las lecturas en tópicos MQTT configurados.

3. **Redundancia en la Conectividad:**
   - Prioriza la conexión LAN y utiliza Wi-Fi como respaldo en caso de falla.

4. **Soporte para MQTT Local y AWS IoT Core:**
   - Publica datos en un broker MQTT local.
   - Puede enviar datos a AWS IoT Core para análisis avanzado y monitoreo.

---

## **Estructura del Proyecto**

```plaintext
src/pi2/
│
├── config/
│   └── pi2_config.yaml              # Configuración centralizada del sistema
│
├── data/
│   ├── pressure_logs.json           # Registro de lecturas de presión
│   └── valve_logs.json              # Registro de acciones en válvulas
│
├── lib/
│   ├── pressure_sensor.py           # Manejo de sensores de presión
│   └── valve_control.py             # Control de válvulas
│
├── utils/
│   ├── json_manager.py              # Lectura/escritura de archivos JSON
│   ├── mqtt_publisher.py            # Manejo de comunicación MQTT
│   ├── networking.py                # Gestión de conectividad LAN y Wi-Fi
│   └── greengrass.py                # Soporte para AWS Greengrass (opcional)
│
├── main_pi2.py                      # Script principal
└── README.md                        # Documentación del sistema
```

---

## **Configuración del Sistema**

### **Archivo de Configuración: `pi2_config.yaml`**
Este archivo contiene la configuración completa del sistema, incluyendo:

1. **Red (LAN y Wi-Fi):**
   ```yaml
   network:
     ethernet:
       ip: "192.168.1.137"
       gateway: "192.168.1.1"
     wifi:
       ssid: "Capstone"
       password: "Elefante"
       ip: "192.168.2.11"
       gateway: "192.168.2.1"
   ```

2. **Sensores de Presión:**
   ```yaml
   pressure_sensors:
     sensors:
       - i2c_address: 0x28
         name: "valve_1_inlet"
       - i2c_address: 0x29
         name: "valve_1_outlet"
       - i2c_address: 0x2A
         name: "valve_2_inlet"
       - i2c_address: 0x2B
         name: "valve_2_outlet"
     read_interval: 5
   ```

3. **Válvulas:**
   ```yaml
   valves:
     relay_module:
       addresses:
         valve_1: 0x18
         valve_2: 0x19
     default_timeout: 2
   ```

4. **MQTT y AWS IoT Core:**
   ```yaml
   mqtt:
     broker_addresses:
       - "192.168.1.137"
       - "192.168.2.137"
     port: 1883
     topics:
       valve_control: "pi2/valve_control"
       pressure_data: "pi2/pressure_data"

   aws:
     iot_core_endpoint: "your_aws_iot_core_endpoint"
     cert_path: "/certs/certificate.pem.crt"
     key_path: "/certs/private.pem.key"
     ca_path: "/certs/AmazonRootCA1.pem"
   ```

---

## **Instrucciones de Uso**

### **1. Configuración del Entorno**
- Asegúrate de que las direcciones I2C de los sensores y válvulas sean correctas.
- Configura las credenciales de red en `pi2_config.yaml`.
- Si usarás AWS IoT Core, asegúrate de tener los certificados en el directorio `/certs`.

### **2. Instalación de Dependencias**
Ejecuta el siguiente comando para instalar las bibliotecas necesarias:
```bash
pip install -r requirements.txt
```

### **3. Ejecución del Sistema**
Para iniciar el sistema, ejecuta el script principal:
```bash
python3 main_pi2.py
```

---

## **Tópicos MQTT**

- **Publicación:**
  - **`pi2/pressure_data`**: Publica datos de presión de los sensores.
- **Suscripción:**
  - **`pi2/valve_control`**: Escucha comandos para activar/desactivar válvulas.

---

## **Pruebas Sugeridas**

1. **Conexión de Red:**
   - Desconecta LAN y verifica que el sistema cambia automáticamente a Wi-Fi.

2. **Lecturas de Sensores:**
   - Verifica que las lecturas de los sensores se publican correctamente en el tópico `pi2/pressure_data`.

3. **Control de Válvulas:**
   - Envía un comando MQTT al tópico `pi2/valve_control` y confirma que las válvulas responden correctamente.

4. **Integración con AWS IoT Core:**
   - Verifica que los datos publicados en `pressure_data` lleguen a AWS.

---

## **Contribuciones**

Si deseas contribuir a este proyecto, sigue estos pasos:
1. Haz un fork del repositorio.
2. Crea una rama para tu funcionalidad: `git checkout -b feature/nueva-funcionalidad`.
3. Envía tus cambios mediante un pull request.

---

## **Soporte**

Si encuentras problemas o tienes preguntas, abre un issue en el repositorio o contacta al equipo de desarrollo.

---

## **Licencia**

Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más información.
