import pandas as pd


# ==============================
# RSI (Wilder's Smoothing)
# ==============================
def calcular_rsi(df, periodo=14):
    """RSI usando el método de suavizado de Wilder (el estándar)."""
    delta = df['Close'].diff()

    ganancia = delta.clip(lower=0)
    perdida  = (-delta).clip(lower=0)

    # ewm con com=periodo-1 equivale a alpha=1/periodo (Wilder)
    avg_gan = ganancia.ewm(com=periodo - 1, min_periods=periodo).mean()
    avg_per = perdida.ewm(com=periodo - 1, min_periods=periodo).mean()

    # Evitar división por cero
    rs  = avg_gan / avg_per.replace(0, float('inf'))
    rsi = 100 - (100 / (1 + rs))

    return rsi


# ==============================
# MACD
# ==============================
def calcular_macd(df, rapido=12, lento=26, senal=9):
    ema_r = df['Close'].ewm(span=rapido, adjust=False).mean()
    ema_l = df['Close'].ewm(span=lento,  adjust=False).mean()
    macd        = ema_r - ema_l
    macd_signal = macd.ewm(span=senal, adjust=False).mean()
    macd_hist   = macd - macd_signal
    return macd, macd_signal, macd_hist


# ==============================
# VOLUMEN RELATIVO
# ==============================
def calcular_volumen_relativo(df, ventana=20):
    """Vol actual / promedio de N velas. > 1.2 = volumen alto."""
    promedio = df['Volume'].rolling(window=ventana).mean()
    return df['Volume'] / promedio.replace(0, float('inf'))


# ==============================
# CALCULO COMPLETO
# ==============================
def calcular_todos(df):
    """
    Recibe un DataFrame con columnas OHLCV (Open/High/Low/Close/Volume).
    Retorna el mismo DataFrame con indicadores agregados.
    """
    df = df.copy()

    # RSI
    df['rsi'] = calcular_rsi(df)

    # Volumen relativo
    df['vol_relativo'] = calcular_volumen_relativo(df)

    # MACD
    df['macd'], df['macd_signal'], df['macd_hist'] = calcular_macd(df)

    # EMA rápida / lenta para tendencia
    df['ema_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['ema_50'] = df['Close'].ewm(span=50, adjust=False).mean()

    return df
