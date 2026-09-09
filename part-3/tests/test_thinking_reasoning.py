import unittest
from langchain_core.messages import HumanMessage
from src.nodes.thinking import ToolDecision, thinking_node, fallback_heuristic_decision
from src.nodes.tools_node import retrieve_tools_node

class TestThinkingReasoning(unittest.TestCase):
    def test_tool_decision_schema(self):
        decision = ToolDecision(
            thought="Perlu memeriksa pasal kutipan langsung",
            need_kb=True,
            kb_query="kutipan langsung 40 kata",
            need_web=False,
            web_query=None
        )
        self.assertTrue(decision.need_kb)
        self.assertFalse(decision.need_web)
        self.assertEqual(decision.kb_query, "kutipan langsung 40 kata")
        self.assertIsNone(decision.web_query)

    def test_fallback_heuristic_greetings(self):
        res = fallback_heuristic_decision("halo selamat pagi")
        self.assertFalse(res["need_kb"])
        self.assertFalse(res["need_web"])
        self.assertIsNone(res["kb_query"])

    def test_fallback_heuristic_academic(self):
        res = fallback_heuristic_decision("bagaimana cara menulis kutipan langsung?")
        self.assertTrue(res["need_kb"])
        self.assertIsNotNone(res["kb_query"])

    def test_fallback_heuristic_web_trigger(self):
        res = fallback_heuristic_decision("apa aturan penulisan sitasi apa style edisi 7?")
        self.assertTrue(res["need_web"])
        self.assertIsNotNone(res["web_query"])

    def test_retrieve_tools_zero_waste_when_no_tools_needed(self):
        state = {
            "need_kb": False,
            "kb_query": None,
            "need_web": False,
            "web_query": None
        }
        res = retrieve_tools_node(state)
        self.assertEqual(len(res["kb_results"]), 0)
        self.assertEqual(len(res["web_results"]), 0)

    def test_retrieve_tools_when_kb_needed(self):
        state = {
            "need_kb": True,
            "kb_query": "kutipan langsung",
            "need_web": False,
            "web_query": None
        }
        res = retrieve_tools_node(state)
        self.assertGreater(len(res["kb_results"]), 0)
        self.assertEqual(len(res["web_results"]), 0)

    def test_thinking_node_live_or_fallback(self):
        state = {
            "messages": [HumanMessage(content="Bagaimana aturan penomoran bab skripsi?")]
        }
        res = thinking_node(state)
        self.assertIn("thinking_process", res)
        self.assertIn("need_kb", res)
        self.assertIn("kb_query", res)
        self.assertIn("need_web", res)
        self.assertIn("web_query", res)
        self.assertTrue(res["need_kb"])

if __name__ == "__main__":
    unittest.main()
