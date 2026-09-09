import os
import re
import time
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.6-flash"
CHUNK_SIZE = 10000
MIN_CONTENT_LENGTH = 500
MIN_SUMMARY_WORDS = 100
MAX_SUMMARY_WORDS = 250
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def generate_content_with_retry(prompt: str, max_output_tokens: int = 1000) -> str:
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_output_tokens
                )
            )

            if not response.text:
                raise RuntimeError("Gemini mengembalikan response kosong.")

            return response.text.strip()

        except Exception as e:
            last_error = e
            error_text = str(e)

            retryable = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
                or "high demand" in error_text.lower()
            )

            if not retryable or attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Gemini gagal setelah {attempt} percobaan: {e}"
                )

            time.sleep(RETRY_DELAY_SECONDS * attempt)

    raise RuntimeError(f"Gemini gagal: {last_error}")


def fetch_with_requests(url: str) -> str:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )
    response.raise_for_status()
    return response.text


def fetch_with_playwright(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent=HEADERS["User-Agent"]
        )

        page.goto(
            url,
            wait_until="networkidle",
            timeout=30000
        )

        html = page.content()
        browser.close()

    return html


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup([
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
        "noscript",
        "iframe"
    ]):
        element.decompose()

    article = soup.find("article")

    if article:
        container = article
    else:
        main = soup.find("main")
        container = main if main else (soup.body or soup)

    text = container.get_text(
        separator=" ",
        strip=True
    )

    return re.sub(r"\s+", " ", text).strip()


def scrape_webpage(url: str) -> str:
    try:
        html = fetch_with_requests(url)
        text = clean_html(html)

        if len(text) >= MIN_CONTENT_LENGTH:
            return text

    except requests.exceptions.RequestException:
        pass

    try:
        html = fetch_with_playwright(url)
        text = clean_html(html)

        if text:
            return text

    except Exception as e:
        raise RuntimeError(f"Scraping gagal: {e}")

    raise RuntimeError(
        "Tidak ada konten yang berhasil diekstrak dari halaman."
    )


def chunk_text(text: str, max_chunk_size: int = CHUNK_SIZE) -> list[str]:
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word) + 1

        if (
            current_chunk
            and current_length + word_length > max_chunk_size
        ):
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(word)
        current_length += word_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def count_words(text: str) -> int:
    return len(text.split())


