import json
import sqlite3
import uuid
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from src.config import BASE_DIR, CHECKPOINT_DB_PATH
from src.graph import get_agent_graph
from src.tools.kb_search import search_knowledge_base
from src.utils import silence_warnings, extract_clean_text, get_current_time_info
from src.memory import get_sqlite_conn

silence_warnings()

app = FastAPI(
    title="Asisten Karya Ilmiah UM",
    description="Asisten Penulisan Karya Ilmiah Berbasis Pedoman UM 2017 & LangGraph",
    version="1.0.0"
)

static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"
static_dir.mkdir(parents=True, exist_ok=True)
templates_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

graph = get_agent_graph()

PEDOMAN_CHAPTERS = [
    {"number": 1, "title": "Jenis-Jenis Karya Ilmiah", "pages": "1 - 5", "desc": "Tugas Akhir, Skripsi, Tesis, Disertasi, Makalah, Artikel, dan Laporan."},
    {"number": 2, "title": "Proposal Tugas Akhir, Skripsi, Tesis, Disertasi", "pages": "6 - 8", "desc": "Substansi keaslian, kemutakhiran, ruang lingkup, manfaat, dan format proposal."},
    {"number": 3, "title": "Sistematika dan Isi TA, Skripsi, Tesis, Disertasi", "pages": "9 - 18", "desc": "Bagian Awal, Bagian Inti (Alternatif 1, 2, 3), dan Bagian Akhir."},
    {"number": 4, "title": "Sistematika Artikel Jurnal, Makalah, & Laporan", "pages": "19 - 27", "desc": "Format artikel hasil penelitian, artikel telaah, makalah, dan laporan."},
    {"number": 5, "title": "Pengutipan, Perujukan, dan Daftar Rujukan", "pages": "28 - 38", "desc": "Kutipan langsung <40 kata, >=40 kata, perujukan buku, jurnal, prosiding, internet."},
    {"number": 6, "title": "Kebahasaan", "pages": "39 - 49", "desc": "Ragam bahasa ilmiah, pilihan kata (diksi), tata kalimat, paragraf, penulisan angka & lambang."},
    {"number": 7, "title": "Etika Penulisan Karya Ilmiah", "pages": "50", "desc": "Keaslian, pencegahan plagiarisme, fabrikasi, dan falsifikasi."},
    {"number": 8, "title": "Penataan Isi Karya Ilmiah", "pages": "51 - 56", "desc": "Tata cara penomoran bab/sub-bab, penataan tabel, bagan, dan gambar."},
    {"number": 9, "title": "Pencetakan dan Penjilidan", "pages": "57 - 61", "desc": "Kertas, margin, jenis dan ukuran font, spasi baris, dan standar penjilidan."},
    {"number": 10, "title": "Lampiran Format & Template", "pages": "63 - 122", "desc": "Contoh halaman sampul, judul, lembar persetujuan, daftar isi, tabel, rujukan."}
]

class ChatRequest(BaseModel):
    message: str
    thread_id: str = None

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    time_info = get_current_time_info()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "time_info": time_info,
            "chapters": PEDOMAN_CHAPTERS
        }
    )

@app.get("/api/time")
async def get_time():
    return get_current_time_info()

@app.get("/api/pedoman/chapters")
async def get_chapters():
    return {"chapters": PEDOMAN_CHAPTERS}

@app.get("/api/pedoman/search")
async def search_pedoman_api(q: str):
    if not q or not q.strip():
        return {"results": []}
    results = search_knowledge_base(q, top_k=3)
    return {"results": results}

@app.get("/api/threads")
async def get_threads():
    threads = []
    if CHECKPOINT_DB_PATH.exists():
        try:
            conn = sqlite3.connect(CHECKPOINT_DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id NOT LIKE 'test_%' ORDER BY checkpoint_id DESC LIMIT 15")
            threads = [row[0] for row in cur.fetchall()]
            conn.close()
        except Exception:
            pass
    return {"threads": threads}

@app.delete("/api/threads/{thread_id}")
async def delete_thread(thread_id: str):
    if not thread_id or not thread_id.strip():
        return {"status": "error", "message": "thread_id tidak valid."}
    deleted = 0
    if CHECKPOINT_DB_PATH.exists():
        try:
            conn = get_sqlite_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
            cur.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            deleted = cur.rowcount
            conn.commit()
            # conn.close()  <-- Tidak perlu, ini koneksi global
        except Exception:
            return {"status": "error", "message": "Gagal menghapus sesi dari database."}
    return {"status": "ok", "thread_id": thread_id, "deleted": deleted}

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    thread_id = payload.thread_id or f"sesi-{uuid.uuid4().hex[:6]}"
    user_message = payload.message.strip()

    async def event_generator() -> AsyncGenerator[str, None]:
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = {"messages": [HumanMessage(content=user_message)]}

        has_chunk = False
        try:
            for chunk, meta in graph.stream(initial_state, config=config, stream_mode="messages"):
                msg_type = type(chunk).__name__
                if msg_type == "AIMessageChunk":
                    has_chunk = True
                    text_chunk = extract_clean_text(chunk.content)
                    if text_chunk:
                        yield f"data: {json.dumps({'type': 'token', 'content': text_chunk})}\n\n"
                elif msg_type == "AIMessage" and not has_chunk:
                    text_chunk = extract_clean_text(chunk.content)
                    if text_chunk:
                        yield f"data: {json.dumps({'type': 'token', 'content': text_chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': 'Mohon maaf, terjadi kendala saat memproses jawaban.'})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

if __name__ == "__main__":
    import uvicorn
    print("================================================================================")
    print("   MEMULAI WEB UI ASISTEN PENULISAN KARYA ILMIAH (UNIVERSITAS NEGERI MALANG)")
    print("   Buka browser pada alamat: http://127.0.0.1:8000")
    print("================================================================================")
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)
