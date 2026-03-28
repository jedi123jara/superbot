import os
import pandas as pd
import time
from datetime import datetime, time as dtime
import pytz

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
    # Los 10 Titanes (Indispensables)
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "BRK.B", "JPM", "V",
    # Semiconductores (Tu zona de mayor profit)
    "AMD", "AVGO", "TSM", "MU", "INTC", "QCOM", "TXN", "AMAT", "LRCX", "ADI",
    # Ciberseguridad y Cloud
    "PANW", "CRWD", "FTNT", "OKTA", "ZS", "DDOG", "NET", "SNOW", "PLTR",
    # Software e IA
    "CRM", "ADBE", "ORCL", "SAP", "NOW", "WDAY", "TEAM", "ADSK", "PLTR", "IBM",
    # Fintech y Pagos
    "MA", "PYPL", "SQ", "COIN", "HOOD", "AFRM", "SOFI", "SHOP", "SPOT", "MELI",
    # Consumo y Retail
    "WMT", "COST", "TGT", "HD", "LOW", "NKE", "SBUX", "MCD", "PEP", "KO",
    # Energía y Materiales
    "XOM", "CVX", "OXY", "SLB", "COP", "FCX", "NUE", "AA", "NEM", "GOLD",
    # Salud y Biotech
    "JNJ", "PFE", "MRNA", "UNH", "ABT", "LLY", "ABBV", "BMY", "GILD", "AMGN",
    # Entretenimiento y Comunicaciones
    "DIS", "NFLX", "TMUS", "VZ", "T", "CMCSA", "PARA", "WBD", "ROKU", "UBER",
    # ETFs (Para suavizar la curva de capital)
    "SPY", "QQQ", "IWM", "DIA", "SMH", "SOXX", "XLF", "XLV", "XLE", "ARKK",
    # Industriales y Aeroespacial (Movimientos pesados y claros)
    "GE", "HON", "MMM", "UNP", "UPS", "FDX", "DE", "CAT", "LMT", "GD", 
    "NOC", "RTX", "BA", "EMR", "ETN", "ITW", "PH", "AME", "DOV", "XYL",
    
    # Consumo Discrecional y Retail (Volatilidad por reportes)
    "SBUX", "NKE", "TGT", "TJX", "ROST", "MAR", "HLT", "BKNG", "EXPE", "LULU",
    "ULTA", "BBY", "LOW", "TSCO", "ORLY", "AZO", "GME", "AMC", "EBAY", "ETSY",
    
    # Finanzas y Bancos Regionales (Sensibles a tasas)
    "BAC", "GS", "MS", "C", "BLK", "TROW", "SCHW", "PNC", "USB", "CMA",
    "FITB", "HBAN", "KEY", "RF", "ZION", "TFC", "SYF", "DFS", "AXP", "COF",
    
    # Energía, Minería y Materiales (Ciclos de RSI muy marcados)
    "SLB", "HAL", "MPC", "PSX", "VLO", "HES", "DVN", "FANG", "MRO", "APA",
    "FCX", "NEM", "NUE", "STLD", "RS", "CLF", "X", "AA", "CENX", "VALE",
    
    # Salud, Pharma y Biotech (Mid-Cap)
    "CVS", "CI", "HUM", "HCA", "SYK", "ZTS", "IDXX", "IQV", "EW", "BSX",
    "MDT", "ISRG", "DXCM", "ALGN", "VRTX", "REGN", "BIIB", "ILMN", "TMO", "A",
    # Bienes Raíces / REITs (Dividendos y Ciclos Claros)
    "O", "SPG", "PLD", "AMT", "CCI", "EQIX", "DLR", "PSA", "WY", "AVB", 
    "EQR", "CPT", "MAA", "ESS", "UDR", "SUI", "ELS", "INVH", "AMH", "VICI",
    
    # Servicios Públicos / Utilities (Seguridad y Rebotes de RSI)
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "XEL", "ED", "PEG", "WEC", 
    "ES", "AWK", "EIX", "ETR", "FE", "PPL", "AEE", "CMS", "CNP", "LNT",
    
    # Consumo Básico (Defensivas para el interés compuesto)
    "K", "GIS", "CAG", "SJM", "CPB", "HRL", "TSN", "TAP", "KR", "SFM", 
    "WBA", "CHD", "CLX", "HSY", "MKC", "ADM", "STZ", "MNST", "KMB", "EL",
    
    # Transporte, Logística y Automotriz
    "NSC", "CSX", "FDX", "UPS", "JBHT", "ODFL", "KNX", "SNDR", "ARCB", "SAIA",
    "F", "GM", "STLA", "RIVN", "LCID", "HMC", "TM", "PCAR", "ALSN", "TEX",
    
    # Materiales, Construcción y Químicos
    "SHW", "PPG", "APD", "LIN", "ECL", "VMC", "MLM", "DHI", "LEN", "PHM",
    "NVR", "TOL", "KBH", "MTH", "MDC", "TMHC", "GRBK", "LGIH", "CCS", "WLK",
    # Lujo y Estilo de Vida (Alta volatilidad, rebotes técnicos)
    "LVMUY", "RMSFY", "ORLY", "RL", "CPRI", "TPR", "EL", "TIF", "SIG", "VFC",
    "ONON", "SKX", "DECK", "PINS", "SNAP", "EBAY", "ETSY", "CHWY", "RVLV", "U",
    
    # Tecnología Emergente e Inteligencia Artificial
    "AI", "PLTR", "SNOW", "PATH", "C3AI", "SOUN", "BBAI", "RGTI", "IONQ", "GWRE",
    "SENT", "SPLK", "DT", "ESTC", "MDB", "DDOG", "OKTA", "ZS", "CRWD", "PANW",
    
    # Servicios Financieros y Fintech (Movimientos rápidos)
    "HOOD", "SOFI", "AFRM", "UPST", "LC", "MQ", "NU", "PAGS", "STONE", "MELI",
    "SE", "TME", "BILI", "IQ", "PDD", "JD", "BABA", "TCEHY", "NTES", "DIDY",
    
    # Hospitalidad, Viajes y Casinos
    "ABNB", "BKNG", "EXPE", "TRIP", "TCOM", "HLT", "MAR", "H", "WH", "CHH",
    "MGM", "WYNN", "LVS", "PENN", "CZR", "DKNG", "RCL", "CCL", "NCLH", "DAL",
    
    # Gaming, Medios y Entretenimiento
    "RBLX", "EA", "TTWO", "MTCH", "BMBL", "SPOT", "NFLX", "DIS", "WBD", "PARA",
    "LYV", "SIRI", "AMC", "CNK", "IMAX", "NYT", "NWSA", "FOXA", "WMG", "SONY",
    # Biotecnología y Farmacéuticas (Volatilidad pura)
    "VRTX", "REGN", "BIIB", "ILMN", "SGEN", "ALNY", "BMRN", "SRPT", "INSM", "HALO",
    "RNA", "CRSP", "NTLA", "EDIT", "BEAM", "PACB", "EXAS", "NVAX", "CVAC", "BHC",
    
    # Seguros y Servicios Financieros (Estables y técnicos)
    "AFL", "ALL", "TRV", "PGR", "CB", "CINF", "HIG", "LNC", "PFG", "GL",
    "AIZ", "RE", "RGA", "UNM", "AIG", "BHF", "CRBG", "EQH", "VOYA", "L",
    
    # Hardware, Almacenamiento y Periféricos
    "STX", "WDC", "HPQ", "HPE", "NTAP", "PSTG", "WOLF", "RMBS", "LSCC", "SLAB",
    "CRUS", "SYNA", "DIOD", "POWI", "FORM", "ACLS", "AEHR", "TER", "ENTG", "MKSI",
    
    # Hospitales y Servicios de Salud
    "HCA", "THC", "UHS", "CYH", "ACHC", "SEM", "EHC", "AMN", "CHH", "ENSG",
    "DVA", "CNC", "MOH", "OSCR", "ALHC", "CLOV", "BHG", "AMED", "OPCH", "AGL",
    
    # Química Especializada y Fertilizantes
    "CF", "MOS", "NTR", "ICL", "SMG", "AVNT", "HUN", "OLN", "CC", "NEU",
    "ASH", "KRO", "FMC", "CTVA", "ALB", "LTHM", "SQM", "SGML", "LAC", "MP",
    # Infraestructura y Construcción de Maquinaria
    "CAT", "DE", "PCAR", "CMI", "TEX", "OSK", "ALSN", "AGCO", "FLS", "ITT",
    "IR", "PNR", "AOS", "XYL", "NDSN", "DOV", "AME", "ROK", "EMR", "ETN",
    
    # Retail Especializado y Ropa (Movimientos estacionales fuertes)
    "GPS", "ANF", "AEO", "URBN", "JWN", "M", "KSS", "DDS", "BURL", "DG",
    "DLTR", "FIVE", "PLNT", "BOOT", "YETI", "SKX", "DECK", "ONON", "CROX", "NKE",
    
    # Servicios Profesionales y Consultoría
    "ACN", "CTSH", "INFY", "WIT", "EPAM", "GLOB", "G", "BAH", "CACI", "SAIC",
    "LDOS", "LEIDOS", "KBR", "ACM", "AECOM", "TTEK", "VRSK", "EFX", "TRU", "SPGI",
    
    # Semiconductores de Nicho y Electrónica
    "WOLF", "RMBS", "LSCC", "SLAB", "CRUS", "SYNA", "DIOD", "POWI", "FORM", "ACLS",
    "AEHR", "KLAC", "LRCX", "AMAT", "TER", "ENTG", "MKSI", "COHR", "ONTO", "CAMT",
    
    # Consumo de Alimentos y Bebidas (Nuevos Tickers)
    "CAVA", "SG", "LOCO", "SHAK", "WEN", "QSR", "DPZ", "PZZA", "TXRH", "BLMN",
    "DENN", "DIN", "CAKE", "PLAY", "EAT", "DRI", "CELH", "MNST", "KDP", "STZ",
    # Software como Servicio (SaaS) y Cloud (Alta volatilidad)
    "DOCN", "DBX", "BOX", "ZEN", "NEWR", "PD", "DT", "ESTC", "MNDY", "ASAN",
    "SMAR", "PATH", "SNOW", "PLTR", "DDOG", "OKTA", "ZS", "CRWD", "PANW", "FTNT",
    
    # Hardware de Redes y Telecomunicaciones
    "CSCO", "JNPR", "ANET", "FFIV", "AKAM", "NET", "FSLY", "CIEN", "LITE", "VIAV",
    "EXTR", "ADTN", "CALX", "MSI", "STNE", "PAGS", "MELI", "SE", "TME", "BILI",
    
    # Datos, Análisis y Consultoría Tecnológica
    "MCO", "SPGI", "MSCI", "INFO", "EPAM", "GLOB", "G", "ACN", "CTSH", "INFY",
    "WIT", "TCS", "CDW", "STX", "WDC", "HPQ", "HPE", "NTAP", "PSTG", "PURE",
    
    # Química Industrial y Materiales de Construcción
    "LIN", "APD", "ECL", "SHW", "PPG", "VMC", "MLM", "DHI", "LEN", "PHM",
    "NVR", "TOL", "KBH", "MTH", "MDC", "TMHC", "GRBK", "LGIH", "CCS", "WLK",
    
    # Farmacéuticas de Crecimiento y Salud
    "VRTX", "REGN", "BIIB", "ILMN", "IDXX", "IQV", "EW", "BSX", "MDT", "ISRG",
    "DXCM", "ALGN", "ZTS", "HCA", "THC", "UHS", "CYH", "ACHC", "SEM", "EHC",
    # Energía y Servicios de Campo Petrolero (Alta volatilidad técnica)
    "BKR", "HAL", "SLB", "OVV", "MRO", "HES", "DVN", "FANG", "CTRA", "EQT",
    "TRGP", "WMB", "OKE", "KMI", "ET", "MPLX", "PAA", "PAGP", "AM", "CHRD",
    
    # Semiconductores de Equipo y Manufactura (Técnicos y precisos)
    "ASML", "LRCX", "AMAT", "KLAC", "TER", "ONTW", "MKSI", "ENTG", "COHR", "CAMT",
    "UCTT", "ICHR", "AEHR", "ACLS", "FORM", "POWI", "DIOD", "SYNA", "CRUS", "SLAB",
    
    # Consumo Masivo, Alimentos y Bebidas
    "MDLZ", "KDP", "STZ", "MNST", "KMB", "HSY", "CLX", "GIS", "K", "STT",
    "ADM", "SYY", "SYCO", "USFD", "PFGC", "CORE", "UNFI", "SFM", "KR", "WBA",
    
    # Transporte Marítimo, Ferroviario y Logística
    "UNP", "CSX", "NSC", "CP", "CNI", "KSU", "FDX", "UPS", "EXPD", "CHRW",
    "JBHT", "ODFL", "KNX", "SNDR", "ARCB", "SAIA", "ZIM", "SBLK", "GNK", "EGLE",
    
    # Hardware, Redes y Servicios IT Especializados
    "IBM", "ORCL", "CSCO", "JNPR", "ANET", "FFIV", "AKAM", "NET", "FSLY", "CIEN",
    "LITE", "VIAV", "EXTR", "ADTN", "CALX", "MSI", "TEL", "APH", "GLW", "STX",
    # Defensa y Aeroespacial (Contratos de largo plazo, RSI estable)
    "LMT", "RTX", "GD", "NOC", "HII", "LHX", "LDOS", "BAH", "CACI", "SAIC",
    "KTOS", "SPCE", "RKLB", "ASTS", "PL", "LUNR", "LLAP", "TDY", "TXT", "WWD",
    
    # Ciberseguridad y Protección de Datos (Alta volatilidad)
    "PANW", "CRWD", "FTNT", "OKTA", "ZS", "DDOG", "NET", "SNOW", "PLTR", "S",
    "CYBR", "CHKP", "TENB", "VRNS", "QLYS", "RAPT", "GEN", "QLYS", "RDWR", "AKAM",
    
    # Semiconductores de Potencia y Análogos
    "WOLF", "RMBS", "LSCC", "SLAB", "CRUS", "SYNA", "DIOD", "POWI", "FORM", "ACLS",
    "AEHR", "KLAC", "LRCX", "AMAT", "TER", "ENTG", "MKSI", "COHR", "ONTO", "CAMT",
    
    # Servicios Financieros Digitales y Exchanges
    "ICE", "CBOE", "NDAQ", "CME", "MKTX", "MSCI", "SPGI", "INFO", "COIN", "HOOD",
    "SOFI", "AFRM", "UPST", "LC", "MQ", "NU", "PAGS", "STONE", "MELI", "SE",
    
    # Hardware de Almacenamiento y Redes Enterprise
    "STX", "WDC", "HPQ", "HPE", "NTAP", "PSTG", "PURE", "ANET", "CSCO", "JNPR",
    "FFIV", "FSLY", "CIEN", "LITE", "VIAV", "EXTR", "ADTN", "CALX", "MSI", "TEL",
    # Especialidades Médicas y Diagnóstico
    "IDXX", "IQV", "A", "MTD", "WAT", "RVTY", "DGX", "LH", "CRL", "BIO",
    "TECH", "WST", "STE", "TFX", "ZBH", "SYK", "BSX", "EW", "MDT", "ISRG",
    
    # Retail de Descuento y Consumo Defensivo
    "DLTR", "DG", "FIVE", "BURL", "TJX", "ROST", "M", "JWN", "KSS", "AEO",
    "ANF", "GPS", "URBN", "ULTA", "EL", "CLX", "CHD", "KMB", "HSY", "MKC",
    
    # Construcción, Materiales y Maquinaria Pesada
    "VMC", "MLM", "EXP", "SUM", "CRH", "NUE", "STLD", "RS", "CLF", "X",
    "AA", "CENX", "FCX", "NEM", "GOLD", "AEM", "FNV", "WPM", "PAAS", "MAG",
    
    # Servicios de Infraestructura y Energía Especializada
    "PWR", "EME", "MTZ", "ACM", "AECOM", "TTEK", "VRSK", "EFX", "TRU", "SPGI",
    "MCO", "NDAQ", "CBOE", "ICE", "CME", "MKTX", "FDS", "MSCI", "JKHY", "FISV",
    
    # Automotriz Especializada y Componentes
    "APTV", "BWA", "ALV", "LEA", "MGA", "GT", "TEL", "APH", "GLW", "STX",
    "WDC", "HPQ", "HPE", "NTAP", "PSTG", "PURE", "ANET", "CSCO", "JNPR", "FFIV"
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

