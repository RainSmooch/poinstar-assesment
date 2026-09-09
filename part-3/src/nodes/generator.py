from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from src.config import get_llm
from src.state import AcademicAgentState
from src.tools.kb_search import format_kb_context
from src.tools.web_search import format_web_context
from src.utils import extract_clean_text, get_current_time_info

GENERATOR_SYSTEM_PROMPT = """Anda adalah Asisten Resmi Penulisan Karya Ilmiah berlandaskan 'Pedoman Penulisan Karya Ilmiah Edisi 2017 (Universitas Negeri Malang - UM Press)'.

PRINSIP RESPON CEPAT, PADAT, & AKADEMIK:
1. Langsung ke Inti Kaidah:
   - Hindari kata-kata pengantar berulang atau klise (seperti: "Terima kasih atas pertanyaan Anda...", "Sebagai asisten...", "Terkait pertanyaan Anda...").
   - Langsung paparkan jawaban, ketentuan teknis, dan format aturan yang ditanyakan secara lugas, terstruktur (gunakan poin/daftar), dan efisien.
2. Sitasi Presisi:
   - Wajib menyertakan rujukan nomor Bab dan Halaman pedoman (contoh: [Pedoman UM 2017, Bab 5, Hlm. 29]).
3. Sapaan & Basa-Basi:
   - HANYA berikan salam dan perkenalan singkat apabila pengguna secara khusus menyapa (misal 'hi', 'halo') atau menanyakan identitas Anda.
4. Kesadaran Waktu:
   - Gunakan tahun berjalan sebagai acuan kemutakhiran pustaka (10 tahun terakhir).
5. Nada Bicara:
   - Santun, formal, berwibawa, dan bernuansa akademik baku.
"""

def generate_response_node(state: AcademicAgentState) -> dict:
    messages = state.get("messages", [])
    kb_results = state.get("kb_results", [])
    web_results = state.get("web_results", [])
    
    time_info = get_current_time_info()
    time_context = (
        f"--- WAKTU SEKARANG: {time_info['full_datetime_str']} | Tahun: {time_info['year']} | "
        f"Pustaka Mutakhir 10 Tahun: {time_info['year'] - 10}-{time_info['year']} ---"
    )

    kb_text = format_kb_context(kb_results) if kb_results else ""
    web_text = format_web_context(web_results) if web_results else ""
    
    context_blocks = [time_context]
    if kb_text:
        context_blocks.append(f"--- PEDOMAN UM 2017 ---\n{kb_text}")
    if web_text:
        context_blocks.append(f"--- RUJUKAN WEB ---\n{web_text}")
        
    context_str = "\n\n".join(context_blocks)
    
    prompt_messages = [
        SystemMessage(content=GENERATOR_SYSTEM_PROMPT),
        SystemMessage(content=context_str)
    ]
        
    for msg in messages:
        if isinstance(msg, (HumanMessage, AIMessage)):
            clean_content = extract_clean_text(msg.content)
            if isinstance(msg, HumanMessage):
                prompt_messages.append(HumanMessage(content=clean_content))
            else:
                prompt_messages.append(AIMessage(content=clean_content))
        elif hasattr(msg, "type"):
            clean_content = extract_clean_text(getattr(msg, "content", ""))
            if msg.type == "human":
                prompt_messages.append(HumanMessage(content=clean_content))
            elif msg.type == "ai":
                prompt_messages.append(AIMessage(content=clean_content))

    try:
        llm = get_llm(temperature=0.2)
        raw_response = llm.invoke(prompt_messages)
        clean_text = extract_clean_text(raw_response.content)
        return {
            "messages": [AIMessage(content=clean_text)]
        }
    except Exception:
        fallback_msg = (
            "Mohon maaf yang sebesar-besarnya, saat ini sistem sedang mengalami kendala jaringan atau server.\n"
            "Silakan pastikan koneksi internet Anda aktif dan ajukan kembali pertanyaan Anda."
        )
        return {
            "messages": [AIMessage(content=fallback_msg)]
        }
