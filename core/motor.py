import queue
from enum import Enum
from core.eventos import TipoEvento

# --- 2. EL CORAZÓN DEL MOTOR DE BACKTESTING ---

def motor_dirigido_por_eventos(data_feed, estrategia_piie, gestor_riesgo, exchange_emulador):
    """
    El latido del sistema. Procesa eventos hasta que se agotan los datos.
    """
    cola_eventos = queue.Queue()
    
    # El corazón da su primer latido
    data_feed.bombear_primer_tick(cola_eventos)

    while True:
        try:
            # Intentamos extraer el evento más urgente de la cola (sin bloquear)
            evento = cola_eventos.get(False)
        except queue.Empty:
            # Si el sistema procesó todo, pedimos el siguiente tick temporal
            if not data_feed.hay_mas_datos():
                print("🛑 Simulación Finalizada. Generando reporte de métricas.")
                break 
            data_feed.bombear_siguiente_tick(cola_eventos)
            continue

        if evento is not None:
            # ---------------------------------------------------------
            # ENRUTAMIENTO DE ESTADOS SEGÚN EL TIPO DE EVENTO
            # ---------------------------------------------------------
            if evento.tipo == TipoEvento.MERCADO:
                # El cerebro matemático (PIIE) analiza la estructura del precio
                estrategia_piie.evaluar_entropia(evento, cola_eventos)
                # El contable actualiza el valor del portafolio flotante
                gestor_riesgo.marcar_a_mercado(evento)

            elif evento.tipo == TipoEvento.SEÑAL:
                # El enrutador fractal decide el tamaño de la bala matemática
                gestor_riesgo.dimensionar_y_enrutar(evento, cola_eventos)

            elif evento.tipo == TipoEvento.ORDEN:
                # El francotirador envía la orden a la trinchera (Exchange Simulado)
                exchange_emulador.procesar_orden_con_latencia(evento, cola_eventos)

            elif evento.tipo == TipoEvento.EJECUCION:
                # La confirmación final. Se anota la sangre o la gloria en el balance. 
                gestor_riesgo.registrar_impacto_financiero(evento)
                print(f"⚡ FILL CONFIRMADO: {evento.cantidad}x a {evento.precio_real} | Fricción disipada: {evento.costo_friccion:.4f}")