#!/bin/bash

set -e  # Detener la ejecución ante errores

# Verificar si el script se ejecutó con "sudo -E"
if [ -z "$SUDO_USER" ] || [ "$SUDO_USER" == "root" ] || [ -z "$HOME" ] || [ "$HOME" == "/root" ]; then
    echo "[ERROR] Este script debe ejecutarse usando 'sudo -E ./clean_raspberry.sh'."
    echo "Ejemplo: sudo -E $0"
    exit 1
fi

# Continuar ejecución del script
echo "[INFO] Script ejecutado correctamente con 'sudo -E' por el usuario: $SUDO_USER"

# Solicitar al usuario el número de Raspberry Pi
read -p "Introduce el número de Raspberry Pi (1, 2, 3...): " PI
PI=${PI:-1}  # Si no se introduce un valor, usar "1" como predeterminado

# Obtener el nombre de usuario activo y validarlo
USER_LOGNAME=$(logname)

if [[ "$USER_LOGNAME" =~ ^raspberry-(1|2|3)$ ]]; then
    echo "[INFO] Usuario activo detectado como $USER_LOGNAME."
    RASPBERRY="$USER_LOGNAME"
else
    echo "[ERROR] Usuario $USER_LOGNAME no válido. Debe ser raspberry-1, raspberry-2 o raspberry-3."
    exit 1
fi

# Variables
CAPSTONE="/home/$RASPBERRY/capstonepupr/src/pi$PI"
VENV_DIR="/home/$RASPBERRY/venv"
PYTHON_GLOBAL="/usr/bin/python3"
LOG_FILE="/home/$RASPBERRY/clean_raspberry.log"
REQUIREMENTS_FILE="$CAPSTONE/requirements.txt"
BASHRC_FILE="/home/$RASPBERRY/.bashrc"

echo "=== Iniciando limpieza y reconstrucción del entorno virtual en Raspberry Pi$PI ===" | tee -a "$LOG_FILE"

# Paso 1: Eliminar el entorno virtual si existe
if [ -d "$VENV_DIR" ]; then
    echo "[INFO] Se encontró un entorno virtual en $VENV_DIR. Eliminándolo..." | tee -a "$LOG_FILE"
    rm -rf "$VENV_DIR"
    echo "[SUCCESS] Entorno virtual eliminado." | tee -a "$LOG_FILE"
fi

# Paso 2: Crear un nuevo entorno virtual
echo "[INFO] Creando un nuevo entorno virtual en $VENV_DIR..." | tee -a "$LOG_FILE"
$PYTHON_GLOBAL -m venv "$VENV_DIR"
echo "[SUCCESS] Nuevo entorno virtual creado en $VENV_DIR." | tee -a "$LOG_FILE"

# Paso 3: Activar el entorno virtual
source "$VENV_DIR/bin/activate" | tee -a "$LOG_FILE"
echo "[INFO] Entorno virtual activado correctamente." | tee -a "$LOG_FILE"

# Paso 4: Actualizar herramientas base
echo "[SETUP] Actualizando pip, setuptools y wheel..." | tee -a "$LOG_FILE"
sudo apt update && sudo apt upgrade -y  || { echo "[ERROR] Fallo en la actualización de paquetes."; exit 1; }
sudo apt install -y libjpeg-dev libpng-dev libtiff-dev zlib1g-dev libopenjp2-7 libopenjp2-7-dev || { echo "[ERROR] Fallo en la instalación de paquetes."; exit 1; }
$VENV_DIR/bin/pip install --upgrade pip setuptools wheel | tee -a "$LOG_FILE"

# Paso 5: Instalar dependencias desde requirements.txt
echo "[INFO] Instalando dependencias desde $REQUIREMENTS_FILE..." | tee -a "$LOG_FILE"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "[INFO] Creando archivo requirements.txt..." | tee -a "$LOG_FILE"
    cat <<EOL > "$REQUIREMENTS_FILE"
