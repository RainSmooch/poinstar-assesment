from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from src.state import AcademicAgentState
from src.config import get_llm
from src.utils import extract_clean_text

class ToolDecision(BaseModel):
    """
    Struktur keputusan penalaran agen (Agentic Reasoning) untuk menentukan pemanggilan tools.
    """
    thought: str = Field(
        description="Analisis penalaran kritis: jelaskan mengapa naskah Pedoman UM 2017 dan/atau penelusuran web eksternal diperlukan atau tidak diperlukan."
    )
    need_kb: bool = Field(
        description="True jika pertanyaan membutuhkan rujukan aturan/kaidah/format dari Pedoman Penulisan Karya Ilmiah UM 2017 (skripsi, tesis, disertasi, makalah, pengutipan, rujukan, tata letak, margin, font, dsb). False jika hanya sapaan, ucapan terima kasih, pertanyaan identitas asisten, atau penjelasan umum."
    )
    kb_query: Optional[str] = Field(
        None,
        description="Kueri pencarian naskah pedoman UM yang spesifik dan padat (hanya kata kunci penting, bukan kalimat panjang pengguna) jika need_kb=True."
    )
    need_web: bool = Field(
        description="True jika pertanyaan membutuhkan informasi eksternal terkini di luar Pedoman UM 2017 (misal: format sitasi APA edisi 7, standar IEEE, software referensi Mendeley/Zotero, indeks SINTA/Scopus, turnitin, atau publikasi internet)."
    )
    web_query: Optional[str] = Field(
        None,
        description="Kueri pencarian web eksternal yang spesifik dan terarah jika need_web=True."
    )

THINKING_SYSTEM_PROMPT = """Anda adalah modul penalaran perencana (Reasoning & Tool-Decision Planner) untuk Asisten Penulisan Karya Ilmiah Universitas Negeri Malang (UM).
Tugas Anda adalah menganalisis pesan pengguna dan secara otonom memutuskan apakah perlu memanggil:
1. 'need_kb' (Naskah Pedoman Karya Ilmiah UM 2017):
   - Wajib 'true' jika pengguna menanyakan aturan, format, kaidah kutipan, sistematika skripsi/tesis/makalah, daftar rujukan, penomoran, tabel/gambar, atau kertas/spasi di UM.
   - Tetapkan 'false' jika pesan pengguna hanyalah sapaan (halo/pagi), ucapan terima kasih, pertanyaan identitas Anda, atau obrolan santai yang tidak memerlukan dokumen pedoman.
2. 'need_web' (Pencarian Web Eksternal):
   - Wajib 'true' jika pengguna menanyakan standar internasional di luar pedoman institusi UM (misal: APA style edisi 7, format IEEE, panduan penggunaan Mendeley/Zotero, verifikasi indeks jurnal SINTA/Scopus, Turnitin, dll).
   - Tetapkan 'false' jika pertanyaan murni seputar gaya selingkung resmi UM 2017 atau percakapan biasa.

PENTING:
- Rumuskan 'kb_query' dan 'web_query' secara padat dan terarah menggunakan kata kunci esensial (misal: 'kutipan langsung 40 kata', 'sistematika skripsi bab 1', 'apa style edisi 7 mendeley').
- Jangan sekadar menyalin seluruh kalimat tanya pengguna jika kalimat tersebut bertele-tele.
"""

def fallback_heuristic_decision(user_msg: str) -> dict:
    """
    Fallback cepat jika pemanggilan LLM mengalami kendala jaringan atau batas kuota.
    """
    t = user_msg.lower().strip()
    
    # Sapaan murni tidak memerlukan tools
    greetings = {"halo", "hi", "hey", "selamat pagi", "selamat siang", "selamat malam", "terima kasih", "makasih", "siapa kamu"}
    if any(t == g or t.startswith(g) for g in greetings) and len(t.split()) <= 4:
        return {
            "thought": "Fallback heuristic: Sapaan atau percakapan santai, tidak membutuhkan retrieval.",
            "need_kb": False,
            "kb_query": None,
            "need_web": False,
            "web_query": None
        }

    # Kata kunci web eksternal
    web_terms = {
        "apa 7", "apa edisi 7", "apa style", "edisi 7", "edisi ke-7",
        "ieee", "mendeley", "zotero", "sinta", "scopus", "turnitin"
    }
    need_web = any(term in t for term in web_terms)
    
    # Secara umum pertanyaan karya ilmiah memerlukan naskah pedoman UM
    return {
        "thought": "Fallback heuristic: Menganalisis kaidah penulisan berdasarkan naskah Pedoman UM 2017.",
        "need_kb": True,
        "kb_query": user_msg,
        "need_web": need_web,
        "web_query": user_msg if need_web else None
    }

def thinking_node(state: AcademicAgentState) -> dict:
    messages = state.get("messages", [])
    user_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or (hasattr(msg, "type") and msg.type == "human"):
            user_msg = extract_clean_text(msg.content)
            break
    if not user_msg and messages:
        user_msg = extract_clean_text(messages[-1].content)

    # 1. Panggil LLM dengan Structured Output (Pydantic)
    try:
        llm = get_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(ToolDecision)
        
        prompt_msgs = [
            SystemMessage(content=THINKING_SYSTEM_PROMPT),
            HumanMessage(content=f"Pesan Pengguna: \"{user_msg}\"\nBerikan analisis penalaran dan keputusan tool Anda.")
        ]
        
        decision: ToolDecision = structured_llm.invoke(prompt_msgs)
        
        # Validasi konsistensi kueri
        kb_query = decision.kb_query if decision.need_kb and decision.kb_query else (user_msg if decision.need_kb else None)
        web_query = decision.web_query if decision.need_web and decision.web_query else (user_msg if decision.need_web else None)
        
        return {
            "thinking_process": decision.thought,
            "need_kb": decision.need_kb,
            "kb_query": kb_query,
            "need_web": decision.need_web,
            "web_query": web_query
        }
    except Exception:
        # 2. Resilient Graceful Fallback
        fallback = fallback_heuristic_decision(user_msg)
        return {
            "thinking_process": f"{fallback['thought']} (LLM structured reasoning fallback)",
            "need_kb": fallback["need_kb"],
            "kb_query": fallback["kb_query"],
            "need_web": fallback["need_web"],
            "web_query": fallback["web_query"]
        }
