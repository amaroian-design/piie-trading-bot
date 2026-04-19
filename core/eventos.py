import queue
from enum import Enum

# --- 1. DEFINICIÓN DE LA JERARQUÍA DE EVENTOS ---

class TipoEvento(Enum):
    MERCADO = 'MERCADO'
    SEÑAL = 'SEÑAL'
    ORDEN = 'ORDEN'
    EJECUCION = 'EJECUCION'

class Evento:
    """Clase base polimórfica para todos los eventos."""
    pass

class EventoMercado(Evento):
    def __init__(self, datos_tick, timestamp):
        self.tipo = TipoEvento.MERCADO
        self.datos_tick = datos_tick
        self.timestamp = timestamp

class EventoSeñal(Evento):
    def __init__(self, activo, diagnostico_piie, energia_psi, dI=0.0, gamma=0.0, prob_colapso=0.0):
        self.tipo = TipoEvento.SEÑAL
        self.activo = activo
        self.diagnostico_piie = diagnostico_piie
        self.energia_psi = energia_psi
        self.dI = dI
        self.gamma = gamma
        self.prob_colapso = prob_colapso # 🦇 NUEVO SENSOR: El Radar de Murciélago

class EventoOrden(Evento):
    def __init__(self, activo, tipo_orden, cantidad, precio_limite=None):
        self.tipo = TipoEvento.ORDEN
        self.activo = activo
        self.tipo_orden = tipo_orden # 'MARKET', 'LIMIT', 'ICEBERG'
        self.cantidad = cantidad
        self.precio_limite = precio_limite

class EventoEjecucion(Evento):
    def __init__(self, activo, cantidad, precio_real, costo_friccion):
        self.tipo = TipoEvento.EJECUCION
        self.activo = activo
        self.cantidad = cantidad
        self.precio_real = precio_real           # Precio después del slippage
        self.costo_friccion = costo_friccion  