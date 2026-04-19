import numpy as np

class OraculoAI:
    def __init__(self, umbral_confianza=0.60, tasa_aprendizaje=0.01):
        self.umbral = umbral_confianza
        self.lr = tasa_aprendizaje
        
        # 🧠 AHORA SON 5 PESOS: [Psi, dI, Gamma, Prob_Colapso, Bias]
        # El peso inicial de Prob_Colapso es negativo (-0.5), si hay mucho riesgo, la IA se asusta.
        self.pesos = np.array([0.1, 0.1, -0.1, -0.5, 1.0]) 
        
        self.ultima_prediccion = 0
        self.ultimos_features = None

    def _activacion_sigmoide(self, x):
        x = np.clip(x, -500, 500)
        return 1 / (1 + np.exp(-x))

    # Añadimos prob_colapso a los parámetros
    def predecir_exito(self, psi, dI, gamma, prob_colapso):
        features = np.array([
            min(psi / 10.0, 1.0),   
            np.sign(dI),            
            min(gamma * 100, 1.0),
            prob_colapso,           # 🦇 Sensor de caída
            1.0                     
        ])
        
        suma = np.dot(features, self.pesos)
        probabilidad = self._activacion_sigmoide(suma)
        
        self.ultimos_features = features
        self.ultima_prediccion = probabilidad
        
        return probabilidad

    def aprender_del_resultado(self, es_ganancia):
        if self.ultimos_features is None: return
        target = 1.0 if es_ganancia else 0.0
        error = target - self.ultima_prediccion
        ajuste = self.lr * error * self.ultima_prediccion * (1 - self.ultima_prediccion)
        self.pesos += ajuste * self.ultimos_features
        # Opcional: print para debug