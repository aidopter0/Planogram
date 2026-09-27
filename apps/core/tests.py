from django.test import SimpleTestCase

from apps.core.width_fit import (
    available_width_mm,
    effective_width_mm,
    summarize_carrier,
    validate_scene_width_fit,
)


class WidthFitTests(SimpleTestCase):
    def test_available_width_d3(self):
        self.assertEqual(available_width_mm(900, 0), 900)
        self.assertEqual(available_width_mm(900, 20), 880)

    def test_effective_width_a32(self):
        self.assertEqual(effective_width_mm(66, 220, "normal"), 66)
        self.assertEqual(effective_width_mm(66, 220, "rotated_90"), 220)

    def test_summarize_and_overflow(self):
        ok = summarize_carrier(
            900,
            0,
            [
                {"effective_width_mm": 66, "facings": 4},
                {"effective_width_mm": 58, "facings": 3},
            ],
        )
        self.assertEqual(ok["used_width_mm"], 438)
        self.assertFalse(ok["overflow"])

        bad = summarize_carrier(
            200,
            0,
            [{"effective_width_mm": 66, "facings": 4}],
        )
        self.assertTrue(bad["overflow"])

    def test_validate_scene(self):
        graph = {
            "placements": [
                {
                    "id": "1",
                    "carrier_ref": {"component_instance_id": 9},
                    "effective_width_mm": 100,
                    "facings": 10,
                }
            ]
        }
        issues = validate_scene_width_fit(
            graph, {"9": {"width_mm": 900, "reserved_insets_mm": 0}}
        )
        self.assertTrue(any(i["code"] == "width_overflow" for i in issues))
