import os
import time
import logging
import threading
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

from bot import ejecutar_estrategia, actualizar_martingala
from risk_manager import inicializar_dia

# ==============================
# LOGGING
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ==============================
# ESTADO GLOBAL
# ==============================
bot_state = {
    "status": "idle",        # idle | running | stopped | error
    "last_run": None,
    "error": None,
    "is_running": False
}

# ==============================
# LOOP DEL BOT (REAL)
# ==============================
def trading_loop():
    global bot_state

    if bot_state["is_running"]:
        logger.warning("⚠️ Bot ya está corriendo")
        return

    bot_state["is_running"] = True
    bot_state["status"] = "running"
    bot_state["error"] = None

    logger.info("🚀 BOT INICIADO (PAPER TRADING)")
    inicializar_dia()

    # 🔥 LOOP CONTROLADO
    while bot_state["is_running"]:
        try:
            ahora = datetime.now()
            bot_state["last_run"] = ahora.isoformat()

            logger.info(f"⏰ Ejecutando estrategia: {ahora}")

            ejecutar_estrategia()
            actualizar_martingala()

            # ⏱️ Espera 5 minutos (timeframe)
            time.sleep(300)

        except Exception as e:
            bot_state["status"] = "error"
            bot_state["error"] = str(e)

            logger.error(f"❌ Error en el bot: {e}", exc_info=True)

            # evita que se caiga
            time.sleep(60)

    logger.info("🛑 Bot detenido correctamente")

# ==============================
# LIFESPAN (Koyeb)
# ==============================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Bot desplegado")

    # AUTO RUN
    if os.getenv("AUTO_RUN", "true").lower() == "true":
        threading.Thread(target=trading_loop, daemon=True).start()
        logger.info("▶️ AUTO_RUN activado")

    yield

    logger.info("🛑 App cerrada")

# ==============================
# APP
# ==============================
app = FastAPI(
    title="Alpaca Trading Bot",
    description="Bot profesional de trading (paper trading)",
    version="3.0.0",
    lifespan=lifespan
)

# ==============================
# ENDPOINTS
# ==============================
@app.get("/")
def root():
    return {
        "service": "Alpaca Trading Bot",
        "status": "online",
        "bot_status": bot_state["status"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/status")
def status():
    return bot_state

@app.post("/start")
def start_bot():
    if bot_state["is_running"]:
        return JSONResponse(
            status_code=409,
            content={"message": "El bot ya está corriendo"}
        )

    threading.Thread(target=trading_loop, daemon=True).start()

    return {
        "message": "🚀 Bot iniciado",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/stop")
def stop_bot():
    if not bot_state["is_running"]:
        return {"message": "El bot ya está detenido"}

    bot_state["is_running"] = False
    bot_state["status"] = "stopped"

    return {"message": "🛑 Bot detenido"}

@app.post("/reset")
def reset():
    if bot_state["is_running"]:
        return JSONResponse(
            status_code=409,
            content={"message": "No puedes resetear mientras corre"}
        )

    bot_state.update({
        "status": "idle",
        "last_run": None,
        "error": None,
        "is_running": False
    })

    return {"message": "Estado reseteado"}

# ==============================
# ENTRYPOINT
# ==============================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)