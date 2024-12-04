# mux_diagnostics.py
import logging
from utils.alert_manager import AlertManager

def run_mux_diagnostics(mux, channels, alert_manager=None):
    """
    Ejecuta diagnósticos en el MUX conectado.
    """
    try:
        mux_status = mux.get_status()  # Método que devuelve el estado del MUX
        logging.info(f"Estado del MUX: {mux_status}")

        for channel in channels:
            try:
                mux.select_channel(channel)
                logging.info(f"Canal {channel} del MUX operativo.")
            except Exception as e:
                message = f"Error en el canal {channel} del MUX: {e}"
                logging.error(message)
                if alert_manager:
                    alert_manager.send_alert("CRITICAL", message, {"mux_channel": channel})
    except Exception as e:
        message = f"Error al diagnosticar el MUX: {e}"
        logging.error(message)
        if alert_manager:
            alert_manager.send_alert("CRITICAL", message, {"mux_status": "failure"})
