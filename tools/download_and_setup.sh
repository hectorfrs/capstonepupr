#!/bin/bash

# Variables
REPO_URL="https://github.com/hectorfrs/capstonepupr.git"
CLONE_DIR="/home/raspberry-1/capstonepupr"
SETUP_SCRIPT="setup_pi1.sh"

# Verificar si git está instalado
if ! command -v git &> /dev/null; then
    echo "Git no está instalado. Instalándolo ahora..."
    sudo apt update && sudo apt install -y git
fi

# Clonar o actualizar el repositorio
echo "Verificando el repositorio en $CLONE_DIR..."
if [ -d "$CLONE_DIR" ]; then
    echo "El repositorio ya existe. Actualizando..."
    cd "$CLONE_DIR"
    git pull origin main
else
    echo "Clonando el repositorio desde $REPO_URL..."
    git clone "$REPO_URL" "$CLONE_DIR"
fi

# Verificar el archivo de configuración de setup
SETUP_PATH="$CLONE_DIR/src/pi1/$SETUP_SCRIPT"

if [ -f "$SETUP_PATH" ]; then
    echo "Encontrado $SETUP_SCRIPT en $SETUP_PATH."
    echo "Cambiando permisos del script para hacerlo ejecutable..."
    chmod +x "$SETUP_PATH"

    echo "Ejecutando $SETUP_SCRIPT..."
    "$SETUP_PATH"
else
    echo "El archivo $SETUP_SCRIPT no se encontró en $SETUP_PATH."
    echo "Verifica que el repositorio y la estructura sean correctos."
    exit 1
fi

echo "Proceso completado."
