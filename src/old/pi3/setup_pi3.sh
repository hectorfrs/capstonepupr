#!/bin/bash

# Variables
REPO_URL="https://github.com/hectorfrs/capstonepupr.git"
REPO_DIR="/home/raspberry-3/capstonepupr"
SCRIPT_DIR="$REPO_DIR/src/pi3"
SERVICE_FILE="capstone_pi3.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_FILE"
GREENGRASS_DIR="/greengrass"
LOG_FILE="/var/log/setup_pi3.log"

# Redirigir salida a un archivo log
exec > >(tee -i $LOG_FILE) 2>&1

# Crear directorio de Capstone
echo "Validando existencia de directorio Capstone..."
if [ -d "$REPO_DIR" ]; then
    echo "El directorio ya existe."
else
    echo "Creando directorio..."
    mkdir -p "$REPO_DIR"
fi

# Actualizar sistema e instalar dependencias
echo "Actualizando el sistema e instalando dependencias..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-smbus i2c-tools git nodejs unzip mosquitto mosquitto-clients tk gcc build-essential

# Configurar Mosquitto como broker MQTT
echo "Configurando Mosquitto como broker MQTT..."
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
sudo systemctl status mosquitto --no-pager

# Verificar si I2C está habilitado
echo "Verificando estado de I2C..."
if ! ls /dev/i2c-* > /dev/null 2>&1; then
    echo "I2C no está habilitado. Habilítalo desde raspi-config."
else
    echo "I2C está habilitado."
fi

# Escanear dispositivos I2C
echo "Escaneando dispositivos I2C conectados..."
i2cdetect -y 1

# Instalar dependencias de Python
echo "Instalando paquetes de Python..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip3 install -r "$SCRIPT_DIR/requirements.txt"
else
    pip3 install pyyaml paho-mqtt AWSIoTPythonSDK smbus2
fi

# Clonar o actualizar el repositorio
if [ -d "$REPO_DIR" ]; then
    echo "El repositorio ya existe. Actualizando..."
    cd "$REPO_DIR"
    git pull
else
    echo "Clonando el repositorio..."
    git clone "$REPO_URL" "$REPO_DIR"
fi

# Configurar servicio systemd
echo "Configurando el servicio systemd..."
sudo cp "$SCRIPT_DIR/services/$SERVICE_FILE" "$SERVICE_PATH"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_FILE"
sudo systemctl start "$SERVICE_FILE"
sudo systemctl status "$SERVICE_FILE" --no-pager

# Descargar e instalar Greengrass V2
echo "Descargando e instalando AWS IoT Greengrass V2..."
wget -q https://d1onfpft10uf5o.cloudfront.net/greengrass-core/downloads/latest/greengrass-v2.zip
sudo unzip -o greengrass-v2.zip -d $GREENGRASS_DIR
sudo $GREENGRASS_DIR/greengrass-cli install --aws-region <your-region> --thing-name pi3-thing --thing-group-name Capstone-Group
sudo /greengrass/v2/bin/greengrass-cli component list

# Crear directorios de logs y datos
echo "Validando directorios /logs y /data..."
mkdir -p "$REPO_DIR/src/pi3/logs" "$REPO_DIR/src/pi3/data"
chmod 755 "$REPO_DIR/src/pi3/logs" "$REPO_DIR/src/pi3/data"

echo "Asignando permisos a los directorios..."
chmod 644 /etc/systemd/system/capstone_pi3.service
chmod +x /home/raspberry-3/capstonepupr/src/pi3/scripts/main_pi3.py


echo "Configuración de Raspberry Pi 3 completada."
