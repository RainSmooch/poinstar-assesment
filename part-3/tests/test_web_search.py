import unittest
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.tools.web_search import search_web

class TestWebSearch(unittest.TestCase):
    def test_search_web_apa(self):
        results = search_web("format sitasi APA edisi 7", max_results=2)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0, "Harus menemukan hasil penelusuran web")
        first = results[0]
        self.assertIn("title", first)
        self.assertIn("href", first)
        self.assertIn("body", first)

if __name__ == "__main__":
    unittest.main()
