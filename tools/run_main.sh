#!/bin/bash

# Configuración
PI="1"
RASPBERRY="raspberry-$PI"
PROJECT_DIR="/home/$RASPBERRY/capstonepupr"
VENV_DIR="/home/$RASPBERRY/venv"
MAIN_SCRIPT="$PROJECT_DIR/src/pi$PI/scripts/main_pi$PI.py"
LOG_DIR="/home/$RASPBERRY/logs"
LOG_FILE="$LOG_DIR/pi$PI_execution.log"

# Crear el directorio de logs si no existe
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
fi

# Activar el entorno virtual
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "El entorno virtual no existe en $VENV_DIR"
    exit 1
fi

# Configurar el PYTHONPATH
export PYTHONPATH="$PROJECT_DIR/src/pi1:$PYTHONPATH"

# Ejecutar el script principal y registrar la salida en un archivo de log
echo "Ejecutando main_pi1.py..."
{
    echo "========== INICIO DE EJECUCIÓN: $(date) =========="
    python3 "$MAIN_SCRIPT"
    echo "========== FIN DE EJECUCIÓN: $(date) =========="
} >> "$LOG_FILE" 2>&1

# Manejo de rotación de logs
MAX_LOG_SIZE=10485760 # 10 MB
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(stat -c%s "$LOG_FILE")
    if [ "$LOG_SIZE" -ge "$MAX_LOG_SIZE" ]; then
        mv "$LOG_FILE" "$LOG_FILE.$(date +%Y%m%d%H%M%S)"
        echo "El archivo de log ha sido rotado debido a su tamaño."
    fi
fi

echo "Ejecución completada. Revisa los logs en $LOG_FILE"
