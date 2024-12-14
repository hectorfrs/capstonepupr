#!/bin/bash

# Variables
PI="1"
RASPBERRY="raspberry-$PI"
CAPSTONE="/home/$RASPBERRY/capstonepupr/src/pi$PI"
VENV_DIR="/home/$RASPBERRY/venv"
PYTHON_PATH="/usr/bin/python3"

# Crear ambiente virtual
echo "Creando ambiente virtual en $VENV_DIR..."
if [ -d "$VENV_DIR" ]; then
    echo "El ambiente virtual ya existe. Eliminando..."
    rm -rf "$VENV_DIR"
fi

$PYTHON_PATH -m venv "$VENV_DIR"

# Activar ambiente virtual e instalar dependencias
source "$VENV_DIR/bin/activate"
echo "Instalando dependencias..."
pip install --upgrade pip
pip install --break-system-packages -r $CAPSTONE/requirements.txt

echo "Ambiente virtual configurado correctamente en $VENV_DIR."
