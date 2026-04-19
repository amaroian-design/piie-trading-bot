import ccxt
import time
import pandas as pd
from core.eventos import EventoMercado

class DatafeedBybitRealtime: # 🔄 Renombrado para ser honestos
    def __init__(self, simbolo="BTC/USDT", temporalidad="15m"):
        # Forzamos Bybit
        self.exchange = ccxt.bybit() 
        self.simbolo = simbolo
        self.temporalidad = temporalidad
        self.ultima_vela_timestamp = None

    def bombear_primer_tick(self, cola_eventos):
        print(f"📡 Sincronizando memoria histórica de Bybit ({self.simbolo})...")
        # Bybit a veces prefiere 'BTCUSDT' (sin la barra), CCXT suele manejarlo, 
        # pero si falla, probaremos quitando la barra.
        ohlcv = self.exchange.fetch_ohlcv(self.simbolo, self.temporalidad, limit=100)
        df = self._convertir_a_df(ohlcv)
        
        for i in range(len(df)):
            tick = df.iloc[i]
            evento = EventoMercado(datos_tick=tick, timestamp=tick.name)
            cola_eventos.put(evento)
        
        self.ultima_vela_timestamp = df.index[-1]
        print("✅ Memoria de Bybit lista. Esperando vela en vivo...")

    def bombear_siguiente_tick(self, cola_eventos):
        """Se bloquea hasta que aparece una nueva vela cerrada en el exchange."""
        while True:
            try:
                # Consultamos la última vela terminada
                ohlcv = self.exchange.fetch_ohlcv(self.simbolo, self.temporalidad, limit=2)
                df = self._convertir_a_df(ohlcv)
                nueva_vela = df.iloc[-1]

                if nueva_vela.name > self.ultima_vela_timestamp:
                    print(f"🔔 NUEVA VELA DETECTADA: {nueva_vela.name} | Close: {nueva_vela['close']}")
                    evento = EventoMercado(datos_tick=nueva_vela, timestamp=nueva_vela.name)
                    cola_eventos.put(evento)
                    self.ultima_vela_timestamp = nueva_vela.name
                    break
                
                # Esperamos 10 segundos antes de volver a preguntar (para no saturar la API)
                time.sleep(10)
            except Exception as e:
                print(f"⚠️ Error de conexión: {e}. Reintentando...")
                time.sleep(30)

    def _convertir_a_df(self, ohlcv):
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df

    def hay_mas_datos(self):
        return True # En tiempo real, el mercado nunca duerme
