# mux_diagnostics.py - Funciones para ejecutar diagnósticos en los canales del MUX.
import logging
from time import time
from utils.alert_manager import AlertManager


def run_mux_diagnostics(mux, channels, alert_manager=None, restart_failed=False):
    """
    Ejecuta diagnósticos en los canales especificados del MUX.

    :param mux_manager: Instancia del MUXManager.
    :param channels: Lista de canales a diagnosticar.
    :param alert_manager: Instancia de AlertManager.
    :param restart_failed: Si es True, intenta reiniciar canales defectuosos.
    :return: Diccionario con el estado de cada canal.
    """
    diagnostics_results = {}

    logging.info("[DIAGNOSTIC] [MUX]Iniciando diagnósticos del MUX...")

    for channel in channels:
        start_time = time()  # Medir tiempo de diagnóstico
        try:
            # Seleccionar y diagnosticar canal
            mux.select_channel(channel)
            if mux.is_channel_active(channel):
                diagnostics_results[channel] = "OK"
                logging.info(f"[DIAGNOSTIC] [MUX] Canal {channel} del MUX operativo.")
            else:
                diagnostics_results[channel] = "NOT_RESPONDING"
                logging.warning(f"[DIAGNOSTIC] [MUX] Canal {channel} del MUX no responde.")
                if alert_manager:
                    alert_manager.send_alert(
                        level="WARNING",
                        message=f"[DIAGNOSTIC] [MUX] Canal {channel} del MUX no responde.",
                        metadata={"channel": channel}
                    )

            # Medir tiempo tomado
            elapsed_time = time() - start_time
            logging.info(f"[DIAGNOSTIC] [MUX] Diagnóstico del canal {channel} completado en {elapsed_time:.2f} segundos.")

        except Exception as e:
            # Registrar error y enviar alerta
            diagnostics_results[channel] = f"[DIAGNOSTIC] [MUX] ERROR: {str(e)}"
            logging.error(f"[DIAGNOSTIC] [MUX] Error diagnosticando canal {channel}: {e}")
            if alert_manager:
                alert_manager.send_alert(
                    level="CRITICAL",
                    message=f"[DIAGNOSTIC] [MUX] Error diagnosticando canal {channel}",
                    metadata={"channel": channel, "error": str(e)}
                )

            # Intentar reiniciar canal si está habilitado
            if restart_failed:
                try:
                    logging.info(f"[DIAGNOSTIC] [MUX] Intentando reiniciar canal {channel}...")
                    mux.reset_channel(channel)
                    logging.info(f"[DIAGNOSTIC] [MUX] Canal {channel} reiniciado exitosamente.")
                except Exception as reset_error:
                    logging.error(f"[DIAGNOSTIC] [MUX] Error reiniciando canal {channel}: {reset_error}")
                    if alert_manager:
                        alert_manager.send_alert(
                            level="CRITICAL",
                            message=f"[DIAGNOSTIC] [MUX] Error reiniciando canal {channel}",
                            metadata={"channel": channel, "error": str(reset_error)}
                        )

    # Desactivar todos los canales al finalizar
    mux.disable_all_channels()

    # Resumen final
    logging.info("[DIAGNOSTIC] [MUX] Diagnósticos completados.")
    logging.info(f"[DIAGNOSTIC] [MUX] Resumen de diagnósticos: {diagnostics_results}")

    return diagnostics_results