ET = pytz.timezone("America/New_York")


# ==============================
# FILTRO DE HORARIO (Wall Street)
# ==============================
def mercado_abierto():
    """
    Wall Street abre Lun-Vie 9:30am - 4:00pm ET.
    Dejamos de operar a las 3:50pm para evitar \u00f3rdenes en el cierre.
    """
    ahora = datetime.now(ET)

    # Fin de semana
    if ahora.weekday() >= 5:  # 5=S\u00e1bado, 6=Domingo
        return False

    hora = ahora.time()
    apertura = dtime(9, 30)
    cierre   = dtime(15, 50)   # 10 min antes del cierre oficial

    return apertura <= hora <= cierre


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
    ahora_et = datetime.now(ET).strftime('%H:%M:%S ET')
    print(f"\n⏰ {ahora_et} | Verificando mercado...")

    # Filtro de horario: solo operar cuando Wall Street está abierto
    if not mercado_abierto():
        ahora_et_full = datetime.now(ET)
        dia = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"][ahora_et_full.weekday()]
        print(f"🚫 Mercado cerrado ({dia} {ahora_et}) | Abre Lun-Vie 9:30am ET")
        return

    print(f"\n📊 Escaneando {len(ACCIONES_VIP)} tickers... {ahora_et}")

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
        finally:
            time.sleep(0.3)  # ← 0.3s entre tickers = 1000 tickers en ~5 min (rate limit safe)


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
            # No sleep(300): el delay de 0.3s por ticker hace que el ciclo
            # dure ~5 minutos naturalmente con 1000 tickers

        except KeyboardInterrupt:
            print("\n🛑 Bot detenido por el usuario.")
            break
        except Exception as e:
            print(f"❌ ERROR GLOBAL: {e}")
            time.sleep(60)


if __name__ == "__main__":
    loop()