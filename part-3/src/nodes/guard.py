import re
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from src.config import get_llm
from src.state import AcademicAgentState
from src.utils import extract_clean_text, parse_llm_json

POLITE_REJECTION_TEMPLATE = POLITE_REJECTION_MESSAGE = (
    "Mohon maaf yang sebesar-besarnya. Sebagai Asisten Penulisan Karya Ilmiah, "
    "ruang lingkup keilmuan dan layanan saya secara khusus dibatasi pada hal-hal "
    "yang berkaitan dengan pedoman, kaidah, sistematika, format, tata bahasa, dan etika "
    "penulisan karya ilmiah (seperti Skripsi, Tesis, Disertasi, Makalah, Artikel Jurnal, "
    "maupun Laporan Penelitian).\n\n"
    "Pertanyaan yang Anda ajukan berada di luar ruang lingkup penulisan karya ilmiah "
    "(seperti informasi navigasi/rute perjalanan, rekomendasi kuliner/tempat makan, "
    "maupun topik umum non-akademik lainnya). "
    "Apabila Anda memiliki pertanyaan seputar penyusunan naskah penelitian, format sitasi, "
    "daftar rujukan, atau sistematika bab, silakan sampaikan dan saya akan dengan senang hati membantu Anda."
)

# 1. Istilah Akademik (In-Scope)
ACADEMIC_TERMS = {
    "skripsi", "tesis", "disertasi", "makalah", "jurnal", "artikel", "proposal",
    "karya ilmiah", "ilmiah", "penelitian", "metode", "metodologi", "sitasi", "kutipan",
    "daftar pustaka", "daftar rujukan", "abstrak", "latar belakang", "rumusan masalah",
    "tinjauan pustaka", "pedoman", "format", "bab", "sub-bab", "plagiasi", "tabel",
    "gambar", "lampiran", "eyd", "puebi", "baku", "diksi", "tata bahasa", "rujukan",
    "buku", "sinta", "scopus", "apa", "ieee", "font", "spasi", "margin", "tugas akhir",
    "menulis", "penulisan", "paragraf", "kalimat", "kerangka berpikir", "hipotesis",
    "variabel", "populasi", "sampel", "kualitatif", "kuantitatif", "rumusan", "simpulan",
    "kesimpulan", "pembahasan", "daftar isi", "halaman judul", "lembar persetujuan",
    "pengutipan", "perujukan", "mendeley", "zotero", "peneliti", "akademik", "naskah"
}

# 2. Pola Basa-Basi, Sapaan, Percakapan Sosial, & Pertanyaan Waktu (In-Scope)
SMALL_TALK_WORDS = {
    "hi", "hello", "hey", "halo", "hai", "hola",
    "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "selamat datang",
    "assalamualaikum", "assalamu'alaikum", "permisi", "kulonuwun", "sampurasun",
    "pagi", "siang", "sore", "malam",
    "apa kabar", "gimana kabarnya", "bagaimana kabarnya", "kabar baik", "sehat",
    "lagi apa", "lagi ngapain", "sedang apa", "lagi sibuk apa",
    "kamu siapa", "siapa kamu", "siapa namamu", "nama kamu siapa", "siapa nama anda",
    "kamu bisa apa", "bisa bantu apa", "apa tugasmu", "apa fungsi kamu",
    "bisa bantu saya", "bisa bantu aku", "tolong bantu", "tolong dong",
    "terima kasih", "makasih", "thanks", "thank you", "matur nuwun", "nuhun",
    "sama-sama", "kembali", "ok", "oke", "siap", "baiklah", "mantap", "keren", "paham", "mengerti",
    "tes", "test", "ping",
    # Pertanyaan Waktu Sistem (Temporal Awareness)
    "sekarang hari apa", "hari apa sekarang", "hari ini hari apa",
    "tanggal berapa sekarang", "sekarang tanggal berapa", "tanggal berapa hari ini", "hari ini tanggal berapa",
    "sekarang tahun berapa", "tahun berapa sekarang", "tahun ini tahun berapa",
    "jam berapa sekarang", "sekarang jam berapa", "waktu sekarang", "jam berapa ini"
}

