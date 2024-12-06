#!/bin/bash

# Script de configuración para Raspberry Pi #1, #2 y #3
# Uso: ./setup.sh [raspberry-1|raspberry-2|raspberry-3]

# Validar entrada
if [ -z "$1" ]; then
  echo "Uso: $0 [1|2|3]"
  exit 1
fi

PI=$1

# Función para instalar dependencias comunes
install_dependencies() {
  echo "Instalando dependencias comunes..."
  sudo apt-get update
  sudo apt-get install -y python3 python3-pip python3-venv i2c-tools git libcamera-apps python3-picamera2 python3-tk awscli

  pip3 install --break-system-packages -r /home/raspberry-$PI/capstonepupr/src/pi$PI/requirements.txt
}

# Función para clonar el repositorio específico
clone_repository() {
  REPO_URL="$1"
  DEST_DIR="$2"
  
  echo "Clonando el repositorio desde $REPO_URL..."
  
  if [ -d "$DEST_DIR" ]; then
    echo "Directorio $DEST_DIR ya existe. Realizando git pull..."
    cd "$DEST_DIR" || exit
    git pull
    cd - || exit
  else
    git clone "$REPO_URL" "$DEST_DIR"
  fi
}

# Función para configurar servicios
setup_service() {
  SERVICE_NAME="capstone-pi$PI.service"
  SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
  echo "Configurando servicio para $SERVICE_NAME..."

  if [ -f "./services/$SERVICE_NAME" ]; then
    sudo cp "./services/$SERVICE_NAME" "$SERVICE_FILE"
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    sudo systemctl start "$SERVICE_NAME"
  else
    echo "Archivo de servicio $SERVICE_NAME no encontrado."
  fi
}

# Configuración específica por dispositivo
case $PI in
  1)
    echo "Configurando Raspberry Pi #1..."
    REPO_URL="https://github.com/hectorfrs/capstonepupr/tree/main/src/pi$PI"
    DEST_DIR="/home/raspberry-$PI/capstonepupr/src/pi$PI"
    clone_repository "$REPO_URL" "$DEST_DIR"
    install_dependencies
    setup_service "raspberry-$PI"
    ;;
  2)
    echo "Configurando Raspberry Pi #2..."
    REPO_URL="https://github.com/hectorfrs/capstonepupr/tree/main/src/pi$PI"
    DEST_DIR="/home/raspberry-$PI/capstonepupr/src/pi$PI"
    clone_repository "$REPO_URL" "$DEST_DIR"
    install_dependencies
    setup_service "raspberry-$pi"
    ;;
  3)
    echo "Configurando Raspberry Pi #3..."
    REPO_URL="https://github.com/hectorfrs/capstonepupr/tree/main/src/pi$PI"
    DEST_DIR="/home/raspberry-$PI/capstonepupr/src/pi$PI"
    clone_repository "$REPO_URL" "$DEST_DIR"
    install_dependencies
    setup_service "raspberry-$PI"
    ;;
  *)
    echo "Dispositivo no reconocido: raspberry-$PI"
    exit 1
    ;;
esac

echo "Configuración de raspberry-$PI completada."
