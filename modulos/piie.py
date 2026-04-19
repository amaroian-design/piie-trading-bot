import numpy as np
import pandas as pd
from core.eventos import EventoSeñal

class EstrategiaPIIE:
    def __init__(self, sensibilidad_kappa=3.0, ventana=60, ventana_calibracion=180):
        # ⚠️ Aumentamos las ventanas por defecto. 
        # Si usas datos de 1 minuto: 60 = 1 hora de memoria, 180 = 3 horas de calibración
        self.kappa = sensibilidad_kappa
        self.ventana = ventana
        self.ventana_calibracion = ventana_calibracion
        
        self.historial_precios = []
        self.historial_retornos = []
        self.historial_informacion = []

    def _shannon_entropy(self, serie):
        serie = np.array(serie)
        if len(serie) == 0 or np.sum(np.abs(serie)) == 0:
            return 0
        probs = np.abs(serie) / np.sum(np.abs(serie))
        return -np.sum([p * np.log2(p) for p in probs if p > 0])

    def evaluar_entropia(self, evento_mercado, cola_eventos):
        precio_actual = evento_mercado.datos_tick['close']
        self.historial_precios.append(precio_actual)
        
        if len(self.historial_precios) < 2: return

        retorno = (self.historial_precios[-1] - self.historial_precios[-2]) / self.historial_precios[-2]
        self.historial_retornos.append(retorno)

        if len(self.historial_retornos) < self.ventana: return
            
        ventana_retornos = self.historial_retornos[-self.ventana:]
        info_t = self._shannon_entropy(ventana_retornos)
        self.historial_informacion.append(info_t)

        if len(self.historial_informacion) < self.ventana_calibracion + 1: return

        # 🧠 FILTRO DE RUIDO INSTITUCIONAL (SMOOTHING)
        # Calculamos la derivada, pero usamos Pandas para sacarle una EMA (Media Móvil Exponencial)
        # Esto elimina los "falsos positivos" de colapso
        gradientes_crudos = np.diff(self.historial_informacion)
        gradientes_suavizados = pd.Series(gradientes_crudos).ewm(span=10, adjust=False).mean().values
        
        dI_actual = gradientes_suavizados[-1]
        
        gradientes_ventana = gradientes_suavizados[-self.ventana_calibracion:]
        mu_gradiente = np.mean(gradientes_ventana)
        sigma_gradiente = np.std(gradientes_ventana)
        
        # Umbral dinámico
        tau_actual = mu_gradiente - (self.kappa * sigma_gradiente)
        
        volatilidad_std = np.std(ventana_retornos)
        gamma = abs(volatilidad_std - np.std(self.historial_retornos[-(self.ventana+1):-1]))
        
        # --- 🦇 RADAR DE RIESGO DE COLA (Probabilidad de Colapso) ---
        retornos_negativos = [r for r in ventana_retornos if r < 0]
        retornos_positivos = [r for r in ventana_retornos if r > 0]
        
        vol_down = np.std(retornos_negativos) if len(retornos_negativos) > 2 else 1e-9
        vol_up = np.std(retornos_positivos) if len(retornos_positivos) > 2 else 1e-9
        
        # Ratio de asimetría: Si vol_down es mucho mayor que vol_up, hay ventas institucionales ocultas
        riesgo_cola = vol_down / (vol_up + 1e-9)
        # Función sigmoide para convertir el riesgo en probabilidad (0.0 a 1.0)
        prob_colapso_actual = 1 / (1 + np.exp(-(riesgo_cola - 2.0))) 
        # -------------------------------------------------------------

        psi_bruto = (info_t + dI_actual) / (gamma + 1e-9)
        psi_actual = max(0.0, min(10.0, psi_bruto)) 

        precio_subiendo = retorno > 0
        
        # Modifica la emisión de señales para incluir el nuevo sensor
        if precio_subiendo and (dI_actual < tau_actual):
            diagnostico = f"🚨 TRAMPA DETECTADA: Fuga extrema de bits ({dI_actual:.4f} < {tau_actual:.4f})"
            senal = EventoSeñal("BTC", diagnostico, 0.0, dI_actual, gamma, prob_colapso_actual)
            cola_eventos.put(senal)
            
        elif psi_actual > 2.0:
            diagnostico = "💎 ESTADO DE GRACIA: Alta Energía Informacional"
            senal = EventoSeñal("BTC", diagnostico, psi_actual, dI_actual, gamma, prob_colapso_actual)
            cola_eventos.put(senal)
        