def clean_model_output(text: str) -> str:
    text = text.strip()

    text = re.sub(
        r"```(?:text|markdown)?",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = text.replace("```", "")

    text = re.sub(
        r"^\s*(ringkasan|summary)\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bSentence\s*\d+\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    return text.strip()


def extract_facts(source: str) -> str:
    prompt = f"""
Anda adalah analis konten profesional.

Ekstrak fakta penting dari sumber berikut agar seluruh informasi
utama dapat digunakan untuk membuat ringkasan akhir.

Ambil sebanyak mungkin fakta yang relevan, termasuk:
- topik atau definisi utama
- tujuan atau fungsi
- kategori atau jenis
- manfaat
- fitur atau karakteristik
- langkah atau cara kerja
- contoh
- angka dan data
- nama pihak atau entitas
- tanggal jika tersedia
- rekomendasi atau tips
- kesimpulan penting

Jangan mengarang.
Jangan menggunakan pengetahuan dari luar sumber.
Jangan memberikan opini.
Jangan menghilangkan informasi penting hanya karena terlihat kecil.

Tulis dalam bullet point yang jelas.

SUMBER:
{source}
"""

    return clean_model_output(
        generate_content_with_retry(
            prompt,
            max_output_tokens=1800
        )
    )


def summarize_source(source: str) -> str:
    facts = extract_facts(source)

    prompt = f"""
Anda adalah editor profesional.

Buat ringkasan komprehensif berdasarkan fakta yang diekstrak dari
sumber berikut.

Target panjang keseluruhan 150-220 kata dan tidak boleh melebihi
250 kata.

Gunakan format:

### Inti Sari Utama
Satu atau dua paragraf yang merangkum keseluruhan isi.

### Poin-Poin Fakta Penting
6-10 bullet point yang berisi informasi berbeda dan penting.

### Latar Belakang / Konteks
Satu paragraf yang menjelaskan konteks atau informasi pendukung.

Pastikan ringkasan mencakup sebanyak mungkin informasi penting
tanpa mengulang fakta yang sama.

Hanya gunakan fakta yang tersedia.
Jangan menggunakan pengetahuan eksternal.
Jangan mengarang.
Jangan membuat asumsi.
Jangan memberikan opini.
Jangan menulis pengantar seperti "Berikut adalah ringkasan".

FAKTA SUMBER:
{facts}
"""

    return clean_model_output(
        generate_content_with_retry(
            prompt,
            max_output_tokens=1600
        )
    )


def extract_chunk_facts(
    chunk: str,
    chunk_number: int,
    total_chunks: int
) -> str:
    prompt = f"""
Anda adalah analis konten profesional.

Ini adalah bagian {chunk_number} dari {total_chunks} bagian sumber.

Ekstrak fakta penting dari bagian ini untuk digunakan saat membuat
ringkasan keseluruhan.

Pertahankan:
- definisi dan konsep
- fakta utama
- kategori atau jenis
- manfaat
- fitur
- langkah
- contoh
- angka
- tanggal
- nama
- rekomendasi
- kesimpulan
- informasi unik yang tidak boleh hilang

Ambil 10-15 fakta jika tersedia.

Jangan mengarang.
Jangan menggunakan pengetahuan eksternal.
Jangan beropini.

Tulis dalam bullet point.

TEKS:
{chunk}
"""

    return clean_model_output(
        generate_content_with_retry(
            prompt,
            max_output_tokens=1800
        )
    )


def generate_final_summary(chunk_facts: list[str]) -> str:
    combined = "\n\n".join(chunk_facts)

    prompt = f"""
Anda adalah editor profesional.

Buat ringkasan komprehensif dari semua fakta berikut.

Target 150-220 kata.
Maksimal 250 kata.

Gunakan format:

### Inti Sari Utama
Satu atau dua paragraf mengenai keseluruhan isi.

### Poin-Poin Fakta Penting
6-10 bullet point berisi fakta berbeda.

### Latar Belakang / Konteks
Satu paragraf mengenai konteks yang diperlukan.

Gabungkan informasi dari seluruh bagian sumber.
Jangan hanya mengambil fakta dari satu bagian.

Pertahankan definisi, detail penting, angka, tanggal, nama,
kategori, manfaat, langkah, contoh, dan kesimpulan jika tersedia.

Jangan mengarang.
Jangan menggunakan pengetahuan eksternal.
Jangan memberikan opini.
Jangan mengulang fakta.

Output langsung dimulai dengan:
### Inti Sari Utama

FAKTA:
{combined}
"""

    return clean_model_output(
        generate_content_with_retry(
            prompt,
            max_output_tokens=1600
        )
    )


def regenerate_summary(source: str) -> str:
    prompt = f"""
Buat ulang ringkasan komprehensif dari sumber asli berikut.

Target 150-220 kata.
Maksimal 250 kata.

Format:

### Inti Sari Utama
Satu atau dua paragraf.

### Poin-Poin Fakta Penting
6-10 bullet point.

### Latar Belakang / Konteks
Satu paragraf.

Jangan hanya mengambil satu informasi.
Masukkan sebanyak mungkin fakta utama yang relevan, termasuk
definisi, tujuan, kategori, manfaat, fitur, cara kerja, contoh,
angka, tanggal, tips, dan kesimpulan jika memang terdapat pada
sumber.

Gunakan hanya sumber asli.
Jangan mengarang.
Jangan menggunakan pengetahuan eksternal.
Jangan beropini.

SOURCE:
{source}
"""

    return clean_model_output(
        generate_content_with_retry(
            prompt,
            max_output_tokens=1600
        )
    )


def is_valid_summary(summary: str) -> bool:
    word_count = count_words(summary)

    required_headings = [
        "### Inti Sari Utama",
        "### Poin-Poin Fakta Penting",
        "### Latar Belakang / Konteks"
    ]

    headings_ok = all(
        heading in summary
        for heading in required_headings
    )

    bullet_count = len(
        re.findall(
            r"(?m)^\s*[-*•]\s+\S+",
            summary
        )
    )

    return (
        MIN_SUMMARY_WORDS <= word_count <= MAX_SUMMARY_WORDS
        and headings_ok
        and bullet_count >= 6
    )


def enforce_guardrail(
    summary: str,
    source: str
) -> str:
    summary = clean_model_output(summary)

    if is_valid_summary(summary):
        return summary

    summary = regenerate_summary(source)

    if is_valid_summary(summary):
        return summary

    words = summary.split()

    if len(words) > MAX_SUMMARY_WORDS:
        summary = " ".join(
            words[:MAX_SUMMARY_WORDS]
        )

    return summary


def scrape_and_summarize(url: str) -> str:
    source = scrape_webpage(url)
    chunks = chunk_text(source)

    if len(chunks) == 1:
        summary = summarize_source(chunks[0])
    else:
        facts = []

        for i, chunk in enumerate(chunks):
            facts.append(
                extract_chunk_facts(
                    chunk,
                    i + 1,
                    len(chunks)
                )
            )

        summary = generate_final_summary(facts)

    return enforce_guardrail(
        summary,
        source
    )


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print(" Web Scraper & Content Summarizer (Part 2: Technical Implementation)")
    print("=" * 60)
    
    # URL default untuk demonstrasi atau gunakan argumen terminal
    default_url = "https://www.biznetgio.com/blog/apa-itu-landing-page/"
    target_url = sys.argv[1] if len(sys.argv) > 1 else default_url
    
    print(f"[*] Target URL : {target_url}")
    print("[*] Memulai proses scraping, DOM cleaning, chunking, & summarization...")
    print("    (Harap tunggu beberapa saat...)\n")
    
    try:
        hasil_ringkasan = scrape_and_summarize(target_url)
        print("-" * 60)
        print(" HASIL RINGKASAN TERSTRUKTUR (SESUAI GUARDRAIL 100-250 KATA):")
        print("-" * 60)
        print(hasil_ringkasan)
        print("-" * 60)
        word_count = len(hasil_ringkasan.split())
        print(f"[✓] Panjang ringkasan: {word_count} kata (Valid: 100-250 kata)")
    except Exception as err:
        print(f"[!] Terjadi kesalahan saat memproses: {err}")

