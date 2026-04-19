import random
from core.eventos import EventoEjecucion

class EmuladorExchange:
    def __init__(self, latencia_ms=20, comision_base=0.0002):
        self.latencia_base = latencia_ms / 1000.0
        self.comision_base = comision_base

    def procesar_orden_con_latencia(self, evento_orden, cola_eventos):
        latencia_real = self.latencia_base + random.uniform(0, 0.005)
        precio_señal = evento_orden.precio_limite
        
        volatilidad_simulada = random.uniform(0.0001, 0.001)
        slippage_ratio = volatilidad_simulada
        
        if evento_orden.tipo_orden == 'MARKET':
            if evento_orden.cantidad > 0:
                # COMPRA A MERCADO: Pagamos más caro por el desorden
                precio_ejecucion = precio_señal * (1 + slippage_ratio)
            else:
                # VENTA A MERCADO (PÁNICO): Nos pagan menos porque no hay liquidez
                precio_ejecucion = precio_señal * (1 - slippage_ratio)
        else:
            # Orden LIMIT se ejecuta al precio deseado
            precio_ejecucion = precio_señal

        # La comisión se cobra en dólares en base al volumen total movido (abs evita valores negativos)
        volumen_dolares = abs(evento_orden.cantidad * precio_ejecucion)
        costo_friccion = volumen_dolares * self.comision_base

        ejecucion = EventoEjecucion(
            activo=evento_orden.activo,
            cantidad=evento_orden.cantidad,
            precio_real=precio_ejecucion,
            costo_friccion=costo_friccion
        )
        
        cola_eventos.put(ejecucion)