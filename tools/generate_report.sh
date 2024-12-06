#!/bin/bash

# Variables
PI="1"
RASPBERRY="raspberry-$PI"
REPORT_FILE="/home/$RASPBERRY/report_$(date +'%Y%m%d').txt"

# Generar reporte
echo "Generando reporte del sistema..."
{
    echo "Reporte del sistema - $(date)"
    echo
    echo "Estado de los servicios:"
    systemctl status capstone_pi1.service --no-pager
    echo
    echo "Espacio en disco:"
    df -h
    echo
    echo "Uso de memoria:"
    free -h
    echo
    echo "Logs recientes:"
    tail -n 20 /home/$RASPBERRY/logs/pi$PI_logs.log
} > "$REPORT_FILE"

echo "Reporte generado en $REPORT_FILE."
