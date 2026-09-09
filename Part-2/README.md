# Web Scraper & Content Summarizer

<div align="center">

<p align="center">
  <a href="../README.md">⬅️ Kembali ke Repositori Utama</a> •
  <a href="web_scraper.py">💻 Source Code: web_scraper.py</a> •
  <a href="../system_architecture_summary.pdf">📄 Dokumen Ringkasan Eksekutif PDF</a>
</p>

</div>

---

Aplikasi Python sederhana untuk mengambil konten teks dari sebuah website, membersihkan HTML, menangani halaman dinamis, memproses konten panjang, lalu menghasilkan ringkasan menggunakan Gemini.

## Tujuan

Project ini dibuat untuk menangani tiga masalah utama pada proses scraping dan summarization:

1. Halaman web kompleks atau dinamis tidak selalu dapat diambil dengan HTTP request biasa.
2. Konten yang sangat panjang dapat melebihi batas input model atau menyebabkan informasi di bagian tertentu hilang.
3. Output model dapat terlalu pendek, terlalu panjang, atau tidak mengikuti format yang diharapkan.

## Arsitektur

```text
URL
 ↓
Requests
 ↓
DOM Cleaning
 ↓
Konten cukup?
 ├── Ya → lanjut
 └── Tidak → Playwright
 ↓
Extract Text
 ↓
Chunking
 ↓
┌───────────────────────────────┐
│ 1 chunk                       │
│ → langsung diringkas          │
└───────────────────────────────┘

atau

┌───────────────────────────────┐
│ >1 chunk                      │
│ → extract fakta tiap chunk    │
│ → gabungkan fakta             │
│ → final summarization         │
└───────────────────────────────┘
 ↓
Summary Guardrail
 ↓
Output
```

## Solusi yang Digunakan

### 1. Web Scraping

`Requests` digunakan sebagai scraper utama karena lebih ringan dan cepat untuk halaman HTML biasa.

Jika hasil extraction terlalu sedikit atau Requests gagal, program menggunakan `Playwright` sebagai fallback untuk halaman yang membutuhkan JavaScript rendering.

### 2. DOM Cleaning

`BeautifulSoup` digunakan untuk membersihkan elemen yang tidak relevan terhadap isi utama halaman, seperti `script`, `style`, `nav`, `footer`, `header`, `aside`, `form`, `noscript`, dan `iframe`.

Program memprioritaskan container berikut:

```text
<article>
<main>
<body>
```

### 3. Long Content Handling

Konten panjang tidak dipotong secara langsung. Teks dibagi menjadi beberapa chunk berdasarkan jumlah karakter sehingga bagian akhir halaman tidak langsung hilang.

Untuk halaman yang hanya terdiri dari satu chunk, source asli langsung digunakan dalam proses summarization agar tidak terjadi information loss akibat summarization bertingkat.

Untuk halaman yang terdiri dari beberapa chunk, setiap chunk diekstrak menjadi fakta penting terlebih dahulu. Fakta dari seluruh chunk kemudian digunakan untuk membuat ringkasan akhir.

### 4. Summary Guardrail

Output model divalidasi secara programmatic dengan batas:

```text
Minimum: 100 kata
Target:   150–220 kata
Maximum: 250 kata
```

Output juga diperiksa berdasarkan struktur:

```text
### Inti Sari Utama
### Poin-Poin Fakta Penting
### Latar Belakang / Konteks
```

Jika hasil terlalu pendek, terlalu panjang, atau struktur minimum tidak terpenuhi, program meminta model membuat ulang ringkasan berdasarkan source asli.

### 5. Retry untuk API Error

Program memiliki retry otomatis untuk error sementara seperti `503 UNAVAILABLE` dan `429 RESOURCE_EXHAUSTED`, dengan jeda bertahap sampai tiga percobaan.

## Requirements

Python 3.10 atau lebih baru direkomendasikan.

Install dependency:

```bash
pip install -r requirements.txt
```

Kemudian install browser Playwright:

```bash
playwright install chromium
```

