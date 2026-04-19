import queue
from enum import Enum
from core.eventos import EventoOrden
from modulos.ia import OraculoAI 

class GestorRiesgoInstitucional:
    def __init__(self, capital_inicial=100000.0):
        self.capital_actual = capital_inicial
        self.precio_mercado_actual = 0.0 
        self.inventario_activo = 0.0 
        self.costo_total_inventario = 0.0 
        self.cooldown_ticks = 0 
        self.precio_maximo_alcanzado = 0.0
        
        self.ia = OraculoAI(umbral_confianza=0.60, tasa_aprendizaje=0.01)
        self.win_rate_estimado = 0.55 
        self.payoff_ratio = 1.5       
        self.multiplicador_kelly = 0.5 
        
        # 📊 BITÁCORA
        self.total_trades_cerrados = 0
        self.trades_ganadores = 0
        self.total_comisiones_pagadas = 0.0

    def marcar_a_mercado(self, evento_mercado):
        self.precio_mercado_actual = evento_mercado.datos_tick['close']
        if self.cooldown_ticks > 0:
            self.cooldown_ticks -= 1
            
        if self.inventario_activo > 0:
            if self.precio_mercado_actual > self.precio_maximo_alcanzado:
                self.precio_maximo_alcanzado = self.precio_mercado_actual

    def _calcular_fraccion_kelly_piie(self, psi_crudo):
        q = 1.0 - self.win_rate_estimado
        kelly_base = (self.win_rate_estimado * self.payoff_ratio - q) / self.payoff_ratio
        psi_norm = max(0.0, min(1.0, psi_crudo / 2.0))
        return max(0.0, (kelly_base * self.multiplicador_kelly) * psi_norm)

    def _evacuar_posicion(self, evento_senal, cola_eventos, razon, ticks_castigo=60, es_ganancia=False):
        print(f"{razon} Evacuando {self.inventario_activo:.4f} unidades.")
        orden_venta = EventoOrden(
            activo=evento_senal.activo, 
            tipo_orden='MARKET', 
            cantidad=-self.inventario_activo, 
            precio_limite=self.precio_mercado_actual
        )
        cola_eventos.put(orden_venta)
        self.cooldown_ticks = ticks_castigo 
        self.inventario_activo = 0.0 
        self.precio_maximo_alcanzado = 0.0 
        
        self.total_trades_cerrados += 1
        if es_ganancia:
            self.trades_ganadores += 1
            
        self.ia.aprender_del_resultado(es_ganancia)

    def dimensionar_y_enrutar(self, evento_senal, cola_eventos):
        if self.cooldown_ticks > 0: return

        if self.inventario_activo > 0 and evento_senal.prob_colapso > 0.85:
            self._evacuar_posicion(evento_senal, cola_eventos, "🦇 RADAR CRÍTICO: Anticipando colapso inminente.", 60, es_ganancia=True)
            return

        if "TRAMPA" in evento_senal.diagnostico_piie or "COLAPSO" in evento_senal.diagnostico_piie:
            if self.inventario_activo > 0:
                self._evacuar_posicion(evento_senal, cola_eventos, "🚨 PÁNICO PIIE:", 60, es_ganancia=False)
            return

        if self.inventario_activo > 0:
            precio_promedio = self.costo_total_inventario / self.inventario_activo
            rendimiento_desde_entrada = (self.precio_mercado_actual - precio_promedio) / precio_promedio
            caida_desde_pico = (self.precio_maximo_alcanzado - self.precio_mercado_actual) / self.precio_maximo_alcanzado
            
            # 🌊 TRAILING STOP AMPLIADO AL 3% (Para surfear velas de 15 minutos sin asustarse)
            if caida_desde_pico > 0.030:
                es_ganancia_real = self.precio_mercado_actual > precio_promedio
                estado = "💰 TRAILING PROFIT" if es_ganancia_real else "🛡️ TRAILING CORTADO"
                self._evacuar_posicion(evento_senal, cola_eventos, f"{estado} (Caída de 3.0% desde pico):", 60, es_ganancia=es_ganancia_real)
                return 

            if rendimiento_desde_entrada < -0.020:
                self._evacuar_posicion(evento_senal, cola_eventos, f"🩸 STOP LOSS HARD ({rendimiento_desde_entrada*100:.2f}%):", 120, es_ganancia=False)
                return

        if "ESTADO DE GRACIA" in evento_senal.diagnostico_piie:
            probabilidad = self.ia.predecir_exito(evento_senal.energia_psi, evento_senal.dI, evento_senal.gamma, evento_senal.prob_colapso)
            
            import random
            es_exploracion = random.random() < 0.02 
            
            if probabilidad < self.ia.umbral and not es_exploracion:
                return

            valor_inventario = self.inventario_activo * self.precio_mercado_actual
            patrimonio_total = self.capital_actual + valor_inventario
            exposicion_actual = valor_inventario / (patrimonio_total + 1e-9)

            if exposicion_actual < 0.50 and self.capital_actual > 10.0:
                fraccion_riesgo = self._calcular_fraccion_kelly_piie(evento_senal.energia_psi)
                if probabilidad < self.ia.umbral:
                    fraccion_riesgo *= 0.10 
                    
                capital_en_riesgo = self.capital_actual * fraccion_riesgo 
                cantidad_orden = capital_en_riesgo / self.precio_mercado_actual 
                
                if cantidad_orden > 0:
                    orden = EventoOrden(
                        activo=evento_senal.activo, tipo_orden='LIMIT', 
                        cantidad=cantidad_orden, precio_limite=self.precio_mercado_actual
                    )
                    cola_eventos.put(orden)

    def registrar_impacto_financiero(self, evento_ejecucion):
        valor_operacion = evento_ejecucion.cantidad * evento_ejecucion.precio_real
        self.capital_actual -= valor_operacion 
        self.capital_actual -= evento_ejecucion.costo_friccion 
        self.total_comisiones_pagadas += evento_ejecucion.costo_friccion
        
        if evento_ejecucion.cantidad > 0:
            self.inventario_activo += evento_ejecucion.cantidad
            self.costo_total_inventario += abs(valor_operacion)
            if self.precio_maximo_alcanzado == 0.0:
                self.precio_maximo_alcanzado = evento_ejecucion.precio_real
        else:
            self.inventario_activo = 0.0
            self.costo_total_inventario = 0.0
            self.precio_maximo_alcanzado = 0.0

    # 🛑 NUEVO: BOTÓN DE LIQUIDACIÓN FINAL
    def liquidacion_forzosa_final(self, comision_exchange=0.001):
        if self.inventario_activo > 0:
            print(f"\n🔔 CAMPANA DE CIERRE: Liquidando inventario final a precio de mercado...")
            
            cantidad_venta = -self.inventario_activo
            # Simulamos un ligero slippage de salida (0.1%)
            precio_ejecucion = self.precio_mercado_actual * 0.999 
            
            valor_operacion = cantidad_venta * precio_ejecucion 
            costo_friccion = abs(valor_operacion) * comision_exchange
            
            precio_promedio = self.costo_total_inventario / self.inventario_activo
            es_ganancia = precio_ejecucion > precio_promedio
            
            self.capital_actual -= valor_operacion 
            self.capital_actual -= costo_friccion 
            
            self.total_comisiones_pagadas += costo_friccion
            self.total_trades_cerrados += 1
            if es_ganancia:
                self.trades_ganadores += 1
                
            self.inventario_activo = 0.0
            self.costo_total_inventario = 0.0
            self.precio_maximo_alcanzado = 0.0
            print(f"💼 Liquidación completada. Capital asegurado en cash: ${self.capital_actual:,.2f}")