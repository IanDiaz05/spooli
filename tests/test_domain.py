"""Characterisation tests for the business logic in core.py."""

import sys
import tempfile
import unittest
import warnings
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import core
import db


def setUpModule():
    # db.py leaves sqlite connections open after its "with" blocks; the runner
    # enables the 'default' filter, which surfaces their ResourceWarning noise.
    warnings.filterwarnings(
        "ignore", message="unclosed database", category=ResourceWarning
    )


class CalculateCostsTests(unittest.TestCase):
    """core.calculate_costs must round every monetary field to 4 decimals."""

    def test_known_simple_values(self):
        result = core.calculate_costs(
            grams=10.0,
            duration_seconds=3600,
            spool_price=20.0,
            spool_initial_weight=1000.0,
            printer_watts=200.0,
            kwh_cost=0.2,
        )
        self.assertEqual(result.filament_cost, 0.2)
        self.assertEqual(result.electricity_cost, 0.04)
        self.assertEqual(result.total_cost, 0.24)

    def test_values_are_rounded_to_four_decimals(self):
        result = core.calculate_costs(
            grams=33.33,
            duration_seconds=7325,
            spool_price=19.99,
            spool_initial_weight=1000.0,
            printer_watts=150.0,
            kwh_cost=0.15,
        )
        self.assertEqual(result.filament_cost, 0.6663)
        self.assertEqual(result.electricity_cost, 0.0458)
        self.assertEqual(result.total_cost, 0.712)

    def test_every_field_carries_at_most_four_decimals(self):
        result = core.calculate_costs(7.7, 9999, 13.37, 750.0, 123.4, 0.23)
        for value in (result.filament_cost, result.electricity_cost, result.total_cost):
            self.assertEqual(round(value, 4), value)

    def test_zero_duration_yields_zero_electricity_cost(self):
        result = core.calculate_costs(10.0, 0, 20.0, 1000.0, 200.0, 0.2)
        self.assertEqual(result.electricity_cost, 0.0)
        self.assertEqual(result.filament_cost, result.total_cost)

    def test_rejects_negative_grams(self):
        with self.assertRaises(ValueError) as ctx:
            core.calculate_costs(-1.0, 0, 1.0, 1000.0, 100.0, 0.1)
        self.assertEqual(str(ctx.exception), "grams cannot be negative")

    def test_rejects_negative_duration(self):
        with self.assertRaises(ValueError) as ctx:
            core.calculate_costs(1.0, -1, 1.0, 1000.0, 100.0, 0.1)
        self.assertEqual(str(ctx.exception), "duration_seconds cannot be negative")

    def test_rejects_negative_spool_price(self):
        with self.assertRaises(ValueError) as ctx:
            core.calculate_costs(1.0, 0, -0.01, 1000.0, 100.0, 0.1)
        self.assertEqual(str(ctx.exception), "spool_price cannot be negative")

    def test_rejects_non_positive_initial_weight(self):
        with self.assertRaises(ValueError) as ctx:
            core.calculate_costs(1.0, 0, 1.0, 0.0, 100.0, 0.1)
        self.assertEqual(
            str(ctx.exception), "spool_initial_weight must be greater than 0"
        )

    def test_rejects_negative_printer_watts(self):
        with self.assertRaises(ValueError) as ctx:
            core.calculate_costs(1.0, 0, 1.0, 1000.0, -5.0, 0.1)
        self.assertEqual(str(ctx.exception), "printer_watts cannot be negative")

    def test_rejects_negative_kwh_cost(self):
        with self.assertRaises(ValueError) as ctx:
            core.calculate_costs(1.0, 0, 1.0, 1000.0, 100.0, -0.1)
        self.assertEqual(str(ctx.exception), "kwh_cost cannot be negative")


