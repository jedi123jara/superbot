import os
import pandas as pd
import time
from datetime import datetime

from dotenv import load_dotenv
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit

import config.settings as settings
from indicators.calculator import calcular_todos
from alpaca_client import api as API   # ← una sola instancia compartida
from risk_manager import puede_operar, registrar_trade, inicializar_dia

# ==============================
# CONFIG
# ==============================
load_dotenv()

ACCIONES_VIP = [
    "AAPL","MSFT","GOOGL","AMZN","META","TSLA","NVDA","JPM","V",
    "AMD","AVGO","TSM","MU","INTC","QCOM","TXN",
    "CRM","ADBE","ORCL","NOW",
    "MA","PYPL","COIN","SOFI",
    "WMT","COST","HD",
    "XOM","CVX",
    "JNJ","PFE","UNH",
    "DIS","NFLX",
    "SPY","QQQ"
]

# ==============================
# PARÁMETROS
# ==============================
CAPITAL_BASE = 1000
RIESGO       = 0.10
TP           = 0.03
SL           = 0.003

# ==============================
# MARTINGALA
# ==============================
nivel_martingala = 0
MAX_MARTINGALA   = 2
MULT             = 2


# ==============================
# EJECUTAR ORDEN (TP/SL correcto para CALL y PUT)
# ==============================
def ejecutar_orden(ticker, tipo, capital):
    global nivel_martingala

    try:
        precio = API.get_latest_trade(ticker).price

        riesgo_actual = RIESGO * (MULT ** nivel_martingala)
        monto = capital * riesgo_actual
        qty   = round(monto / precio, 2)

        if qty <= 0:
            print(f"⚠️  Qty inválida para {ticker}")
            return

        side = "buy" if tipo == "CALL" else "sell"

        # TP y SL según dirección de la orden
        if side == "buy":
            tp_price = round(precio * (1 + TP), 2)
            sl_price = round(precio * (1 - SL), 2)
        else:
            # Para short: TP hacia abajo, SL hacia arriba
            tp_price = round(precio * (1 - TP), 2)
            sl_price = round(precio * (1 + SL), 2)

        API.submit_order(
            symbol=ticker,
            qty=qty,
            side=side,
            type="market",
            time_in_force="day",
            order_class="bracket",
            take_profit={"limit_price": tp_price},
            stop_loss={"stop_price": sl_price}
        )

        print(f"✅ {side.upper()} {ticker} | qty={qty} | TP={tp_price} | SL={sl_price} | M={nivel_martingala}")

    except Exception as e:
        print(f"❌ Error orden {ticker}: {e}")


# ==============================
# ESTRATEGIA PRINCIPAL
# ==============================
def ejecutar_estrategia():
    print(f"\n📊 Escaneando mercado... {datetime.now().strftime('%H:%M:%S')}")

    # Control de riesgo global (límite trades, drawdown máximo, posiciones)
    if not puede_operar():
        return

    tf = TimeFrame(5, TimeFrameUnit.Minute)

    # Una sola llamada de posiciones para todo el loop
    try:
        posiciones_set = {p.symbol for p in API.list_positions()}
    except Exception as e:
        print(f"❌ Error obteniendo posiciones: {e}")
        return

    for ticker in ACCIONES_VIP:
        try:
            barras = API.get_bars(ticker, tf, limit=200).df

            if barras.empty:
                continue

            df = pd.DataFrame({
                'timestamp': barras.index,
                'open':      barras['open'],
                'high':      barras['high'],
                'low':       barras['low'],
                'close':     barras['close'],
                'volume':    barras['volume'],
            })

            # Compatibilidad con calcular_todos (espera columnas capitalizadas)
            df['Open']   = df['open']
            df['High']   = df['high']
            df['Low']    = df['low']
            df['Close']  = df['close']
            df['Volume'] = df['volume']

            # Settings por ticker
            settings.PAR             = ticker
            settings.RSI_UMBRAL_CALL = 65
            settings.RSI_UMBRAL_PUT  = 32
            settings.VOL_MINIMO      = 1.2
            settings.FILTRO_HORARIO  = False

            df_ind = calcular_todos(df)
            ultima = df_ind.iloc[-1]
            rsi    = ultima.get("rsi", 50)

            if ticker in posiciones_set:
                continue

            if rsi > 65:
                print(f"📈 CALL {ticker} | RSI={rsi:.2f}")
                ejecutar_orden(ticker, "CALL", CAPITAL_BASE)
                registrar_trade()  # contador de riesgo diario

            elif rsi < 32:
                print(f"📉 PUT {ticker} | RSI={rsi:.2f}")
                ejecutar_orden(ticker, "PUT", CAPITAL_BASE)
                registrar_trade()  # contador de riesgo diario

        except Exception as e:
            print(f"❌ Error en {ticker}: {e}")


# ==============================
# CONTROL MARTINGALA (lógica real basada en PnL)
# ==============================
def actualizar_martingala():
    global nivel_martingala

    try:
        posiciones = API.list_positions()

        if not posiciones:
            nivel_martingala = 0
            print("🎯 Martingala reseteada (sin posiciones abiertas)")
            return

        ganadoras  = sum(1 for p in posiciones if float(p.unrealized_pl) >= 0)
        perdedoras = sum(1 for p in posiciones if float(p.unrealized_pl) <  0)

        if ganadoras >= perdedoras:
            # Mayoría o empate en ganadores → resetear
            nivel_martingala = 0
        elif nivel_martingala < MAX_MARTINGALA:
            # Mayoría perdedora → subir nivel
            nivel_martingala += 1

        print(f"🎯 Martingala: nivel={nivel_martingala} | ✅ {ganadoras} | ❌ {perdedoras}")

    except Exception as e:
        print(f"❌ Error actualizando martingala: {e}")


# ==============================
# INTERFAZ PARA FASTAPI (main.py)
# ==============================
class BacktestBot:
    """Wrapper para que main.py (FastAPI) pueda llamar a bot_instance.run()."""

    def run(self):
        """Ejecuta un ciclo completo de la estrategia y retorna resumen."""
        ejecutar_estrategia()
        actualizar_martingala()
        return {
            "ciclo":           "completado",
            "timestamp":       datetime.now().isoformat(),
            "nivel_martingala": nivel_martingala,
        }


# ==============================
# LOOP STANDALONE
# ==============================
def loop():
    print("=" * 70)
    print("🚀 BOT PAPER TRADING — MODO STANDALONE")
    print("=" * 70)

    inicializar_dia()  # establece capital base para calcular drawdown del día

    while True:
        try:
            ejecutar_estrategia()
            actualizar_martingala()
            print(f"\n⏳ Próximo ciclo en 5 minutos...\n")
            time.sleep(300)

        except KeyboardInterrupt:
            print("\n🛑 Bot detenido por el usuario.")
            break
        except Exception as e:
            print(f"❌ ERROR GLOBAL: {e}")
            time.sleep(60)


if __name__ == "__main__":
    loop()