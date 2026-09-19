"""Unit tests for the trading-cost defaults and break-even helper."""

import unittest

from quant.costs import DEFAULT_COSTS, break_even_probability


class CostModelTests(unittest.TestCase):
    def test_symmetric_break_even_formula(self):
        self.assertAlmostEqual(break_even_probability(0.2, 1.0), 0.6)
        self.assertAlmostEqual(break_even_probability(0.0, 1.0), 0.5)

    def test_requested_pair_defaults(self):
        expected_pips = {
            "GBPUSD": 1.6,
            "USDJPY": 1.6,
            "GBPJPY": 3.45,
        }
        for symbol, spread in expected_pips.items():
            with self.subTest(symbol=symbol):
                model = DEFAULT_COSTS[symbol]
                self.assertEqual(model.spread, spread)
                self.assertEqual(model.spread_unit, "pips")

        xauusd = DEFAULT_COSTS["XAUUSD"]
        self.assertIsNone(xauusd.spread)
        self.assertEqual(xauusd.spread_unit, "price units")
        self.assertIn("TBD", xauusd.notes)

        nas100 = DEFAULT_COSTS["NAS100_OANDA"]
        self.assertEqual(nas100.spread, 1.1)
        self.assertEqual(nas100.spread_unit, "points")
        self.assertEqual(nas100.point_value, 20.0)

    def test_binance_sol_fee_tiers_and_bnb_note(self):
        expected_rates = {
            "BINANCE_SOL_SPOT": 0.001,
            "BINANCE_SOL_FUTURES": 0.0005,
            "BINANCE_SOL_MAKER": 0.0002,
        }
        for symbol, rate in expected_rates.items():
            with self.subTest(symbol=symbol):
                model = DEFAULT_COSTS[symbol]
                self.assertIsNone(model.spread)
                self.assertEqual(model.spread_unit, "price units")
                self.assertEqual(model.commission_rate_per_side, rate)
                self.assertIn("BNB discount", model.notes)


if __name__ == "__main__":
    unittest.main()
