#!/bin/bash

# Variables
PI="1"
RASPBERRY="raspberry-$PI"
LOG_DIR="/home/$RASPBERRY/logs"
MAX_SIZE_MB=10

# Rotar logs
echo "Rotando logs en $LOG_DIR..."
find "$LOG_DIR" -type f -name "*.log" -exec sh -c '
    for log; do
        size=$(du -m "$log" | cut -f1)
        if [ "$size" -ge '"$MAX_SIZE_MB"' ]; then
            echo "El archivo $log excede $MAX_SIZE_MB MB. Rotando..."
            mv "$log" "$log.bak"
            echo "Archivo $log rotado correctamente."
        fi
    done
' sh {} +

echo "Rotación de logs completada."
