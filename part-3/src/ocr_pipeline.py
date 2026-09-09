import asyncio
import io
import json
import re
from pathlib import Path
from PIL import Image
import fitz
import winocr

from src.config import PDF_PATH, CACHE_DIR, CHUNKS_PATH

CHAPTER_MAP = [
    (14, 18, "BAB 1 JENIS-JENIS KARYA ILMIAH"),
    (19, 21, "BAB 2 PROPOSAL TUGAS AKHIR, SKRIPSI, TESIS, DAN DISERTASI"),
    (22, 31, "BAB 3 SISTEMATIKA DAN ISI TUGAS AKHIR, SKRIPSI, TESIS, DAN DISERTASI"),
    (32, 40, "BAB 4 SISTEMATIKA DAN ISI ARTIKEL JURNAL ILMIAH, MAKALAH, DAN LAPORAN PENELITIAN"),
    (41, 51, "BAB 5 PENGUTIPAN, PERUJUKAN, DAN PENULISAN DAFTAR RUJUKAN"),
    (52, 62, "BAB 6 KEBAHASAAN"),
    (63, 63, "BAB 7 ETIKA PENULISAN KARYA ILMIAH"),
    (64, 69, "BAB 8 PENATAAN ISI KARYA ILMIAH"),
    (70, 74, "BAB 9 PENCETAKAN DAN PENJILIDAN"),
    (75, 75, "DAFTAR PUSTAKA"),
    (76, 135, "LAMPIRAN CONTOH FORMAT DAN TEMPLATE")
]

def get_chapter_title(pdf_page: int) -> str:
    if pdf_page < 14:
        return "BAGIAN AWAL (KATA PENGANTAR & DAFTAR ISI)"
    for start, end, title in CHAPTER_MAP:
        if start <= pdf_page <= end:
            return title
    return "DOKUMEN PEDOMAN UM 2017"

async def extract_page_ocr(doc, page_idx: int) -> str:
    cache_file = CACHE_DIR / f"page_{page_idx + 1:03d}.txt"
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")
    
    page = doc[page_idx]
    pix = page.get_pixmap(dpi=150)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    res = await winocr.recognize_pil(img, "en")
    text = res.text.strip()
    
    # Simpan ke cache
    cache_file.write_text(text, encoding="utf-8")
    return text

async def run_ocr_pipeline(force: bool = False) -> list[dict]:
    if CHUNKS_PATH.exists() and not force:
        print(f"[OCR] Membaca chunks yang sudah diproses dari: {CHUNKS_PATH}")
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
            
    print(f"[OCR] Memulai ekstraksi OCR dokumen: {PDF_PATH}")
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    chunks = []
    
    for i in range(total_pages):
        pdf_page = i + 1
        text = await extract_page_ocr(doc, i)
        chapter = get_chapter_title(pdf_page)
        book_page = pdf_page - 13 if pdf_page >= 14 else None
        
        # Bersihkan spasi berlebih
        cleaned_text = re.sub(r"\s+", " ", text).strip()
        
        if len(cleaned_text) > 20:
            chunk = {
                "id": f"chunk_p{pdf_page:03d}",
                "pdf_page": pdf_page,
                "book_page": book_page,
                "chapter": chapter,
                "text": cleaned_text
            }
            chunks.append(chunk)
            
        if (pdf_page) % 20 == 0 or pdf_page == total_pages:
            print(f"[OCR] Progres: {pdf_page}/{total_pages} halaman selesai...")
            
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
        
    print(f"[OCR] Sukses! Sebanyak {len(chunks)} chunks disimpan di {CHUNKS_PATH}")
    return chunks

if __name__ == "__main__":
    asyncio.run(run_ocr_pipeline())
