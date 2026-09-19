"""Sanity tests for the KYLA v0.2 framework."""

import unittest

from kyla.agents import list_agents
from kyla.r13_gate import check
from kyla.sophia import route


class KylaAgentTests(unittest.TestCase):
    def test_registry_has_seven_agents(self):
        self.assertEqual(len(list_agents()), 7)

    def test_r13_flags_fake_api_key(self):
        report = check("draft config: sk-FAKE123")
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["secrets"])

    def test_sophia_routes_trade_to_quant_domain(self):
        decision = route("Please review this trade setup")
        self.assertEqual(decision["agent"], "quant")
        self.assertEqual(decision["agent_id"], "shell")
        self.assertEqual(decision["domain"], "trading")


if __name__ == "__main__":
    unittest.main()
