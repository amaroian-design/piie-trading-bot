import time
import traceback
from core.motor import motor_dirigido_por_eventos
from modulos.data_live import DatafeedBybitRealtime
from modulos.piie import EstrategiaPIIE
from modulos.riesgo import GestorRiesgoInstitucional
from modulos.exchange import EmuladorExchange

def iniciar_paper_trading_nube():
    print("🔥 SISTEMA PIIE-AMEC: MODO PRODUCCIÓN (NUBE) ACTIVADO 🔥")
    
    # 1. Instanciamos el cerebro y el gestor AFUERA del bucle de reconexión.
    # Así, si se cae el internet, la IA no pierde su memoria y el gestor no pierde tu dinero.
    estrategia = EstrategiaPIIE(sensibilidad_kappa=3.0, ventana=60, ventana_calibracion=300)
    gestor_riesgo = GestorRiesgoInstitucional(capital_inicial=100000.0)
    emulador = EmuladorExchange(latencia_ms=50, comision_base=0.001)

    # 🛡️ EL ESCUDO DE INMORTALIDAD
    while True:
        try:
            print("\n⚡ CONECTANDO CABLES AL SERVIDOR DE BYBIT (EUROPA)...")
            datafeed = DatafeedBybitRealtime(simbolo="BTC/USDT", temporalidad="15m")
            
            # El motor arranca. Si todo va bien, se quedará bloqueado aquí funcionando por meses.
            motor_dirigido_por_eventos(datafeed, estrategia, gestor_riesgo, emulador)
            
        except KeyboardInterrupt:
            # Si tú lo apagas manualmente (Ctrl+C en tu PC)
            print("\n🛑 DETECCIÓN DE PARADA MANUAL.")
            gestor_riesgo.liquidacion_forzosa_final()
            print("Saliendo del mercado de forma segura. ¡Buen trabajo, Arquitecto!")
            break
            
        except Exception as e:
            # Si ocurre CUALQUIER error (WiFi, Binance caído, etc.)
            print(f"\n⚠️ ALERTA CRÍTICA DE RED: Se ha perdido la conexión con el exchange.")
            print(f"Detalle técnico: {e}")
            print("🛡️ El Escudo está activo. El inventario y el capital están a salvo en la memoria local.")
            print("🔄 Iniciando protocolo de reconexión en 30 segundos...")
            time.sleep(30)
            # Al terminar los 30 segundos, el 'while True' volverá a intentar conectar.

if __name__ == "__main__":
    iniciar_paper_trading_nube()
