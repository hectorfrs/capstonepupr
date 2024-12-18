#!/bin/bash

# Variables
PI="1"
RASPBERRY="raspberry-$PI"
CAPSTONE="/home/$RASPBERRY/capstonepupr/src/pi$PI"
REPO_URL="git@github.com:hectorfrs/capstonepupr.git"
REPO_DIR="/home/$RASPBERRY/capstonepupr"
BRANCH="main"  # Cambia si necesitas un branch diferente
LOG_FILE="/var/log/update_code.log"
SERVICE_NAME="capstone_pi$PI.service"  # Nombre del servicio systemd asociado

# Redirigir salida a un archivo log
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================="
echo "Inicio del script de actualización: $(date)"
echo "========================================="

# Verificar si el repositorio existe
if [ -d "$REPO_DIR" ]; then
    echo "El directorio del repositorio existe. Verificando actualizaciones..."
    cd "$REPO_DIR"
    
    # Obtener cambios desde el repositorio remoto
    git fetch origin
    LOCAL_HASH=$(git rev-parse HEAD)
    REMOTE_HASH=$(git rev-parse origin/$BRANCH)
    
    if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
        echo "Hay actualizaciones disponibles. Aplicando cambios..."
        git pull origin $BRANCH
        
        # Reiniciar el servicio systemd
        echo "Reiniciando el servicio $SERVICE_NAME..."
        sudo systemctl restart $SERVICE_NAME
        echo "Servicio reiniciado exitosamente."
    else
        echo "El código está actualizado. No se requieren cambios."
    fi
else
    echo "El directorio del repositorio no existe. Clonando..."
    git clone $REPO_URL $REPO_DIR
    cd "$REPO_DIR"
    git checkout $BRANCH
    
    # Configurar permisos y reiniciar servicio
    echo "Repositorio clonado. Configurando y reiniciando el servicio $SERVICE_NAME..."
    sudo systemctl restart $SERVICE_NAME
    echo "Servicio configurado y reiniciado."
fi

echo "========================================="
echo "Fin del script de actualización: $(date)"
echo "========================================="
