import unittest
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.tools.kb_search import search_knowledge_base

class TestKnowledgeBaseSearch(unittest.TestCase):
    def test_kutipan_search(self):
        results = search_knowledge_base("kutipan langsung 40 kata", top_k=2)
        self.assertGreater(len(results), 0, "Harus menemukan hasil pencarian kutipan")
        chapters = [r["chapter"] for r in results]
        has_bab5 = any("BAB 5" in ch for ch in chapters)
        self.assertTrue(has_bab5, f"Pencarian kutipan harus merujuk Bab 5, ditemukan: {chapters}")

    def test_sistematika_skripsi(self):
        results = search_knowledge_base("sistematika bagian inti skripsi", top_k=2)
        self.assertGreater(len(results), 0, "Harus menemukan sistematika skripsi")
        chapters = [r["chapter"] for r in results]
        has_bab3 = any("BAB 3" in ch for ch in chapters)
        self.assertTrue(has_bab3, f"Sistematika skripsi harus merujuk Bab 3, ditemukan: {chapters}")

    def test_penjilidan_kertas(self):
        results = search_knowledge_base("ukuran kertas margin pencetakan", top_k=2)
        self.assertGreater(len(results), 0, "Harus menemukan aturan pencetakan")
        chapters = [r["chapter"] for r in results]
        has_bab9 = any("BAB 9" in ch for ch in chapters)
        self.assertTrue(has_bab9, f"Aturan kertas harus merujuk Bab 9, ditemukan: {chapters}")

if __name__ == "__main__":
    unittest.main()