# 3. Kata Kunci Luar Ruang Lingkup (Out-of-Scope)
OUT_OF_SCOPE_PHRASES = [
    # Rute & Navigasi Perjalanan
    "jalan menuju", "lewat mana", "rute ke", "arah ke", "peta ke", "naik apa ke",
    "naik bis ke", "naik kereta ke", "tol menuju", "jarak dari", "jarak ke", "angkot ke",
    # Makanan & Kuliner
    "makanan enak", "tempat makan", "warung makan", "restoran", "kuliner enak",
    "kuliner dekat", "tempat nongkrong", "cafe terdekat", "kafe terdekat", "resep", "masak",
    "bumbu", "goreng", "rebus",
    # Cuaca, Ramalan, Hiburan, Politik
    "cuaca hari ini", "ramalan cuaca", "hujan tidak", "besok hujan", "zodiak", "horoskop",
    "film bioskop", "nonton film", "lirik lagu", "chord gitar", "skor bola", "pertandingan bola",
    "pemilu", "pilpres", "pilkada", "calon bupati", "partai politik",
    "gosip artis", "harga emas", "promo diskon", "beli tiket"
]

def fast_scope_check(text: str) -> tuple[bool, bool]:
    """
    Evaluasi cepat berbasis heuristik (0 ms).
    Returns: (is_determined, is_in_scope)
    """
    t = text.lower().strip()
    t_clean = re.sub(r"^[^\w\s]+|[^\w\s]+$", "", t).strip()

    # 1. Cek Sapaan, Basa-Basi, & Waktu (In-Scope)
    if t_clean in SMALL_TALK_WORDS or t in SMALL_TALK_WORDS:
        return True, True
        
    for st in SMALL_TALK_WORDS:
        if t_clean.startswith(st) or t_clean == st:
            return True, True

    # 2. Cek Frasa Jelas Di Luar Topik (Out-of-Scope)
    for bad_phrase in OUT_OF_SCOPE_PHRASES:
        if bad_phrase in t:
            if not any(acad in t for acad in ["skripsi", "penelitian", "makalah", "karya ilmiah", "tesis"]):
                return True, False

    # 3. Cek Kata Kunci Karya Ilmiah (In-Scope)
    for acad_term in ACADEMIC_TERMS:
        if acad_term in t:
            return True, True

    return False, True

def scope_guard_node(state: AcademicAgentState) -> dict:
    messages = state.get("messages", [])
    if not messages:
        return {"is_in_scope": False, "rejection_message": POLITE_REJECTION_MESSAGE}

    last_user_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or (hasattr(msg, "type") and msg.type == "human"):
            last_user_msg = extract_clean_text(msg.content)
            break
    if not last_user_msg:
        last_user_msg = extract_clean_text(messages[-1].content)

    determined, in_scope = fast_scope_check(last_user_msg)
    if determined:
        return {
            "is_in_scope": in_scope,
            "rejection_message": None if in_scope else POLITE_REJECTION_MESSAGE
        }

    try:
        llm = get_llm(temperature=0.0)
        eval_prompt = (
            "Anda adalah evaluator ruang lingkup untuk AI Asisten Penulisan Karya Ilmiah.\n"
            "Pedoman Klasifikasi:\n"
            "1. Basa-basi, sapaan santun, tanya kabar, pertanyaan waktu sekarang ('sekarang jam/hari/tanggal/tahun berapa') WAJIB DISETUJUI (is_in_scope: true).\n"
            "2. Pertanyaan seputar penulisan karya ilmiah, skripsi, tesis, jurnal, buku, tata bahasa, sitasi, pedoman WAJIB DISETUJUI (is_in_scope: true).\n"
            "3. Pertanyaan pengetahuan harian di luar karya ilmiah (seperti rute perjalanan, petunjuk jalan, rekomendasi tempat makan/kuliner, ramalan cuaca, film, olahraga) WAJIB DITOLAK (is_in_scope: false).\n\n"
            f"Pertanyaan pengguna: \"{last_user_msg}\"\n"
            "Keluaran WAJIB HANYA JSON: {\"is_in_scope\": true} atau {\"is_in_scope\": false}"
        )
        response = llm.invoke([HumanMessage(content=eval_prompt)])
        data = parse_llm_json(response.content)
        is_scope = bool(data.get("is_in_scope", True))
        return {
            "is_in_scope": is_scope,
            "rejection_message": None if is_scope else POLITE_REJECTION_MESSAGE
        }
    except Exception:
        return {
            "is_in_scope": True,
            "rejection_message": None
        }

def reject_node(state: AcademicAgentState) -> dict:
    rejection = state.get("rejection_message") or POLITE_REJECTION_MESSAGE
    return {
        "messages": [AIMessage(content=rejection)]
    }
