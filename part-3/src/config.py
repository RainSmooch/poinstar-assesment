import os
from pathlib import Path
from dotenv import load_dotenv
from src.utils import silence_warnings

# Nonaktifkan warning internal SDK
silence_warnings()

# Muat variabel dari .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

PDF_PATH = BASE_DIR / "Pedoman-Penulisan-Karya-Ilmiah-2017.pdf"
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "ocr_cache"
CHUNKS_PATH = DATA_DIR / "pedoman_chunks.json"
STORAGE_DIR = BASE_DIR / "storage"
CHECKPOINT_DB_PATH = STORAGE_DIR / "checkpoints.db"

DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
STORAGE_DIR.mkdir(exist_ok=True)

def is_api_key_configured() -> bool:
    return bool(GEMINI_API_KEY and GEMINI_API_KEY.strip() and GEMINI_API_KEY != "your_gemini_api_key_here")

def get_llm(model_name: str = None, temperature: float = 0.2):
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or GEMINI_API_KEY
    if not key or key == "your_gemini_api_key_here":
        raise ValueError(
            "Kunci API Gemini belum dikonfigurasi di berkas .env.\n"
            "Silakan masukkan kunci API Anda pada berkas .env."
        )
        
    model = model_name or os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=key,
        temperature=temperature,
    )
