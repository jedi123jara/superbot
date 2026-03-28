# ==============================
# CONFIGURACIÓN GLOBAL (defaults)
# ==============================
# Estos valores se sobreescriben por ticker en bot.py / strategy.py

PAR             = "SPY"
RSI_UMBRAL_CALL = 65      # RSI > este valor → señal CALL
RSI_UMBRAL_PUT  = 32      # RSI < este valor → señal PUT
VOL_MINIMO      = 1.2     # Volumen relativo mínimo para operar
FILTRO_HORARIO  = False   # True = solo operar en horario prime