import asyncio
import time
import unittest

from project_md.agents import BaseAgent, default_agents
from project_md.agents.orchestrator import Orchestrator, risk_score, verdict
from project_md.core.intent import infer_intent
from project_md.core.knowledge_base import TRAPS, scan
from project_md.core.models import Finding, Severity, Verdict

HANDWRITING = "An app to transcribe doctor handwriting"


class StartGate:
    """Opens once ``parties`` agents have started (asyncio.Barrier needs Python 3.11)."""

    def __init__(self, parties):
        self.parties = parties
        self.arrived = 0
        self.opened = asyncio.Event()

    async def wait(self):
        self.arrived += 1
        if self.arrived == self.parties:
            self.opened.set()
        await self.opened.wait()


class GatedAgent(BaseAgent):
    """Wraps a real agent; cannot finish until every agent in the run has started."""

    def __init__(self, inner, gate, log):
        self.inner, self.gate, self.log = inner, gate, log
        self.name = inner.name

    def owns(self, trap):
        return self.inner.owns(trap)

    async def evaluate(self, idea, domain_context):
        self.log.append(("start", self.name, time.perf_counter()))
        await self.gate.wait()
        findings = await self.inner.evaluate(idea, domain_context)
        self.log.append(("end", self.name, time.perf_counter()))
        return findings


class ExplodingAgent(BaseAgent):
    name = "exploding"

    async def evaluate(self, idea, domain_context):
        raise RuntimeError("boom")


def context_for(idea):
    warnings = scan(idea)
    return {"intent": infer_intent(idea, warnings), "warnings": warnings}


class ConcurrencyTest(unittest.TestCase):
    def test_all_five_agents_run_concurrently(self):
        async def run():
            log = []
            gate = StartGate(parties=5)
            agents = [GatedAgent(a, gate, log) for a in default_agents()]
            # Run sequentially, the first agent would wait on the gate forever.
            outcome = await asyncio.wait_for(Orchestrator(agents).run(HANDWRITING), timeout=2)
            return outcome, log

        outcome, log = asyncio.run(run())
        starts = [t for kind, _, t in log if kind == "start"]
        ends = [t for kind, _, t in log if kind == "end"]
        self.assertEqual(len(starts), 5)
        self.assertLess(max(starts), min(ends), "every agent must start before any finishes")
        self.assertEqual(
            {f.agent for f in outcome.report.findings},
            {"dependency", "architecture", "contract", "impact", "security"},
        )

    def test_failing_agent_does_not_sink_the_run(self):
        agents = default_agents() + [ExplodingAgent()]
        report = Orchestrator(agents).run_sync(HANDWRITING).report
        failures = [f for f in report.findings if f.agent == "exploding"]
        self.assertEqual(len(failures), 1)
        self.assertIn("boom", failures[0].detail)
        self.assertNotEqual(report.verdict, Verdict.PASS)
        self.assertTrue(any(f.agent == "dependency" for f in report.findings))


class AgentOutputTest(unittest.TestCase):
    IDEAS = (
        HANDWRITING,
        "A personal recipe organizer",
        "A realtime chat web app with Google login",
        "A CLI to scrape thousands of URLs",
    )

    def test_every_agent_outputs_findings_for_every_idea(self):
        for idea in self.IDEAS:
            context = context_for(idea)
            for agent in default_agents():
                with self.subTest(idea=idea, agent=agent.name):
                    findings = asyncio.run(agent.evaluate(idea, context))
                    self.assertTrue(findings)
                    for finding in findings:
                        self.assertIsInstance(finding, Finding)
                        self.assertEqual(finding.agent, agent.name)

    def test_every_trap_is_owned_by_exactly_one_agent(self):
        agents = default_agents()
        for trap in TRAPS:
            owners = [a.name for a in agents if a.owns(trap)]
            with self.subTest(trap=trap.id):
                self.assertEqual(len(owners), 1, owners)

    def test_dependency_agent_mandates_trocr_for_handwriting(self):
        report = Orchestrator().run_sync(HANDWRITING).report
        ocr = report.stack.get("OCR")
        self.assertIsNotNone(ocr)
        self.assertIn("TrOCR", ocr.choice)

    def test_architecture_agent_defines_four_layers(self):
        report = Orchestrator().run_sync(HANDWRITING).report
        self.assertEqual([l.name for l in report.layers], ["Domain", "Data", "Service", "Interface"])
        interface = next(l for l in report.layers if l.name == "Interface")
        self.assertNotIn("Data", interface.may_depend_on)

    def test_contract_agent_uses_integer_cents_for_money(self):
        report = Orchestrator().run_sync("An e-commerce shop with checkout and payments").report
        product = next(m for m in report.data_models if m.name == "Product")
        price = next(f for f in product.fields if f.name == "price_cents")
        self.assertEqual(price.type, "int")

    def test_offline_app_has_no_http_endpoints(self):
        report = Orchestrator().run_sync("An offline mobile app that reads handwritten notes").report
        self.assertEqual(report.endpoints, [])
        self.assertIsNone(report.stack.get("Backend API"))

    def test_license_risk_is_flagged(self):
        report = Orchestrator().run_sync("A web app to detect defects with YOLOv8").report
        self.assertTrue(any("AGPL" in f.title for f in report.findings))


class VerdictTest(unittest.TestCase):
    def test_naming_a_dead_end_blocks(self):
        report = Orchestrator().run_sync("Use OpenCV contours to read handwritten notes").report
        self.assertIs(report.verdict, Verdict.BLOCK)

    def test_sensitive_data_needs_review(self):
        report = Orchestrator().run_sync(HANDWRITING).report
        self.assertIs(report.verdict, Verdict.REVIEW)

    def test_simple_idea_passes(self):
        report = Orchestrator().run_sync("A personal recipe organizer").report
        self.assertIs(report.verdict, Verdict.PASS)

    def test_score_is_capped_and_decisions_are_free(self):
        critical = Finding("x", Severity.CRITICAL, "t", "d")
        self.assertEqual(risk_score([critical] * 5), 100)
        self.assertEqual(verdict([critical], 40), Verdict.BLOCK)
        report = Orchestrator().run_sync("A personal recipe organizer").report
        payload_findings = [f for f in report.findings if f.payload is not None]
        self.assertTrue(payload_findings)
        self.assertEqual(risk_score(payload_findings), 0)


class SpecRenderTest(unittest.TestCase):
    def test_project_md_carries_the_consensus(self):
        outcome = Orchestrator().run_sync("Use OpenCV contours to read handwritten notes")
        md = outcome.project_md
        self.assertTrue(md.startswith("# PROJECT.md"))
        self.assertIn("BLOCK", md)
        self.assertIn("**DO NOT:**", md)
        self.assertIn("TrOCR", md)
        self.assertIn("(you asked for this)", md)

    def test_render_is_deterministic(self):
        first = Orchestrator().run_sync(HANDWRITING).project_md
        second = Orchestrator().run_sync(HANDWRITING).project_md
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
