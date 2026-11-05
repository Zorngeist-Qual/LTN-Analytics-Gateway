import json
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from main import read_jsonl
from shared.configuration.loader import load_config
from shared.configuration.ssl_settings import get_database_ssl_option
from shared.configuration.user_config import (
    DatabaseConfig,
    GatewayConfig,
    load_user_config,
    save_user_config,
)
from tools.data_formatter import to_snapshot_obj
import shared.configuration.user_config as user_config_module


class JsonlReaderTests(unittest.TestCase):
    def test_reads_packets_and_skips_blank_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "data.jsonl"
            source.write_text('{"tick": 1}\n\n{"tick": 2}\n', encoding="utf-8")

            self.assertEqual(read_jsonl(source), [{"tick": 1}, {"tick": 2}])

    def test_reports_invalid_json_line_number(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "data.jsonl"
            source.write_text('{"tick": 1}\nnot-json\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "строке 2"):
                read_jsonl(source)

    def test_rejects_non_object_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "data.jsonl"
            source.write_text('[1, 2, 3]\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "ожидался JSON-объект"):
                read_jsonl(source)

    def test_reports_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            read_jsonl(Path("missing-data.jsonl"))


class SnapshotFormatterTests(unittest.TestCase):
    def test_converts_order_train_station_and_event(self) -> None:
        raw_snapshot = {
            "protocol_version": "1.0",
            "world_id": "9a1a5a63-d7de-41a8-9e37-3704afc1858a",
            "sequence_number": 1,
            "tick": 360,
            "trains": {
                "27": {
                    "id": 27,
                    "length": "1-1-0",
                    "composition_summary": {
                        "cargo-wagon": {
                            "count": 1,
                            "content": {"iron-plate": 10},
                        }
                    },
                    "fuel": [],
                    "name": "Test train",
                    "planet": "nauvis",
                }
            },
            "stations": {
                "10": {
                    "id": 10,
                    "name": "Source",
                    "position": {"x": 1, "y": 2},
                    "planet": "nauvis",
                },
                "20": {
                    "id": 20,
                    "name": "Destination",
                    "position": {"x": 3, "y": 4},
                    "planet": "nauvis",
                },
            },
            "active_orders": [
                {
                    "id": 4,
                    "creation_time": 100,
                    "network_id": 1,
                    "train_id": 27,
                    "current_content": [{"type": "iron-plate", "count": 10}],
                    "required": [{"type": "iron-plate", "count": 20}],
                }
            ],
            "order_events": [
                {
                    "id": "7fc67b50-72f0-4de0-8a97-0ca30f34f43c",
                    "order_id": 4,
                    "action": "create",
                    "from_id": 10,
                    "to_id": 20,
                    "is_empty": False,
                    "tick": 100,
                    "train_id": 27,
                }
            ],
        }

        snapshot = to_snapshot_obj(raw_snapshot)

        self.assertEqual(snapshot.active_orders[0].current_cargo[0]["name"], "iron-plate")
        self.assertEqual(snapshot.active_orders[0].train_data.body_composition["cargo-wagon"]["count"], 1)
        self.assertEqual(snapshot.order_events[0].from_station.id, 10)
        self.assertEqual(snapshot.order_events[0].type.value, "created")


class UserConfigTests(unittest.TestCase):
    def test_config_round_trip_and_database_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "config.conf"
            with patch.object(user_config_module, "CONFIG_PATH", config_path):
                config = GatewayConfig(
                    source_jsonl_path="C:/factorio/data.jsonl",
                    database=DatabaseConfig(
                        db_user="gateway",
                        db_password="test-secret",
                        db_host="db.example.test",
                        db_port=5432,
                        db_name="analytics",
                        db_ssl=True,
                    ),
                )
                save_user_config(config)

                self.assertTrue(config_path.is_file())
                self.assertEqual(load_user_config(), config)
                loaded = load_config()
                self.assertEqual(loaded.db_settings.db_user, "gateway")
                self.assertTrue(loaded.db_settings.db_ssl)

    def test_legacy_config_defaults_ssl_to_disabled(self) -> None:
        legacy_config = GatewayConfig.model_validate_json(
            json.dumps(
                {
                    "source_jsonl_path": "C:/factorio/data.jsonl",
                    "database": {
                        "db_user": "gateway",
                        "db_password": "test-secret",
                        "db_host": "db.example.test",
                        "db_port": 5432,
                        "db_name": "analytics",
                    },
                }
            )
        )

        self.assertFalse(legacy_config.database.db_ssl)

    def test_ssl_option_uses_certificate_verification(self) -> None:
        self.assertIs(get_database_ssl_option(False), False)
        context = get_database_ssl_option(True)

        self.assertIsInstance(context, ssl.SSLContext)
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)


if __name__ == "__main__":
    unittest.main()
