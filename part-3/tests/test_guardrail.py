import unittest
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from langchain_core.messages import HumanMessage
from src.nodes.guard import scope_guard_node, reject_node, POLITE_REJECTION_TEMPLATE

class TestGuardrail(unittest.TestCase):
    def test_rejection_format(self):
        state = {"rejection_message": None}
        result = reject_node(state)
        self.assertIn("messages", result)
        msg = result["messages"][0]
        self.assertIn("Mohon maaf", msg.content)
        self.assertIn("Asisten Penulisan Karya Ilmiah", msg.content)

    def test_small_talk_allowed(self):
        # Sapaan santai dan formal harus lolos (in-scope)
        for text in ["hi", "Hi", "halo", "selamat pagi", "apa kabar?", "kamu siapa?", "bisa bantu apa saja?", "terima kasih"]:
            res = scope_guard_node({"messages": [HumanMessage(content=text)]})
            self.assertTrue(res["is_in_scope"], f"'{text}' harus dianggap in-scope (basa-basi diizinkan)")
            self.assertIsNone(res["rejection_message"])

    def test_academic_allowed(self):
        # Topik karya ilmiah harus lolos (in-scope)
        for text in [
            "Bagaimana format penulisan kutipan langsung menurut pedoman?",
            "Bagaimana sistematika bab 1 skripsi?",
            "Jelaskan aturan penulisan daftar rujukan buku."
        ]:
            res = scope_guard_node({"messages": [HumanMessage(content=text)]})
            self.assertTrue(res["is_in_scope"], f"'{text}' harus lolos sebagai topik akademik")

    def test_out_of_scope_rejected(self):
        # Pertanyaan faktual harian di luar karya ilmiah harus ditolak
        for text in [
            "jalan menuju surabaya lewat mana",
            "makanan enak dekat sini apa aja",
            "resep bumbu nasi goreng enak",
            "besok cuaca di jakarta hujan tidak?",
            "skor pertandingan sepak bola kemarin malam"
        ]:
            res = scope_guard_node({"messages": [HumanMessage(content=text)]})
            self.assertFalse(res["is_in_scope"], f"'{text}' harus ditolak sebagai out-of-scope")
            self.assertIsNotNone(res["rejection_message"])
            self.assertIn("Mohon maaf", res["rejection_message"])

if __name__ == "__main__":
    unittest.main()
