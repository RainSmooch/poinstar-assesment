import sys
import os
import uuid
import threading
from langchain_core.messages import HumanMessage
from src.config import is_api_key_configured, GEMINI_MODEL, BASE_DIR, get_llm
from src.graph import get_agent_graph
from src.tools.kb_search import search_knowledge_base, format_kb_context
from src.tools.web_search import search_web, format_web_context
from src.utils import silence_warnings, extract_clean_text

# Nonaktifkan warning internal SDK
silence_warnings()

BANNER = """
================================================================================
          ASISTEN CERDAS PENULISAN KARYA ILMIAH AKADEMIK
   Berlandaskan Pedoman Penulisan Karya Ilmiah 2017 (UM Press)
================================================================================
Perintah Bantuan:
  /new          : Memulai sesi konsultasi baru
  /thread <id>  : Membuka kembali riwayat sesi tertentu
  /pedoman <q>  : Telusuri langsung pedoman penulisan UM 2017
  /web <q>      : Telusuri kaidah penulisan via web
  /keluar       : Selesai dan keluar dari aplikasi
================================================================================
"""

def ensure_api_key():
    if is_api_key_configured():
        return True
    print("\nKunci API Gemini (GEMINI_API_KEY) belum terpasang di berkas .env.")
    key = input("Silakan masukkan kunci API Gemini Anda: ").strip()
    if not key:
        print("Kunci API diperlukan agar asisten dapat bekerja. Aplikasi dihentikan.")
        return False
    
    env_path = BASE_DIR / ".env"
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith("GEMINI_API_KEY="):
            new_lines.append(f"GEMINI_API_KEY={key}")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        new_lines.insert(0, f"GEMINI_API_KEY={key}")
    
    env_path.write_text("\n".join(new_lines), encoding="utf-8")
    os.environ["GEMINI_API_KEY"] = key
    print("Kunci API berhasil disimpan.")
    return True

def _warmup_network():
    """Memanaskan koneksi API di latar belakang saat aplikasi dibuka."""
    try:
        llm = get_llm()
        llm.invoke("ping")
    except Exception:
        pass

def run_cli():
    print(BANNER)
    if not ensure_api_key():
        sys.exit(1)

    # Mulai pemanasan koneksi secara asynchronous
    threading.Thread(target=_warmup_network, daemon=True).start()

    graph = get_agent_graph()
    current_thread = f"sesi-{uuid.uuid4().hex[:6]}"
    print("Status Sistem: Siap melayani konsultasi (Mode Generasi Instan & Streaming).")
    print(f"ID Sesi Aktif: {current_thread}\n")

    while True:
        try:
            user_input = input(f"[{current_thread}] Anda > ").strip()
            if not user_input:
                continue

            # Perintah khusus
            cmd = user_input.lower()
            if cmd in ["/keluar", "/exit", "exit", "quit", "keluar"]:
                print("\nTerima kasih telah berkonsultasi. Semoga penyusunan karya ilmiah Anda berjalan lancar!\n")
                break

            if cmd == "/new":
                current_thread = f"sesi-{uuid.uuid4().hex[:6]}"
                print(f"\n[Sesi Baru] Berhasil beralih ke sesi: {current_thread}\n")
                continue

            if cmd.startswith("/thread "):
                new_tid = user_input[8:].strip()
                if new_tid:
                    current_thread = new_tid
                    print(f"\n[Memori] Membuka kembali sesi: {current_thread}\n")
                continue

            if cmd.startswith("/pedoman "):
                query = user_input[9:].strip()
                print(f"\n[Pencarian Pedoman] Mencari: \"{query}\"...\n")
                results = search_knowledge_base(query, top_k=2)
                print(format_kb_context(results))
                print("\n" + "="*80 + "\n")
                continue

            if cmd.startswith("/web "):
                query = user_input[5:].strip()
                print(f"\n[Pencarian Web] Mencari: \"{query}\"...\n")
                results = search_web(query, max_results=3)
                print(format_web_context(results))
                print("\n" + "="*80 + "\n")
                continue

            # Eksekusi LangGraph dengan Real-Time Token Streaming
            print("\nAsisten: ", end="", flush=True)
            config = {"configurable": {"thread_id": current_thread}}
            initial_state = {
                "messages": [HumanMessage(content=user_input)]
            }

            has_chunk = False
            for chunk, meta in graph.stream(initial_state, config=config, stream_mode="messages"):
                msg_type = type(chunk).__name__
                if msg_type == "AIMessageChunk":
                    has_chunk = True
                    txt = extract_clean_text(chunk.content)
                    sys.stdout.write(txt)
                    sys.stdout.flush()
                elif msg_type == "AIMessage" and not has_chunk:
                    txt = extract_clean_text(chunk.content)
                    sys.stdout.write(txt)
                    sys.stdout.flush()

            print("\n\n" + "-"*80 + "\n")

        except KeyboardInterrupt:
            print("\n\nKonsultasi diakhiri. Sampai jumpa!")
            break
        except Exception:
            print("\nMohon maaf, terjadi kendala saat memproses pertanyaan Anda. Silakan coba kembali beberapa saat lagi.\n")

if __name__ == "__main__":
    run_cli()
