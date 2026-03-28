"""
strategy.py — Módulo de compatibilidad.

Toda la lógica de estrategia fue consolidada en bot.py para tener
una única fuente de verdad. Este archivo redirige las importaciones
para que cualquier código que ya use 'from strategy import ...' siga
funcionando sin cambios.
"""

from bot import (
    ejecutar_estrategia,
    actualizar_martingala,
    ejecutar_orden,
    ACCIONES_VIP as ACCIONES,
    CAPITAL_BASE,
    RIESGO,
    TP,
    SL,
    nivel_martingala,
    MAX_MARTINGALA,
    MULT,
)

__all__ = [
    "ejecutar_estrategia",
    "actualizar_martingala",
    "ejecutar_orden",
    "ACCIONES",
    "CAPITAL_BASE",
    "RIESGO",
    "TP",
    "SL",
    "nivel_martingala",
    "MAX_MARTINGALA",
    "MULT",
]