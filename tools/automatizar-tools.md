Manualmente correr:
1. clean_raspberry.sh
2. setup_virtual_env.sh

crontab -e

# Sincronizar código diariamente a las 2 AM
0 2 * * * bash /home/raspberry-1/sync_code.sh

# Monitorear servicios cada 5 minutos
*/5 * * * * bash /home/raspberry-1/monitor_services.sh

# Limpiar logs cada semana
0 3 * * 0 bash /home/raspberry-1/clean_logs.sh

# Generar reporte cada día a las 8 AM
0 8 * * * bash /home/raspberry-1/generate_report.sh
