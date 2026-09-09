import unittest
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from src.graph import build_graph

class TestGraphFlow(unittest.TestCase):
    def test_rejection_flow(self):
        graph = build_graph(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "test_reject"}}
        
        # Pesan di luar ruang lingkup
        input_state = {
            "messages": [HumanMessage(content="Bagaimana cara memasak rendang daging sapi empuk?")]
        }
        
        result = graph.invoke(input_state, config=config)
        self.assertIn("messages", result)
        last_msg = result["messages"][-1]
        self.assertIsInstance(last_msg, AIMessage)
        self.assertIn("Mohon maaf", last_msg.content)
        self.assertIn("Asisten Penulisan Karya Ilmiah", last_msg.content)

    def test_memory_thread_persistence(self):
        checkpointer = MemorySaver()
        graph = build_graph(checkpointer=checkpointer)
        thread_id = "test_memory_thread"
        config = {"configurable": {"thread_id": thread_id}}

        # Turn 1
        graph.invoke(
            {"messages": [HumanMessage(content="Tolong beritahu cara membuat kue bolu?")]},
            config=config
        )

        # Cek state memory di checkpointer
        checkpoint_state = graph.get_state(config)
        self.assertGreaterEqual(len(checkpoint_state.values["messages"]), 2)

if __name__ == "__main__":
    unittest.main()
