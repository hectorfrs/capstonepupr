#!/bin/bash

set -e  # Detener la ejecución ante errores

# Variables
PI="1"
RASPBERRY="raspberry-$PI"
CAPSTONE="/home/$RASPBERRY/capstonepupr/src/pi$PI"
VENV_DIR="/home/$RASPBERRY/venv"
PYTHON_GLOBAL="/usr/bin/python3"
LOG_FILE="/home/$RASPBERRY/clean_raspberry.log"
REQUIREMENTS_FILE="$CAPSTONE/requirements.txt"
BASHRC_FILE="$HOME/.bashrc"

echo "=== Iniciando limpieza del Raspberry Pi$PI... ===" | tee -a "$LOG_FILE"

# Paso 1: Verificar el ambiente virtual
if [ -d "$VENV_DIR" ]; then
    echo "[INFO] Ambiente virtual encontrado en $VENV_DIR. Procediendo con la limpieza." | tee -a "$LOG_FILE"
else
    echo "[INFO] No se encontró un ambiente virtual en $VENV_DIR. Creándolo..." | tee -a "$LOG_FILE"
    $PYTHON_GLOBAL -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    echo "[SUCCESS] Ambiente virtual creado en $VENV_DIR." | tee -a "$LOG_FILE"
fi

# Paso 2: Activar el ambiente virtual
echo "[INFO] Activando el ambiente virtual..." | tee -a "$LOG_FILE"
source "$VENV_DIR/bin/activate" || { echo "[ERROR] No se pudo activar el ambiente virtual."; exit 1; }

# Paso 3: Desinstalar paquetes globales innecesarios
echo "[INFO] Eliminando instalaciones globales innecesarias..." | tee -a "$LOG_FILE"
pip freeze | xargs -n1 pip uninstall -y || echo "[WARNING] No se encontraron paquetes para desinstalar."

# Confirmar eliminación de paquetes globales (opcional, cuidado con sudo)
GLOBAL_PACKAGES_DIR="/usr/local/lib/python3.11/dist-packages"
USER_PACKAGES_DIR="$RASPBERRY/.local/lib/python3.11/site-packages"

if [ -d "$GLOBAL_PACKAGES_DIR" ]; then
    echo "[INFO] Limpiando directorio global de paquetes: $GLOBAL_PACKAGES_DIR" | tee -a "$LOG_FILE"
    sudo rm -rf "$GLOBAL_PACKAGES_DIR"/* || echo "[WARNING] No se pudo limpiar el directorio global."
fi

if [ -d "$USER_PACKAGES_DIR" ]; then
    echo "[INFO] Limpiando directorio de usuario de paquetes: $USER_PACKAGES_DIR" | tee -a "$LOG_FILE"
    rm -rf "$USER_PACKAGES_DIR"/* || echo "[WARNING] No se pudo limpiar el directorio de usuario."
fi

# Paso 4: Reinstalar dependencias en el ambiente virtual
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "[INFO] Instalando dependencias desde $REQUIREMENTS_FILE en el ambiente virtual..." | tee -a "$LOG_FILE"
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
    pip install -r "$REQUIREMENTS_FILE" || { echo "[ERROR] No se pudieron instalar las dependencias."; exit 1; }
else
    echo "[ERROR] No se encontró el archivo de dependencias: $REQUIREMENTS_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# Paso 5: Verificar la instalación
echo "[INFO] Verificando instalación en el ambiente virtual..." | tee -a "$LOG_FILE"
pip list | tee -a "$LOG_FILE"

# Paso 6: Configurar el PATH para usar el ambiente virtual
if ! grep -Fxq "source $VENV_DIR/bin/activate" ~/.bashrc; then
    echo "[INFO] Configurando el PATH para usar el ambiente virtual por defecto..." | tee -a "$LOG_FILE"
    echo -e "\n# Activar ambiente virtual del proyecto $PROJECT_NAME\n$ACTIVATE_SCRIPT" >> "$BASHRC_FILE"
    #echo "source $VENV_DIR/bin/activate" >> ~/.bashrc
    if [ $? -eq 0 ]; then
    echo "[SETUP] Activación automática añadida exitosamente a $BASHRC_FILE."
    else
    echo "[SETUP] Error al intentar escribir en $BASHRC_FILE. Ejecuta el script como el usuario correcto o verifica permisos."
    exit 1
    fi
    echo "[SUCCESS] PATH configurado correctamente." | tee -a "$LOG_FILE"
else
    echo "[INFO] El PATH ya estaba configurado previamente." | tee -a "$LOG_FILE"
fi
# Finalizar limpieza
echo "[SUCCESS] Limpieza completada. El ambiente virtual es el entorno principal." | tee -a "$LOG_FILE"
source ~/.bashrc