sparkfun-qwiic
sparkfun-qwiic-relay
sparkfun-qwiic-i2c
smbus2
paho-mqtt==1.6.1
PyYAML
boto3
watchdog
RPi.GPIO
numpy
matplotlib
flask
logging
EOL
fi

$VENV_DIR/bin/pip install -r "$REQUIREMENTS_FILE" | tee -a "$LOG_FILE"

# # Paso 6: Configurar PYTHONPATH
# PYTHONPATH_LINE="export PYTHONPATH=$CAPSTONE:\$PYTHONPATH"
# if ! grep -qxF "$PYTHONPATH_LINE" "$BASHRC_FILE"; then
#     echo "[INFO] Configurando PYTHONPATH en ~/.bashrc..." | tee -a "$LOG_FILE"
#     echo "$PYTHONPATH_LINE" >> "$BASHRC_FILE"
#     echo "[SUCCESS] PYTHONPATH configurado correctamente." | tee -a "$LOG_FILE"
# else
#     echo "[INFO] PYTHONPATH ya está configurado en ~/.bashrc." | tee -a "$LOG_FILE"
# fi

# # Paso 7: Priorizar el entorno virtual en el PATH
# PATH_LINE="export PATH=$VENV_DIR/bin:\$PATH"
# if ! grep -qxF "$PATH_LINE" "$BASHRC_FILE"; then
#     echo "[INFO] Configurando PATH para priorizar el entorno virtual..." | tee -a "$LOG_FILE"
#     echo "$PATH_LINE" >> "$BASHRC_FILE"
#     echo "[SUCCESS] PATH configurado correctamente." | tee -a "$LOG_FILE"
# else
#     echo "[INFO] PATH ya está configurado en ~/.bashrc." | tee -a "$LOG_FILE"
# fi

# Paso 8: Limpiar archivos temporales
echo "[INFO] Limpiando archivos temporales innecesarios..." | tee -a "$LOG_FILE"
sudo find /tmp -type f -atime +1 -delete | tee -a "$LOG_FILE"
sudo find /tmp -type d -empty -delete | tee -a "$LOG_FILE"
TEMP_USER_DIR="/home/$USER/.cache"
if [ -d "$TEMP_USER_DIR" ]; then
    rm -rf "$TEMP_USER_DIR"/* | tee -a "$LOG_FILE"
fi
echo "[SUCCESS] Archivos temporales limpiados correctamente." | tee -a "$LOG_FILE"

# Paso 9: Reescribir o añadir configuración específica en ~/.bashrc
echo "[INFO] Configurando ~/.bashrc con configuraciones específicas..." | tee -a "$LOG_FILE"

# Eliminar bloques anteriores si existen
sed -i '/# Activar entorno virtual automáticamente/,/# sudo \/etc\/init.d\/xrdp start > \/dev\/null/d' "$BASHRC_FILE"

# Escribir el bloque exactamente como se requiere
cat <<EOL >> "$BASHRC_FILE"
# Activar entorno virtual automáticamente
source /home/$RASPBERRY/venv/bin/activate

# Configurar PYTHONPATH para el proyecto Capstone
export PYTHONPATH=/home/$RASPBERRY/capstonepupr/src/pi$PI:\$PYTHONPATH

# Priorizar entorno virtual en PATH
export PATH=/home/$RASPBERRY/venv/bin:\$PATH

# Nota: Para evitar sudo en ~/.bashrc, configura xrdp con systemd
# sudo /etc/init.d/xrdp start > /dev/null   # Esta línea se debería mover fuera de ~/.bashrc
EOL

echo "[SUCCESS] Configuración de ~/.bashrc completada correctamente." | tee -a "$LOG_FILE"

# Aplicar cambios
echo "[INFO] Aplicando cambios del bashrc..." | tee -a "$LOG_FILE"
source "$BASHRC_FILE"

# Finalización
echo "[SUCCESS] Entorno virtual reconstruido correctamente. Reinicia sesión o ejecuta 'source ~/.bashrc'." | tee -a "$LOG_FILE"
