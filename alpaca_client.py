import os
from dotenv import load_dotenv
from alpaca_trade_api.rest import REST

load_dotenv()  # carga .env antes de leer las keys

# ==============================
# CONEXIÓN ALPACA (PAPER)
# ==============================
api = REST(
    os.getenv("ALPACA_API_KEY"),
    os.getenv("ALPACA_SECRET_KEY"),
    "https://paper-api.alpaca.markets",
    api_version="v2"
)

# ==============================
# VERIFICAR POSICIÓN ABIERTA
# ==============================
def hay_posicion_abierta(ticker):
    try:
        posiciones = api.list_positions()
        return any(p.symbol == ticker for p in posiciones)
    except Exception as e:
        print(f"❌ Error posiciones: {e}")
        return False

# ==============================
# OBTENER CAPITAL DISPONIBLE
# ==============================
def obtener_capital():
    try:
        account = api.get_account()
        return float(account.cash)
    except Exception as e:
        print(f"❌ Error capital: {e}")
        return 0

# ==============================
# CALCULAR CANTIDAD
# ==============================
def calcular_qty(capital, precio):
    try:
        qty = capital / precio
        return round(qty, 2)
    except:
        return 0

# ==============================
# EJECUTAR ORDEN (CON TP/SL)
# ==============================
def ejecutar_orden(ticker, tipo, capital, tp=0.03, sl=0.003):

    try:
        # ==============================
        # PRECIO ACTUAL
        # ==============================
        trade = api.get_latest_trade(ticker)
        precio = trade.price

        # ==============================
        # VALIDAR CAPITAL
        # ==============================
        capital_disponible = obtener_capital()

        if capital_disponible <= 0:
            print("❌ Sin capital")
            return

        if capital > capital_disponible:
            capital = capital_disponible * 0.95  # margen seguridad

        # ==============================
        # CANTIDAD
        # ==============================
        qty = calcular_qty(capital, precio)

        if qty <= 0:
            print(f"⚠️ Qty inválida {ticker}")
            return

        # ==============================
        # DIRECCIÓN
        # ==============================
        side = "buy" if tipo == "CALL" else "sell"

        # ==============================
        # PRECIOS TP / SL
        # ==============================
        if side == "buy":
            tp_price = precio * (1 + tp)
            sl_price = precio * (1 - sl)
        else:
            tp_price = precio * (1 - tp)
            sl_price = precio * (1 + sl)

        # ==============================
        # ORDEN BRACKET (CLAVE)
        # ==============================
        order = api.submit_order(
            symbol=ticker,
            qty=qty,
            side=side,
            type="market",
            time_in_force="day",
            order_class="bracket",
            take_profit={"limit_price": round(tp_price, 2)},
            stop_loss={"stop_price": round(sl_price, 2)}
        )

        print(f"""
✅ ORDEN EJECUTADA
Ticker: {ticker}
Tipo: {tipo}
Qty: {qty}
Precio: {precio:.2f}
TP: {tp_price:.2f}
SL: {sl_price:.2f}
""")

    except Exception as e:
        print(f"❌ Error ejecutando orden {ticker}: {e}")

# ==============================
# CERRAR POSICIÓN (MANUAL)
# ==============================
def cerrar_posicion(ticker):
    try:
        api.close_position(ticker)
        print(f"🔴 Posición cerrada: {ticker}")
    except Exception as e:
        print(f"❌ Error cerrando {ticker}: {e}")

# ==============================
# LISTAR POSICIONES
# ==============================
def listar_posiciones():
    try:
        posiciones = api.list_positions()
        return [
            {
                "ticker": p.symbol,
                "qty": p.qty,
                "pnl": p.unrealized_pl,
                "precio": p.current_price
            }
            for p in posiciones
        ]
    except Exception as e:
        print(f"❌ Error listando posiciones: {e}")
        return []

# ==============================
# CANCELAR ÓRDENES
# ==============================
def cancelar_ordenes():
    try:
        api.cancel_all_orders()
        print("🧹 Órdenes canceladas")
    except Exception as e:
        print(f"❌ Error cancelando órdenes: {e}")