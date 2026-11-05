import json
import tempfile
import unittest
from pathlib import Path

from tools.amp_validate_orca_mixed_nozzle_gcode_against_plan import validate
from tools.amp_generate_orca_gui_workflow_manifest import build_manifest, write_tool_map


class MixedNozzlePlanConsumerTests(unittest.TestCase):
    def check_gcode(self, header, *, explicit_map=True, extra_header="", generated_map=False):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            queue = [{"region_name": name, "recommended_tool_class": nozzle,
                      "recommended_nozzle_diameter": nozzle,
                      "selected_process_profile": "synthetic",
                      "selected_layer_height_mm": "0.1",
                      "selected_line_width_class": "0.22"}
                     for name, nozzle in [("detail", "0.2"), ("bulk", "0.6")]]
            (root / "process_queue.json").write_text(json.dumps({"process_queue": queue}))
            mapping = root / "map.json"
            mapping.write_text(json.dumps({
                "expected_used_nozzle_classes": ["0.2", "0.6"],
                "expected_tools": [
                    {"region_name": "detail", "expected_t_command": "T0", "expected_nozzle_diameter": "0.2"},
                    {"region_name": "bulk", "expected_t_command": "T1", "expected_nozzle_diameter": "0.6"},
                ],
            }))
            if generated_map:
                write_tool_map(build_manifest(root), mapping)
            gcode = root / "synthetic.gcode"
            gcode.write_text(f"; nozzle_diameter = {header}\n{extra_header}\nT0\n; detail\nT1\n; bulk\n")
            return validate(root, gcode, mapping if explicit_map else None)

    def test_accepts_matching_slots_with_unused_duplicate(self):
        self.assertTrue(self.check_gcode("0.2,0.6,0.6")["pass"])

    def test_rejects_swapped_slots_even_when_sets_match(self):
        report = self.check_gcode("0.6,0.2")
        self.assertFalse(report["pass"])
        self.assertTrue(any("T0" in error and "0.2" in error for error in report["errors"]))

    def test_packet_inferred_mapping_also_rejects_swapped_slots(self):
        self.assertFalse(self.check_gcode("0.6,0.2", explicit_map=False)["pass"])

    def test_rejects_missing_slot_even_if_diameter_appears_elsewhere(self):
        self.assertFalse(self.check_gcode("0.6", extra_header="; nozzle_diameter = 0.2,0.6")["pass"])

    def test_accepts_repeated_identical_headers(self):
        self.assertTrue(self.check_gcode("0.2,0.6", extra_header="; nozzle_diameter = 0.2,0.6")["pass"])

    def test_rejects_conflicting_later_header(self):
        self.assertFalse(self.check_gcode("0.2,0.6", extra_header="; nozzle_diameter = 0.6,0.2")["pass"])

    def test_accepts_actual_workflow_generator_mapping(self):
        self.assertTrue(self.check_gcode("0.2,0.6", generated_map=True)["pass"])

    def test_rejects_swapped_slots_against_actual_workflow_generator(self):
        self.assertFalse(self.check_gcode("0.6,0.2", generated_map=True)["pass"])


if __name__ == "__main__":
    unittest.main()
