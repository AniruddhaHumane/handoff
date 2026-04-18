import unittest

from handoff.compiler import compile_agent_summary, compile_get_handoff_markdown


class HandoffRenderingTest(unittest.TestCase):
    def test_compile_agent_summary_contains_core_sections(self) -> None:
        text = compile_agent_summary(
            {
                "agent": "A",
                "summary": "Done work",
                "next_action": "Do next",
            }
        )

        self.assertIn("# Agent Handoff: A", text)
        self.assertIn("## Summary", text)
        self.assertIn("## Next Action", text)

    def test_compile_get_handoff_render_contains_primary_and_appendix(self) -> None:
        text = compile_get_handoff_markdown(
            {
                "primary_agent": "B",
                "summary": "new summary",
                "next_action": "new next",
                "sources": ["B", "A"],
                "snapshots": [
                    {
                        "agent": "B",
                        "summary": "new summary",
                        "next_action": "new next",
                    },
                    {
                        "agent": "A",
                        "summary": "old summary",
                        "next_action": "old next",
                    },
                ],
            }
        )

        self.assertIn("# Get Handoff", text)
        self.assertIn("## Primary Context", text)
        self.assertIn("## Additional Agent Snapshots", text)
        self.assertIn("Agent: B", text)


if __name__ == "__main__":
    unittest.main()
