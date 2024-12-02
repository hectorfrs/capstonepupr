#!/bin/bash

# Script de configuración para Raspberry Pi #1, #2 y #3
# Uso: ./setup.sh [raspberry-1|raspberry-2|raspberry-3]

# Validar entrada
if [ -z "$1" ]; then
  echo "Uso: $0 [raspberry-1|raspberry-2|raspberry-3]"
  exit 1
fi

PI=$1

# Función para instalar dependencias comunes
install_dependencies() {
  echo "Instalando dependencias comunes..."
  sudo apt-get update
  sudo apt-get install -y python3 python3-pip python3-venv i2c-tools git
  pip3 install -r requirements.txt
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
  SERVICE_NAME="$1.service"
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
  pi1)
    echo "Configurando Raspberry Pi #1..."
    REPO_URL="https://github.com/hectorfrs/capstonepupr/tree/main/src/pi1"
    DEST_DIR="/home/pi/src/pi1"
    clone_repository "$REPO_URL" "$DEST_DIR"
    install_dependencies
    setup_service "pi1"
    ;;
  pi2)
    echo "Configurando Raspberry Pi #2..."
    REPO_URL="https://github.com/hectorfrs/capstonepupr/tree/main/src/pi2"
    DEST_DIR="/home/pi/src/pi2"
    clone_repository "$REPO_URL" "$DEST_DIR"
    install_dependencies
    setup_service "pi2"
    ;;
  pi3)
    echo "Configurando Raspberry Pi #3..."
    REPO_URL="https://github.com/hectorfrs/capstonepupr/tree/main/src/pi3"
    DEST_DIR="/home/pi/src/pi3"
    clone_repository "$REPO_URL" "$DEST_DIR"
    install_dependencies
    setup_service "pi3"
    ;;
  *)
    echo "Dispositivo no reconocido: $PI"
    exit 1
    ;;
esac

echo "Configuración de $PI completada."
