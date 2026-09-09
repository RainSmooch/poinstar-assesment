import json
import logging
import warnings
import re
import datetime

def silence_warnings():
    """Menonaktifkan warning teknis internal SDK agar terminal bersih dan ramah pengguna."""
    warnings.filterwarnings("ignore")
    logging.getLogger("google.genai").setLevel(logging.ERROR)
    logging.getLogger("google").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    try:
        from google.genai.models import Models
        Models._logged_afc_warning = True
    except Exception:
        pass

def extract_clean_text(content) -> str:
    """Mengekstrak teks bersih dari pesan LLM yang mungkin berbentuk list atau dict."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                if "text" in part:
                    parts.append(part["text"])
                elif "content" in part:
                    parts.append(str(part["content"]))
        return "".join(parts).strip()
    return str(content).strip()

def parse_llm_json(raw_response) -> dict:
    """Mem-parsing keluaran JSON dari LLM secara aman."""
    text = extract_clean_text(raw_response)
    if "```" in text:
        match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except Exception:
                pass
        return {}

def get_current_time_info() -> dict:
    """
    Mengambil informasi waktu sistem saat ini dalam bahasa Indonesia baku.
    Menyediakan data hari, tanggal, bulan, tahun, jam, sapaan waktu, dan tahun akademik.
    """
    now = datetime.datetime.now()
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    months = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]

    day_name = days[now.weekday()]
    month_name = months[now.month - 1]
    time_str = now.strftime("%H:%M:%S")
    hour = now.hour

    # Penentuan Sapaan Waktu Alami
    if 5 <= hour < 11:
        greeting = "Selamat pagi"
    elif 11 <= hour < 15:
        greeting = "Selamat siang"
    elif 15 <= hour < 18:
        greeting = "Selamat sore"
    else:
        greeting = "Selamat malam"

    # Penentuan Tahun Akademik (semester baru umumnya dimulai bulan Juli)
    if now.month >= 7:
        academic_year = f"{now.year}/{now.year + 1}"
    else:
        academic_year = f"{now.year - 1}/{now.year}"

    full_date_str = f"{day_name}, {now.day} {month_name} {now.year}"
    full_datetime_str = f"{full_date_str}, pukul {time_str} WIB"
    citation_access_str = f"Diakses pada {now.day} {month_name} {now.year}"

    return {
        "now": now,
        "day_name": day_name,
        "day": now.day,
        "month_name": month_name,
        "month": now.month,
        "year": now.year,
        "time_str": time_str,
        "greeting": greeting,
        "full_date_str": full_date_str,
        "full_datetime_str": full_datetime_str,
        "academic_year": academic_year,
        "citation_access_str": citation_access_str
    }
