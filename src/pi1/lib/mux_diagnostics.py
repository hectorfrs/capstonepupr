# mux_diagnostics.py - Funciones para ejecutar diagnósticos en los canales del MUX.
import logging
from utils.alert_manager import AlertManager

def run_mux_diagnostics(mux_manager, channels, alert_manager):
    """
    Ejecuta diagnósticos en los canales especificados del MUX.

    :param mux: Instancia del MUXManager.
    :param channels: Lista de canales a diagnosticar.
    :param alert_manager: Instancia de AlertManager.
    """
    for channel in channels:
        try:
            mux_manager.select_channel(channel)
            if mux_manager.is_channel_active(channel):
                logging.info(f"Canal {channel} del MUX operativo.")
            else:
                logging.warning(f"Canal {channel} del MUX no responde.")
        except Exception as e:
            logging.error(f"Error diagnosticando canal {channel}: {e}")
            alert_manager.send_alert(
                level="CRITICAL",
                message=f"Error diagnosticando canal {channel}",
                metadata={"channel": channel, "error": str(e)}
            )