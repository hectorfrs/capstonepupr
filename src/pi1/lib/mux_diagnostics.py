# mux_diagnostics.py - Funciones para ejecutar diagnósticos en los canales del MUX.
import logging
from time import time
from utils.alert_manager import AlertManager


def run_mux_diagnostics(mux_manager, channels, alert_manager, restart_failed=False):
    """
    Ejecuta diagnósticos en los canales especificados del MUX.

    :param mux_manager: Instancia del MUXManager.
    :param channels: Lista de canales a diagnosticar.
    :param alert_manager: Instancia de AlertManager.
    :param restart_failed: Si es True, intenta reiniciar canales defectuosos.
    :return: Diccionario con el estado de cada canal.
    """
    diagnostics_results = {}

    logging.info("Iniciando diagnósticos del MUX...")

    for channel in channels:
        start_time = time()  # Medir tiempo de diagnóstico
        try:
            # Seleccionar y diagnosticar canal
            mux_manager.select_channel(channel)
            if mux_manager.is_channel_active(channel):
                diagnostics_results[channel] = "OK"
                logging.info(f"Canal {channel} del MUX operativo.")
            else:
                diagnostics_results[channel] = "NOT_RESPONDING"
                logging.warning(f"Canal {channel} del MUX no responde.")
                if alert_manager:
                    alert_manager.send_alert(
                        level="WARNING",
                        message=f"Canal {channel} del MUX no responde.",
                        metadata={"channel": channel}
                    )

            # Medir tiempo tomado
            elapsed_time = time() - start_time
            logging.info(f"Diagnóstico del canal {channel} completado en {elapsed_time:.2f} segundos.")

        except Exception as e:
            # Registrar error y enviar alerta
            diagnostics_results[channel] = f"ERROR: {str(e)}"
            logging.error(f"Error diagnosticando canal {channel}: {e}")
            if alert_manager:
                alert_manager.send_alert(
                    level="CRITICAL",
                    message=f"Error diagnosticando canal {channel}",
                    metadata={"channel": channel, "error": str(e)}
                )

            # Intentar reiniciar canal si está habilitado
            if restart_failed:
                try:
                    logging.info(f"Intentando reiniciar canal {channel}...")
                    mux_manager.reset_channel(channel)
                    logging.info(f"Canal {channel} reiniciado exitosamente.")
                except Exception as reset_error:
                    logging.error(f"Error reiniciando canal {channel}: {reset_error}")
                    if alert_manager:
                        alert_manager.send_alert(
                            level="CRITICAL",
                            message=f"Error reiniciando canal {channel}",
                            metadata={"channel": channel, "error": str(reset_error)}
                        )

    # Desactivar todos los canales al finalizar
    mux_manager.disable_all_channels()

    # Resumen final
    logging.info("Diagnósticos completados.")
    logging.info(f"Resumen de diagnósticos: {diagnostics_results}")

    return diagnostics_results
