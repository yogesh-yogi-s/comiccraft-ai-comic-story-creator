import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.routes import router
from app.image_generator import _get_hf_api_key

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("comiccraft")


def ensure_directories():
    """Ensure static directories exist before serving."""
    dirs = [
        os.path.join("static", "panels"),
        os.path.join("static", "exports"),
        os.path.join("static", "css"),
        os.path.join("static", "js"),
        "templates"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    ensure_directories()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    hf_key = _get_hf_api_key()

    logger.info("==================================================")
    logger.info(" ComicCraft - AI Comic Story Creator starting up ")
    logger.info("==================================================")
    if gemini_key:
        logger.info(" [OK] Google Gemini API Key configured.")
    else:
        logger.warning(" [NOTICE] GEMINI_API_KEY not detected. Using built-in high fidelity fallback storyteller.")

    if hf_key:
        logger.info(" [OK] Hugging Face API Key configured; panels will be generated one at a time.")
    else:
        logger.info(" [INFO] HF_API_KEY not detected. Using built-in Graphic Comic Art Renderer fallback.")

    logger.info(" Web application accessible at: http://127.0.0.1:8000")
    logger.info(" Interactive API Docs:          http://127.0.0.1:8000/docs")
    logger.info("==================================================")

    yield

    # Shutdown sequence
    logger.info("ComicCraft application shutting down.")


app = FastAPI(
    title="ComicCraft - AI Comic Story Creator",
    description="Generates custom 5-panel comic strips, illustrations, narration, and exportable PDFs with Google Gemini & Stable Diffusion.",
    version="1.0.0",
    lifespan=lifespan
)

# Ensure folders exist immediately for static mounting
ensure_directories()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include main application routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
