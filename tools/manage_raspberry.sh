#!/bin/bash

SERVICE_NAME="capstone_pi1.service"
LOG_FILE="/home/raspberry-1/logs/capstone_pi1.log"
ERROR_LOG_FILE="/home/raspberry-1/logs/capstone_pi1_error.log"

function start_service {
    echo "Iniciando $SERVICE_NAME..."
    sudo systemctl start $SERVICE_NAME
    if [ $? -eq 0 ]; then
        echo "$SERVICE_NAME iniciado exitosamente."
    else
        echo "Error al iniciar $SERVICE_NAME. Verifica los logs."
    fi
}

function stop_service {
    echo "Deteniendo $SERVICE_NAME..."
    sudo systemctl stop $SERVICE_NAME
    if [ $? -eq 0 ]; then
        echo "$SERVICE_NAME detenido exitosamente."
    else
        echo "Error al detener $SERVICE_NAME."
    fi
}

function restart_service {
    echo "Reiniciando $SERVICE_NAME..."
    sudo systemctl restart $SERVICE_NAME
    if [ $? -eq 0 ]; then
        echo "$SERVICE_NAME reiniciado exitosamente."
    else
        echo "Error al reiniciar $SERVICE_NAME. Verifica los logs."
    fi
}

function status_service {
    echo "Verificando el estado de $SERVICE_NAME..."
    sudo systemctl status $SERVICE_NAME
}

function show_logs {
    echo "Mostrando logs de $SERVICE_NAME..."
    echo "Logs estándar:"
    tail -n 20 $LOG_FILE
    echo ""
    echo "Logs de errores:"
    tail -n 20 $ERROR_LOG_FILE
}

case $1 in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
