#!/bin/bash

# Variables
PI="1"
RASPBERRY="raspberry-$PI"
CAPSTONE="/home/$RASPBERRY/capstonepupr/src/pi$PI"
VENV_DIR="/home/$RASPBERRY/venv"
PYTHON_GLOBAL="/usr/bin/python3"
LOG_FILE="/home/$RASPBERRY/clean_raspberry.log"

CAPSTONE="/home/raspberry-1/capstonepupr/src/pi1"

echo "Iniciando limpieza del Raspberry Pi..." | tee -a "$LOG_FILE"

# Paso 1: Verificar el ambiente virtual
if [ -d "$VENV_DIR" ]; then
    echo "Ambiente virtual encontrado en $VENV_DIR. Procediendo con la limpieza." | tee -a "$LOG_FILE"
else
    echo "No se encontró un ambiente virtual en $VENV_DIR. Creándolo..." | tee -a "$LOG_FILE"
    $PYTHON_GLOBAL -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    echo "Ambiente virtual creado en $VENV_DIR." | tee -a "$LOG_FILE"
fi

# Paso 2: Activar el ambiente virtual
echo "Activando el ambiente virtual..." | tee -a "$LOG_FILE"
source "$VENV_DIR/bin/activate"

# Paso 3: Desinstalar paquetes globales innecesarios
echo "Eliminando instalaciones globales innecesarias..." | tee -a "$LOG_FILE"
pip freeze --user | xargs -n1 pip uninstall -y

# Confirmar eliminación de paquetes globales
if [ -d "/usr/local/lib/python3.11/dist-packages" ]; then
    echo "Limpiando directorio global de paquetes..." | tee -a "$LOG_FILE"
    sudo rm -rf /usr/local/lib/python3.11/dist-packages/*
fi

if [ -d "$RASPBERRY/.local/lib/python3.11/site-packages" ]; then
    echo "Limpiando directorio de usuario de paquetes..." | tee -a "$LOG_FILE"
    rm -rf $RASPBERRY/.local/lib/python3.11/site-packages/*
fi

# Paso 4: Reinstalar dependencias en el ambiente virtual
echo "Instalando dependencias en el ambiente virtual..." | tee -a "$LOG_FILE"
pip install -r $CAPSTONE/requirements.txt

# Paso 5: Verificar la instalación
echo "Verificando instalación en el ambiente virtual..." | tee -a "$LOG_FILE"
pip list

# Paso 6: Configurar el PATH para usar el ambiente virtual
echo "Configurando el PATH para usar el ambiente virtual por defecto..." | tee -a "$LOG_FILE"
echo "source $VENV_DIR/bin/activate" >> $RASPBERRY/.bashrc
source $RASPBERRY.bashrc

# Finalizar limpieza
echo "Limpieza completada. El ambiente virtual es el entorno principal." | tee -a "$LOG_FILE"
