#!/bin/bash

# Variables
PI="1"
RASPBERRY="raspberry-$PI"
REPO_DIR="/home/$RASPBERRY/capstonepupr"
VENV_DIR="/home/$RASPBERRY/venv"
CAPSTONE_DIR="/home/$RASPBERRY/capstone/src/pi$PI"

# Sincronizar código
echo "Sincronizando código desde GitHub..."
cd "$REPO_DIR" || exit
git pull origin main

# Actualizar dependencias
echo "Actualizando dependencias del ambiente virtual..."
source "$VENV_DIR/bin/activate"
pip install -r $CAPSTONE/requirements.txt

echo "Sincronización y actualización completadas."
