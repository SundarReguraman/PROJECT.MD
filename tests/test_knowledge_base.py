import json
import re
import unittest

from project_md.core.knowledge_base import TRAPS, get_trap, scan, traps_in
from project_md.core.models import (
    Category,
    PreflightReport,
    ProjectIntent,
    Severity,
    TechStack,
)


class KnowledgeBaseIntegrityTest(unittest.TestCase):
    def test_has_top_25_traps(self):
        self.assertEqual(len(TRAPS), 25)

    def test_ids_are_unique(self):
        ids = [trap.id for trap in TRAPS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_pattern_compiles(self):
        for trap in TRAPS:
            for pattern in trap.idea_patterns + trap.anti_patterns:
                with self.subTest(trap=trap.id, pattern=pattern):
                    re.compile(pattern, re.IGNORECASE)

    def test_every_trap_explains_and_recommends(self):
        for trap in TRAPS:
            with self.subTest(trap=trap.id):
                self.assertTrue(trap.idea_patterns)
                self.assertTrue(trap.anti_patterns)
                self.assertTrue(trap.why_it_fails.strip())
                self.assertTrue(trap.recommended)

    def test_every_category_is_covered(self):
        for category in Category:
            with self.subTest(category=category):
                self.assertTrue(traps_in(category))


class ScanTest(unittest.TestCase):
    def test_handwriting_idea_warns_proactively(self):
        warnings = {w.trap.id: w for w in scan("An app to transcribe doctor handwriting")}
        self.assertIn("OCR-001", warnings)
        self.assertFalse(warnings["OCR-001"].explicitly_mentioned)

    def test_naming_the_anti_pattern_escalates_to_critical(self):
        warnings = {w.trap.id: w for w in scan("Use OpenCV contours to read handwritten notes")}
        self.assertTrue(warnings["OCR-001"].explicitly_mentioned)
        self.assertIs(warnings["OCR-001"].severity, Severity.CRITICAL)

    def test_anti_pattern_alone_does_not_fire(self):
        ids = {w.trap.id for w in scan("Track feature requests from customers")}
        self.assertNotIn("SCRAPE-001", ids)

    def test_polling_chat_is_critical(self):
        warnings = {w.trap.id: w for w in scan("A chat app that polls the server every second")}
        self.assertIs(warnings["RT-001"].severity, Severity.CRITICAL)

    def test_get_trap_is_case_insensitive(self):
        self.assertEqual(get_trap("ocr-001").id, "OCR-001")


class ReportSerialisationTest(unittest.TestCase):
    def test_report_round_trips_through_json(self):
        idea = "Use OpenCV to read handwriting offline on a mobile app"
        report = PreflightReport(
            intent=ProjectIntent(idea=idea),
            stack=TechStack(language="Python"),
            warnings=scan(idea),
        )
        data = json.loads(json.dumps(report.to_dict()))
        self.assertTrue(data["has_critical"])
        ocr = next(w for w in data["warnings"] if w["trap"]["id"] == "OCR-001")
        self.assertEqual(ocr["severity"], "critical")
        self.assertEqual(ocr["trap"]["category"], "ocr")


if __name__ == "__main__":
    unittest.main()
