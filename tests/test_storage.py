"""Characterisation tests for the SQLite persistence layer in db.py."""

import sys
import tempfile
import unittest
import warnings
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import db


def setUpModule():
    # db.py leaves sqlite connections open after its "with" blocks; the runner
    # enables the 'default' filter, which surfaces their ResourceWarning noise.
    warnings.filterwarnings(
        "ignore", message="unclosed database", category=ResourceWarning
    )


class TempDbTestCase(unittest.TestCase):
    """Base case isolating every test in its own temporary SQLite file."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db_path = Path(tmp.name) / "spooli_test.db"

    def table_names(self):
        conn = db.get_connection(self.db_path)
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
            return {row["name"] for row in rows}
        finally:
            conn.close()


class InitDbTests(TempDbTestCase):
    """db.init_db must create the schema and seed default settings."""

    def test_creates_database_file_and_returns_path(self):
        returned = db.init_db(self.db_path)
        self.assertEqual(returned, self.db_path)
        self.assertTrue(self.db_path.is_file())

    def test_creates_expected_tables(self):
        db.init_db(self.db_path)
        self.assertTrue({"settings", "spools", "prints"} <= self.table_names())

    def test_init_db_is_idempotent(self):
        db.init_db(self.db_path)
        db.create_spool("PLA", path=self.db_path)
        db.init_db(self.db_path)
        self.assertEqual(len(db.get_all_spools(self.db_path)), 1)
        settings_conn = db.get_connection(self.db_path)
        try:
            count = settings_conn.execute("SELECT COUNT(*) FROM settings").fetchone()[0]
        finally:
            settings_conn.close()
        self.assertEqual(count, len(db.DEFAULT_SETTINGS))


class DefaultSettingsTests(TempDbTestCase):
    """Seeded settings must match db.DEFAULT_SETTINGS exactly."""

    def test_default_settings_are_seeded(self):
        db.init_db(self.db_path)
        self.assertEqual(db.get_setting("electricity_kwh_cost", self.db_path), "0.15")
        self.assertEqual(db.get_setting("printer_power_watts", self.db_path), "150")
        self.assertEqual(db.get_setting("currency_symbol", self.db_path), "$")

    def test_unknown_setting_returns_none(self):
        db.init_db(self.db_path)
        self.assertIsNone(db.get_setting("does_not_exist", self.db_path))

    def test_set_setting_overrides_seeded_value(self):
        db.init_db(self.db_path)
        db.set_setting("currency_symbol", "MXN", self.db_path)
        self.assertEqual(db.get_setting("currency_symbol", self.db_path), "MXN")


class SpoolCrudTests(TempDbTestCase):
    """Spool create/read operations and their validation contracts."""

    def setUp(self):
        super().setUp()
        db.init_db(self.db_path)

    def test_create_spool_returns_integer_id(self):
        first = db.create_spool("PLA", path=self.db_path)
        second = db.create_spool("PETG", path=self.db_path)
        self.assertIsInstance(first, int)
        self.assertEqual(second, first + 1)

    def test_create_spool_defaults_remaining_to_initial_weight(self):
        spool_id = db.create_spool("PLA", initial_weight_g=750.0, path=self.db_path)
        spool = db.get_spool_by_id(spool_id, self.db_path)
        self.assertEqual(spool["initial_weight_g"], 750.0)
        self.assertEqual(spool["remaining_weight_g"], 750.0)

    def test_create_spool_stores_all_fields(self):
        spool_id = db.create_spool(
            "PLA",
            brand="Sunlu",
            color="White",
            initial_weight_g=1000.0,
            purchase_price=19.99,
            remaining_weight_g=400.0,
            path=self.db_path,
        )
        spool = db.get_spool_by_id(spool_id, self.db_path)
        self.assertEqual(spool["material"], "PLA")
        self.assertEqual(spool["brand"], "Sunlu")
        self.assertEqual(spool["color"], "White")
        self.assertEqual(spool["purchase_price"], 19.99)
        self.assertEqual(spool["remaining_weight_g"], 400.0)

    def test_create_spool_rejects_blank_material(self):
        with self.assertRaises(ValueError) as ctx:
            db.create_spool("   ", path=self.db_path)
        self.assertEqual(str(ctx.exception), "material must be a non-empty string")

    def test_create_spool_rejects_non_positive_initial_weight(self):
        with self.assertRaises(ValueError) as ctx:
            db.create_spool("PLA", initial_weight_g=0.0, path=self.db_path)
        self.assertEqual(
            str(ctx.exception), "initial_weight_g must be greater than 0"
        )

    def test_create_spool_rejects_negative_price(self):
        with self.assertRaises(ValueError) as ctx:
            db.create_spool("PLA", purchase_price=-1.0, path=self.db_path)
        self.assertEqual(str(ctx.exception), "purchase_price cannot be negative")

    def test_create_spool_rejects_remaining_above_initial(self):
        with self.assertRaises(ValueError) as ctx:
            db.create_spool(
                "PLA",
                initial_weight_g=1000.0,
                remaining_weight_g=1200.0,
                path=self.db_path,
            )
        self.assertEqual(
            str(ctx.exception), "remaining_weight_g must be within [0, initial_weight_g]"
        )

    def test_create_spool_rejects_negative_remaining(self):
        with self.assertRaises(ValueError) as ctx:
            db.create_spool("PLA", remaining_weight_g=-1.0, path=self.db_path)
        self.assertEqual(
            str(ctx.exception), "remaining_weight_g must be within [0, initial_weight_g]"
        )

    def test_get_all_spools_ordered_by_id(self):
        first = db.create_spool("PLA", path=self.db_path)
        second = db.create_spool("PETG", path=self.db_path)
        third = db.create_spool("ABS", path=self.db_path)
        self.assertEqual(
            [spool["id"] for spool in db.get_all_spools(self.db_path)],
            [first, second, third],
        )

    def test_get_spool_by_id_returns_none_for_missing(self):
        self.assertIsNone(db.get_spool_by_id(404, self.db_path))

    def test_get_compatible_spools_filters_and_orders(self):
        db.create_spool("PLA", remaining_weight_g=250.0, path=self.db_path)
        db.create_spool("PLA", remaining_weight_g=120.0, path=self.db_path)
        db.create_spool("PLA", remaining_weight_g=80.0, path=self.db_path)
        db.create_spool("PETG", remaining_weight_g=500.0, path=self.db_path)
        compatible = db.get_compatible_spools("PLA", 100.0, self.db_path)
        self.assertEqual([spool["remaining_weight_g"] for spool in compatible], [120.0, 250.0])
        self.assertTrue(all(spool["material"] == "PLA" for spool in compatible))

    def test_get_compatible_spools_rejects_negative_required(self):
        with self.assertRaises(ValueError) as ctx:
            db.get_compatible_spools("PLA", -1.0, self.db_path)
        self.assertEqual(str(ctx.exception), "required_grams cannot be negative")


class RecordPrintJobTests(TempDbTestCase):
    """record_print_job must deduct filament and log the job atomically."""

    def setUp(self):
        super().setUp()
        db.init_db(self.db_path)
        self.spool_id = db.create_spool(
            "PLA", initial_weight_g=1000.0, remaining_weight_g=250.0,
            path=self.db_path,
        )

    def test_deducts_filament_and_registers_print_record(self):
        print_id = db.record_print_job(
            spool_id=self.spool_id,
            file_name="part.gcode",
            grams_used=50.0,
            duration_seconds=3600,
            cost=1.25,
            path=self.db_path,
        )
        self.assertIsInstance(print_id, int)
        spool = db.get_spool_by_id(self.spool_id, self.db_path)
        self.assertEqual(spool["remaining_weight_g"], 200.0)
        history = db.get_print_history(path=self.db_path)
        self.assertEqual(len(history), 1)
        record = history[0]
        self.assertEqual(record["id"], print_id)
        self.assertEqual(record["file_name"], "part.gcode")
        self.assertEqual(record["grams_used"], 50.0)
        self.assertEqual(record["duration_seconds"], 3600)
        self.assertEqual(record["status"], "completed")

    def test_cost_snapshot_defaults_to_legacy_cost_field(self):
        db.record_print_job(
            spool_id=self.spool_id,
            file_name="part.gcode",
            grams_used=10.0,
            cost=2.5,
            path=self.db_path,
        )
        record = db.get_print_history(path=self.db_path)[0]
        self.assertEqual(record["filament_cost"], 2.5)
        self.assertEqual(record["electricity_cost"], 0.0)
        self.assertEqual(record["total_cost"], 2.5)
        self.assertEqual(record["currency_symbol"], "$")

    def test_missing_spool_rolls_back_and_records_nothing(self):
        with self.assertRaises(ValueError) as ctx:
            db.record_print_job(
                spool_id=999, file_name="x.gcode", grams_used=10.0, path=self.db_path
            )
        self.assertEqual(str(ctx.exception), "spool with id 999 does not exist")
        self.assertEqual(
            db.get_spool_by_id(self.spool_id, self.db_path)["remaining_weight_g"],
            250.0,
        )
        self.assertEqual(db.get_print_history(path=self.db_path), [])

    def test_insufficient_filament_rolls_back_and_records_nothing(self):
        with self.assertRaises(ValueError) as ctx:
            db.record_print_job(
                spool_id=self.spool_id,
                file_name="x.gcode",
                grams_used=10_000.0,
                path=self.db_path,
            )
        self.assertEqual(
            str(ctx.exception), "spool does not have enough remaining filament"
        )
        self.assertEqual(
            db.get_spool_by_id(self.spool_id, self.db_path)["remaining_weight_g"],
            250.0,
        )
        self.assertEqual(db.get_print_history(path=self.db_path), [])

    def test_rejects_blank_file_name(self):
        with self.assertRaises(ValueError) as ctx:
            db.record_print_job(
                spool_id=self.spool_id, file_name="  ", grams_used=10.0,
                path=self.db_path,
            )
        self.assertEqual(str(ctx.exception), "file_name must be a non-empty string")

    def test_rejects_non_positive_grams(self):
        with self.assertRaises(ValueError) as ctx:
            db.record_print_job(
                spool_id=self.spool_id, file_name="x.gcode", grams_used=0.0,
                path=self.db_path,
            )
        self.assertEqual(str(ctx.exception), "grams_used must be greater than 0")

    def test_rejects_negative_duration(self):
        with self.assertRaises(ValueError) as ctx:
            db.record_print_job(
                spool_id=self.spool_id, file_name="x.gcode", grams_used=10.0,
                duration_seconds=-1, path=self.db_path,
            )
        self.assertEqual(str(ctx.exception), "duration_seconds cannot be negative")


class UpdateFailedPrintTests(TempDbTestCase):
    """update_failed_print must refund filament back to the spool balance."""

    def setUp(self):
        super().setUp()
        db.init_db(self.db_path)
        self.spool_id = db.create_spool(
            "PLA", initial_weight_g=1000.0, remaining_weight_g=250.0,
            path=self.db_path,
        )
        self.print_id = db.record_print_job(
            spool_id=self.spool_id,
            file_name="part.gcode",
            grams_used=50.0,
            path=self.db_path,
        )

    def test_refund_returns_unused_filament_to_spool(self):
        updated = db.update_failed_print(self.print_id, 30.0, self.db_path)
        self.assertEqual(updated["grams_used"], 30.0)
        self.assertEqual(updated["status"], "failed")
        spool = db.get_spool_by_id(self.spool_id, self.db_path)
        self.assertEqual(spool["remaining_weight_g"], 220.0)

    def test_full_consumption_keeps_balance_unchanged(self):
        updated = db.update_failed_print(self.print_id, 50.0, self.db_path)
        self.assertEqual(updated["grams_used"], 50.0)
        self.assertEqual(
            db.get_spool_by_id(self.spool_id, self.db_path)["remaining_weight_g"],
            200.0,
        )

    def test_negative_adjustment_rolls_back_when_spool_cannot_cover(self):
        # Record 480 g against a 500 g spool, leaving only 20 g of balance.
        small_spool = db.create_spool(
            "PETG", initial_weight_g=500.0, path=self.db_path
        )
        print_id = db.record_print_job(
            spool_id=small_spool, file_name="y.gcode", grams_used=480.0,
            path=self.db_path,
        )
        with self.assertRaises(ValueError) as ctx:
            db.update_failed_print(print_id, 600.0, self.db_path)
        self.assertEqual(
            str(ctx.exception), "spool does not have enough filament for adjustment"
        )
        self.assertEqual(
            db.get_spool_by_id(small_spool, self.db_path)["remaining_weight_g"], 20.0
        )
        record = db.get_print_history(path=self.db_path)
        record = next(r for r in record if r["id"] == print_id)
        self.assertEqual(record["grams_used"], 480.0)
        self.assertEqual(record["status"], "completed")

    def test_rejects_negative_actual_usage(self):
        with self.assertRaises(ValueError) as ctx:
            db.update_failed_print(self.print_id, -1.0, self.db_path)
        self.assertEqual(
            str(ctx.exception), "actual_grams_used cannot be negative"
        )
        self.assertEqual(
            db.get_spool_by_id(self.spool_id, self.db_path)["remaining_weight_g"],
            200.0,
        )

    def test_unknown_print_id_raises_exact_error(self):
        with self.assertRaises(ValueError) as ctx:
            db.update_failed_print(4242, 10.0, self.db_path)
        self.assertEqual(str(ctx.exception), "print with id 4242 does not exist")


if __name__ == "__main__":
    unittest.main()
