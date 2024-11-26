#!/bin/bash

# Variables
REPO_URL="https://github.com/hectorfrs/capstonepupr.git"
REPO_DIR="/home/pi/capstonepupr"
SCRIPT_DIR="$REPO_DIR/src/pi2"
SERVICE_FILE="capstone_pi2.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_FILE"
GREENGRASS_DIR="/greengrass"

# Actualizar sistema e instalar dependencias
echo "Actualizando el sistema e instalando dependencias..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-smbus i2c-tools git

# Instalar paquetes de Python
echo "Instalando paquetes de Python..."
pip3 install pyyaml paho-mqtt AWSIoTPythonSDK

# Clonar o actualizar el repositorio
if [ -d "$REPO_DIR" ]; then
    echo "El repositorio ya existe. Actualizando..."
    cd "$REPO_DIR"
    git pull
else
    echo "Clonando el repositorio..."
    git clone "$REPO_URL" "$REPO_DIR"
fi

# Copiar el archivo de servicio
echo "Configurando el servicio systemd..."
sudo cp "$SCRIPT_DIR/services/$SERVICE_FILE" "$SERVICE_PATH"

# Recargar el daemon de systemd
sudo systemctl daemon-reload

# Habilitar e iniciar el servicio
sudo systemctl enable "$SERVICE_FILE"
sudo systemctl start "$SERVICE_FILE"

# Mostrar el estado del servicio
echo "Estado del servicio:"
sudo systemctl status "$SERVICE_FILE" --no-pager

# Instalar y configurar AWS IoT Greengrass Core
echo "Instalando AWS IoT Greengrass Core..."
GREENGRASS_VERSION="1.11.0"
wget https://d1onfpft10uf5o.cloudfront.net/greengrass-core/downloads/$GREENGRASS_VERSION/greengrass-linux-armv7l-$GREENGRASS_VERSION.tar.gz
sudo tar -xzvf greengrass-linux-armv7l-$GREENGRASS_VERSION.tar.gz -C /

# Configurar usuario y grupo para Greengrass
sudo adduser --system ggc_user
sudo addgroup --system ggc_group

# Configurar permisos
sudo chown -R ggc_user:ggc_group /greengrass

echo "AWS IoT Greengrass Core instalado. Recuerda completar la configuración según la documentación oficial."

cd /$REPO_DIR

mkdir -p /logs
chmod 755 /logs

mkdir -p /data
chmod 755 /data