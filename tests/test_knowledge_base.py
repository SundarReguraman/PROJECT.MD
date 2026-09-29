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
    def test_covers_at_least_the_prd_top_25(self):
        self.assertGreaterEqual(len(TRAPS), 25)

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


def trap_ids(idea):
    return {w.trap.id for w in scan(idea)}


def escalated(idea):
    return {w.trap.id for w in scan(idea) if w.explicitly_mentioned}


class NegationTest(unittest.TestCase):
    """Issue #1: rejecting a dead end must never count as choosing it."""

    def test_negated_mentions_do_not_escalate(self):
        for idea in (
            "A handwriting app, and I will NOT use OpenCV",
            "handwriting reader without OpenCV",
            "handwriting app instead of Tesseract",
            "a chat app, avoid polling",
            "an e-commerce shop with no MongoDB",
            "handwriting app, I don't want to use OpenCV",
        ):
            with self.subTest(idea=idea):
                self.assertEqual(escalated(idea), set())

    def test_negation_keeps_the_proactive_guard(self):
        self.assertIn("OCR-001", trap_ids("A handwriting app, and I will NOT use OpenCV"))

    def test_real_choices_still_escalate(self):
        for idea in (
            "Use OpenCV to read handwriting",
            "an OpenCV-based handwriting reader",
            "handwriting app, not sure, maybe OpenCV?",
            "I have no idea how to use OpenCV for handwriting",
            "read handwriting with OpenCV, not Tesseract",
        ):
            with self.subTest(idea=idea):
                self.assertIn("OCR-001", escalated(idea))


class ParaphraseTest(unittest.TestCase):
    """Issues #2 and #3: the same problem phrased differently gets the same guard."""

    def test_handwriting_phrasings_trigger_ocr_001(self):
        for idea in (
            "An app to transcribe doctor handwriting",
            "Read doctor's prescriptions",
            "Read scanned prescriptions from doctors",
            "scanned prescriptions",
            "letters written by hand",
            "my grandma's cursive recipe cards",
            "digitise handwritten forms",
            "notes from doctors into a database",
            "Turn photos of whiteboard notes into text",
            "OCR my lecture notes",
        ):
            with self.subTest(idea=idea):
                self.assertIn("OCR-001", trap_ids(idea))

    def test_non_handwriting_ideas_do_not_trigger_ocr_001(self):
        for idea in ("A pharmacy app to manage prescription refills", "A shared real-time whiteboard for teams"):
            with self.subTest(idea=idea):
                self.assertNotIn("OCR-001", trap_ids(idea))

    def test_whiteboard_photo_is_not_collaborative_editing(self):
        self.assertNotIn("RT-002", trap_ids("Turn photos of whiteboard notes into text"))

    def test_collaborative_whiteboards_still_trigger_rt_002(self):
        for idea in ("A shared real-time whiteboard for teams", "A whiteboard app we can draw on together"):
            with self.subTest(idea=idea):
                self.assertIn("RT-002", trap_ids(idea))


class CoverageTest(unittest.TestCase):
    """Issue #4: marketplace, location, payment and notification risks are detected."""

    def test_service_marketplace_traps(self):
        ids = trap_ids("An Uber for dog walkers")
        for expected in ("GEO-001", "GEO-002", "PAY-001"):
            self.assertIn(expected, ids)

    def test_new_traps_fire_on_their_own_domains(self):
        cases = {
            "A live GPS tracker for delivery couriers": "GEO-001",
            "Find coffee shops near me": "GEO-002",
            "A subscription box site with checkout": "PAY-001",
            "A mobile app that reminds users to take their meds": "PUSH-001",
        }
        for idea, expected in cases.items():
            with self.subTest(idea=idea):
                self.assertIn(expected, trap_ids(idea))

    def test_storing_cards_escalates(self):
        self.assertIn("PAY-001", escalated("A checkout that stores credit cards in our database"))


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
