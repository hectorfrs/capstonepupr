# mux_diagnostics.py
import logging

def run_mux_diagnostics(mux):
    """
    Ejecuta diagnósticos en el MUX conectado.
    """
    try:
        mux_status = mux.get_status()  # Método que devuelve el estado del MUX
        logging.info(f"Estado del MUX: {mux_status}")
    except Exception as e:
        logging.error(f"Error al diagnosticar el MUX: {e}")
