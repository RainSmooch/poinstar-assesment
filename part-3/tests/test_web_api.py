import unittest
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
from web_app import app

class TestWebAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_index_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("UNIVERSITAS NEGERI MALANG", res.text)
        self.assertIn("The Learning University", res.text)
        self.assertIn("Pedoman Penulisan Karya Ilmiah", res.text)

    def test_api_time(self):
        res = self.client.get("/api/time")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("year", data)
        self.assertIn("day_name", data)
        self.assertIn("academic_year", data)

    def test_api_chapters(self):
        res = self.client.get("/api/pedoman/chapters")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("chapters", data)
        self.assertEqual(len(data["chapters"]), 10)

    def test_api_pedoman_search(self):
        res = self.client.get("/api/pedoman/search?q=kutipan")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("results", data)
        self.assertGreater(len(data["results"]), 0)

    def test_api_delete_thread(self):
        thread_id = "test_hapus_sesi_unit"
        res = self.client.delete(f"/api/threads/{thread_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["thread_id"], thread_id)

    def test_api_delete_thread_empty(self):
        res = self.client.delete("/api/threads/%20")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "error")

if __name__ == "__main__":
    unittest.main()