## API Key

Buat file `.env` pada folder project:

```env
GEMINI_API_KEY=API_KEY_KAMU
```

Jangan menulis API key langsung di source code dan jangan commit file `.env` ke repository.

Tambahkan ke `.gitignore`:

```gitignore
.env
__pycache__/
```

## Struktur Project

```text
.
├── web_scraper.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Cara Menggunakan

File `web_scraper.py` menyediakan fungsi utama:

```python
scrape_and_summarize(url)
```

Contoh:

```python
from web_scraper import scrape_and_summarize

url = "https://www.biznetgio.com/blog/apa-itu-landing-page/"

hasil = scrape_and_summarize(url)
print(hasil)
```

Output berbentuk:

```text
### Inti Sari Utama
...

### Poin-Poin Fakta Penting
- ...
- ...
- ...
- ...
- ...
- ...

### Latar Belakang / Konteks
...
```

## Failure Points dan Trade-offs

### Requests vs Playwright

Requests lebih cepat dan ringan, tetapi tidak mengeksekusi JavaScript. Playwright lebih mampu menangani halaman dinamis, tetapi membutuhkan browser dan resource yang lebih besar. Karena itu Requests digunakan sebagai primary scraper dan Playwright hanya sebagai fallback.

### Chunking vs Full Context

Chunking mengurangi risiko input terlalu besar dan menjaga seluruh konten tetap diproses. Trade-off-nya adalah proses membutuhkan lebih banyak pemanggilan model dan dapat meningkatkan penggunaan token.

### Prompt Guardrail vs Programmatic Guardrail

Instruksi pada prompt membantu model mengikuti format dan batas panjang, tetapi tidak memberikan jaminan. Karena itu hasil model tetap diperiksa dengan programmatic validation berdasarkan jumlah kata dan struktur output.

### Hallucination

Prompt membatasi model agar hanya menggunakan informasi yang terdapat pada source. Pendekatan ini mengurangi risiko hallucination, tetapi tidak dianggap sebagai jaminan absolut.

## Limitations

Project ini berfokus pada ekstraksi teks. Beberapa jenis konten mungkin memerlukan pendekatan tambahan, misalnya data yang baru muncul setelah interaksi pengguna tertentu, konten yang hanya tersedia melalui API khusus, tabel atau struktur data yang sangat kompleks, dokumen PDF yang ditampilkan melalui viewer, dan website dengan proteksi anti-bot.

## Assessment Part 2

| Problem | Solution |
|---|---|
| Complex / dynamic pages | Requests + Playwright fallback |
| Long content | Chunking + fact extraction |
| Summary terlalu panjang/tidak sesuai | Programmatic summary guardrail |

## Panduan Menjalankan (Running Locally)

Dari root repositori `assesment`:

```bash
# 1. Masuk ke direktori Part-2
cd Part-2

# 2. Pasang dependensi pustaka
pip install -r requirements.txt

# 3. Pasang browser Playwright Chromium (untuk fallback halaman dinamis)
playwright install chromium

# 4. Salin templat konfigurasi .env
cp .env.example .env
```

Isi kunci API pada `.env`:
```env
GEMINI_API_KEY=AIzaSy...kunci_api_gemini_anda
```

### Cara Eksekusi:

**Opsi 1: Menjalankan Langsung via Terminal CLI (Demo Bawaan)**
```bash
python web_scraper.py
```

**Opsi 2: Menjalankan dengan URL Kustom Pilihan Anda**
```bash
python web_scraper.py "https://id.wikipedia.org/wiki/Kecerdasan_buatan"
```

**Opsi 3: Diimpor sebagai Modul Python**
```python
from web_scraper import scrape_and_summarize

url = "https://www.biznetgio.com/blog/apa-itu-landing-page/"
hasil = scrape_and_summarize(url)
print(hasil)
```
*(Catatan: Perintah `python web-scraper.py` juga tetap didukung untuk kompatibilitas penuh).*

## License

Project ini dibuat untuk keperluan technical assessment.