class CalculateRefundTests(unittest.TestCase):
    """core.calculate_refund contracts for percent and gram-based refunds."""

    def test_percentage_failure_scales_consumption(self):
        result = core.calculate_refund(100.0, 40.0, is_percent=True)
        self.assertEqual(result.estimated_grams, 100.0)
        self.assertEqual(result.actual_consumption, 40.0)
        self.assertEqual(result.refund_grams, 60.0)

    def test_percentage_zero_refunds_everything(self):
        result = core.calculate_refund(50.0, 0.0, is_percent=True)
        self.assertEqual(result.actual_consumption, 0.0)
        self.assertEqual(result.refund_grams, 50.0)

    def test_percentage_hundred_refunds_nothing(self):
        result = core.calculate_refund(100.0, 100.0, is_percent=True)
        self.assertEqual(result.actual_consumption, 100.0)
        self.assertEqual(result.refund_grams, 0.0)

    def test_scale_grams_adjustment_uses_measured_weight(self):
        result = core.calculate_refund(100.0, 12.5, is_percent=False)
        self.assertEqual(result.actual_consumption, 12.5)
        self.assertEqual(result.refund_grams, 87.5)

    def test_consumption_and_refund_round_to_two_decimals(self):
        result = core.calculate_refund(100.0, 33.333, is_percent=False)
        self.assertEqual(result.actual_consumption, 33.33)
        self.assertEqual(result.refund_grams, 66.67)
        self.assertEqual(round(result.actual_consumption, 2), result.actual_consumption)
        self.assertEqual(round(result.refund_grams, 2), result.refund_grams)

    def test_rejects_consumption_above_initial_estimate(self):
        with self.assertRaises(ValueError) as ctx:
            core.calculate_refund(100.0, 120.0, is_percent=False)
        self.assertEqual(
            str(ctx.exception), "actual consumption cannot exceed estimated grams"
        )

    def test_rejects_percentage_above_one_hundred(self):
        with self.assertRaises(ValueError) as ctx:
            core.calculate_refund(100.0, 150.0, is_percent=True)
        self.assertEqual(
            str(ctx.exception), "failure percentage cannot exceed 100"
        )

    def test_rejects_negative_estimated_grams(self):
        with self.assertRaises(ValueError) as ctx:
            core.calculate_refund(-1.0, 10.0)
        self.assertEqual(str(ctx.exception), "estimated_grams cannot be negative")

    def test_rejects_negative_actual_usage(self):
        with self.assertRaises(ValueError) as ctx:
            core.calculate_refund(10.0, -1.0)
        self.assertEqual(str(ctx.exception), "actual_usage cannot be negative")


class SelectSpoolTests(unittest.TestCase):
    """core.select_spool ordering, manual selection and error contracts."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db_path = Path(tmp.name) / "spooli.db"
        db.init_db(self.db_path)
        self.spool_a = db.create_spool(
            "PLA", brand="A", remaining_weight_g=250.0, path=self.db_path
        )
        self.spool_b = db.create_spool(
            "PLA", brand="B", remaining_weight_g=120.0, path=self.db_path
        )
        self.spool_c = db.create_spool(
            "PLA", brand="C", remaining_weight_g=800.0, path=self.db_path
        )
        self.spool_petg = db.create_spool(
            "PETG", brand="P", remaining_weight_g=500.0, path=self.db_path
        )

    def test_compatible_matches_ordered_by_remaining_weight_ascending(self):
        result = core.select_spool("PLA", 100.0, db_path=self.db_path)
        self.assertEqual(result.selected_spool["id"], self.spool_b)
        self.assertEqual(
            [spool["id"] for spool in result.alternatives],
            [self.spool_a, self.spool_c],
        )

    def test_spool_with_exactly_required_weight_is_selected(self):
        result = core.select_spool("PLA", 800.0, db_path=self.db_path)
        self.assertEqual(result.selected_spool["id"], self.spool_c)
        self.assertEqual(result.alternatives, [])

    def test_selection_only_returns_matching_material(self):
        result = core.select_spool("PETG", 300.0, db_path=self.db_path)
        self.assertEqual(result.selected_spool["id"], self.spool_petg)

    def test_selection_excludes_spools_below_required_weight(self):
        result = core.select_spool("PLA", 300.0, db_path=self.db_path)
        self.assertEqual(result.selected_spool["id"], self.spool_c)
        self.assertEqual(result.alternatives, [])

    def test_manual_spool_hit_returns_that_spool(self):
        result = core.select_spool(
            "PLA", 100.0, manual_spool_id=self.spool_c, db_path=self.db_path
        )
        self.assertEqual(result.selected_spool["id"], self.spool_c)
        self.assertEqual(result.alternatives, [])

    def test_manual_spool_miss_raises_exact_error(self):
        with self.assertRaises(ValueError) as ctx:
            core.select_spool("PLA", 100.0, manual_spool_id=999, db_path=self.db_path)
        self.assertEqual(str(ctx.exception), "spool with id 999 does not exist")

    def test_manual_spool_material_mismatch_raises_exact_error(self):
        with self.assertRaises(ValueError) as ctx:
            core.select_spool(
                "PLA", 100.0, manual_spool_id=self.spool_petg, db_path=self.db_path
            )
        self.assertEqual(
            str(ctx.exception),
            f"spool {self.spool_petg} material mismatch: expected PLA, got PETG",
        )

    def test_manual_spool_insufficient_filament_raises_exact_error(self):
        with self.assertRaises(ValueError) as ctx:
            core.select_spool(
                "PLA", 900.0, manual_spool_id=self.spool_c, db_path=self.db_path
            )
        self.assertEqual(
            str(ctx.exception),
            f"spool {self.spool_c} has insufficient filament: "
            "800.0g remaining, 900.0g required",
        )

    def test_no_compatible_spool_raises_exact_error(self):
        with self.assertRaises(ValueError) as ctx:
            core.select_spool("NYLON", 100.0, db_path=self.db_path)
        self.assertEqual(
            str(ctx.exception),
            "no compatible spools found for material 'NYLON' "
            "with at least 100.0g remaining",
        )

    def test_negative_required_grams_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            core.select_spool("PLA", -1.0, db_path=self.db_path)
        self.assertEqual(str(ctx.exception), "required_grams cannot be negative")


if __name__ == "__main__":
    unittest.main()
