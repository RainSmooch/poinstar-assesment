import unittest
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from langchain_core.messages import HumanMessage
from src.utils import get_current_time_info, extract_clean_text
from src.nodes.guard import scope_guard_node
from src.graph import get_agent_graph

class TestTimeAwareness(unittest.TestCase):
    def test_get_current_time_info(self):
        info = get_current_time_info()
        self.assertIn("day_name", info)
        self.assertIn("full_date_str", info)
        self.assertIn("year", info)
        self.assertIn("greeting", info)
        self.assertIn("academic_year", info)
        self.assertGreaterEqual(info["year"], 2024)
        self.assertTrue(any(g in info["greeting"] for g in ["pagi", "siang", "sore", "malam"]))

    def test_guardrail_accepts_time_queries(self):
        time_queries = [
            "sekarang hari apa?",
            "tanggal berapa hari ini?",
            "sekarang tahun berapa?",
            "jam berapa sekarang?",
            "tahun akademik sekarang apa?"
        ]
        for q in time_queries:
            res = scope_guard_node({"messages": [HumanMessage(content=q)]})
            self.assertTrue(res["is_in_scope"], f"'{q}' harus dianggap in-scope untuk kesadaran waktu")
            self.assertIsNone(res["rejection_message"])

    def test_agent_knows_current_year(self):
        g = get_agent_graph()
        info = get_current_time_info()
        current_year = str(info["year"])
        
        cfg = {"configurable": {"thread_id": "test_time_query"}}
        res = g.invoke({"messages": [HumanMessage(content="Sekarang tahun berapa dan hari apa?")]}, config=cfg)
        answer = extract_clean_text(res["messages"][-1].content)
        
        self.assertIn(current_year, answer, f"Jawaban harus menyebutkan tahun saat ini ({current_year}): {answer}")

if __name__ == "__main__":
    unittest.main()
