#!/bin/bash

# Script de configuración del entorno virtual
# Desarrollado por Héctor F. Rivera Santiago
# Proyecto: Smart Recycling Bin

# Variables del proyecto
PI="1"
RASPBERRY="raspberry-$PI"
PROJECT_NAME="capstonepupr"
PROJECT_DIR="$HOME/$RASPBERRY/"
VENV_DIR="$PROJECT_DIR/venv"
REQUIREMENTS_FILE="$PROJECT_DIR/$PROJECT_NAME/src/pi$PI/requirements.txt"
BASHRC_FILE="$HOME/.bashrc"

# Crear directorio del proyecto
echo "[SETUP] Creando directorio del proyecto en $PROJECT_DIR..."
#mkdir -p "$PROJECT_DIR"

# Crear ambiente virtual
if [ ! -d "$VENV_DIR" ]; then
  echo "[SETUP] Creando ambiente virtual en $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
else
  echo "[SETUP] Ambiente virtual ya existe en $VENV_DIR."
fi

# Activar ambiente virtual
echo "[SETUP] Activando ambiente virtual..."
source "$VENV_DIR/bin/activate"

# Actualizar pip y herramientas base
echo "[SETUP] Actualizando pip, setuptools y wheel..."
pip install --upgrade pip setuptools wheel

# Crear archivo requirements.txt si no existe
if [ ! -f "$REQUIREMENTS_FILE" ]; then
  echo "[SETUP] Creando archivo requirements.txt..."
  cat <<EOL > "$REQUIREMENTS_FILE"
sparkfun-qwiic
sparkfun-qwiic-relay
sparkfun-qwiic-i2c
smbus2
paho-mqtt
PyYAML
boto3
watchdog
RPi.GPIO
numpy                       
matplotlib                  
flask                       
EOL
else
  echo "[SETUP] requirements.txt ya existe."
fi

# Instalar dependencias
echo "[SETUP] Instalando dependencias desde requirements.txt..."
pip install -r "$REQUIREMENTS_FILE"

# Configurar activación automática del venv al iniciar sesión
ACTIVATE_SCRIPT="source $VENV_DIR/bin/activate"

if grep -Fxq "$ACTIVATE_SCRIPT" "$BASHRC_FILE"; then
  echo "[SETUP] Activación automática ya configurada en $BASHRC_FILE."
else
  echo "[SETUP] Configurando activación automática del ambiente virtual..."
  echo -e "\n# Activar ambiente virtual del proyecto $PROJECT_NAME\n$ACTIVATE_SCRIPT" >> "$BASHRC_FILE"
  if [ $? -eq 0 ]; then
    echo "[SETUP] Activación automática añadida exitosamente a $BASHRC_FILE."
  else
    echo "[SETUP] Error al intentar escribir en $BASHRC_FILE. Ejecuta el script como el usuario correcto o verifica permisos."
    exit 1
  fi
fi

# Finalización
echo "[SETUP] Configuración completa. Reinicia tu sesión o ejecuta 'source ~/.bashrc' para activar el ambiente virtual por defecto."
