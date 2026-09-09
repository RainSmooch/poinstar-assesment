from typing import List, Dict, Any

def search_web(query: str, max_results: int = 4) -> List[Dict[str, Any]]:
    # Tambahkan pembatas kata kunci akademik agar fokus pada kaidah penulisan
    academic_query = f"{query} kaidah penulisan ilmiah sitasi"
    results = []
    
    # Coba gunakan ddgs
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(academic_query, max_results=max_results))
            for item in raw_results:
                results.append({
                    "title": item.get("title", ""),
                    "href": item.get("href", ""),
                    "body": item.get("body", "")
                })
    except Exception as e:
        # Fallback tanpa kata kunci tambahan jika terlalu spesifik
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))
                for item in raw_results:
                    results.append({
                        "title": item.get("title", ""),
                        "href": item.get("href", ""),
                        "body": item.get("body", "")
                    })
        except Exception:
            pass
            
    return results

def format_web_context(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "Tidak ada informasi eksternal dari penelusuran web."
        
    formatted = []
    for idx, r in enumerate(results, 1):
        formatted.append(f"[{idx}] {r['title']}\nTautan: {r['href']}\nRingkasan: {r['body']}")
    return "\n\n".join(formatted)
