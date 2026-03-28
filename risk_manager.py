import threading
from alpaca_client import api

# ==============================
# CONFIGURACIÓN DE RIESGO
# ==============================
MAX_DRAWDOWN_DIA = -0.05   # -5% diario
MAX_TRADES_DIA = 20
MAX_POSICIONES = 5

trades_hoy = 0
capital_inicio_dia = None
_lock = threading.Lock()  # protege trades_hoy en entornos multi-thread


# ==============================
# CAPITAL ACTUAL
# ==============================
def obtener_equity():
    account = api.get_account()
    return float(account.equity)


# ==============================
# INICIO DE DÍA
# ==============================
def inicializar_dia():
    global capital_inicio_dia
    capital_inicio_dia = obtener_equity()


# ==============================
# CONTROL DRAWDOWN
# ==============================
def drawdown_actual():
    equity = obtener_equity()
    if capital_inicio_dia is None:
        return 0
    return (equity - capital_inicio_dia) / capital_inicio_dia


# ==============================
# BLOQUEAR TRADING
# ==============================
def puede_operar():

    with _lock:
        # limitar trades
        if trades_hoy >= MAX_TRADES_DIA:
            print("⛔ Límite de trades alcanzado")
            return False

    # limitar drawdown
    dd = drawdown_actual()
    if dd <= MAX_DRAWDOWN_DIA:
        print(f"⛔ Drawdown máximo alcanzado: {dd:.2%}")
        return False

    # limitar posiciones abiertas
    posiciones = api.list_positions()
    if len(posiciones) >= MAX_POSICIONES:
        print("⛔ Demasiadas posiciones abiertas")
        return False

    return True


# ==============================
# REGISTRAR TRADE
# ==============================
def registrar_trade():
    global trades_hoy
    with _lock:
        trades_hoy += 1