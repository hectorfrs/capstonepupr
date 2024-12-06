#!/bin/bash

# Variables
PI="1"
SERVICE_NAME="capstone_pi$PI.service"

# Verificar estado del servicio
echo "Verificando estado del servicio $SERVICE_NAME..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "El servicio $SERVICE_NAME está activo."
else
    echo "El servicio $SERVICE_NAME no está activo. Reiniciando..."
    systemctl restart "$SERVICE_NAME"
    echo "Servicio $SERVICE_NAME reiniciado."
fi
