"""Tests use synthetic fixtures only; no model performance is measured."""

from hashlib import sha256
import csv
import json
from pathlib import Path
import tempfile
import unittest

from agp.benchmark import (
    load_responses, load_study, prepare_study, render_prompt, score_study,
    strict_json_loads, validate_output, verifier_packets,
)
from agp.cli import demo


def output():
    return {
        "outcome": "Eligible preliminary recommendation",
        "policy_basis": ["4.1", "4.2"], "missing_information": [],
        "required_next_step": "Submit for authorized human processing.",
        "authority_limitation": "Preliminary recommendation only; no payment or final approval.",
        "claims": [{"claim_id": "C-1", "claim_text": "Approved rideshare is preliminarily eligible.",
                    "relationship": "DIRECT", "source_ids": ["DHS-EXP-001-v1.1"],
                    "locators": ["4.1"], "material": True}],
        "proposed_release_decision": "RELEASE", "limitations": [],
    }


class StrictJSONTests(unittest.TestCase):
    def test_common_output_contract(self):
        self.assertEqual(validate_output(output()), [])

    def test_duplicate_keys_rejected_even_when_nested(self):
        for text in ('{"a":1,"a":2}', '{"a":{"b":1,"b":2}}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                strict_json_loads(text)

    def test_nonfinite_and_overflow_numbers_rejected(self):
        for text in ('{"a":NaN}', '{"a":Infinity}', '{"a":1e999}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                strict_json_loads(text)

    def test_nonobject_output_rejected(self):
        for parsed in ([], None, "text", 4):
            self.assertTrue(validate_output(parsed))

    def test_missing_release_and_empty_claims_rejected(self):
        parsed = output()
        del parsed["proposed_release_decision"]
        parsed["claims"] = []
        self.assertTrue(validate_output(parsed))

    def test_truthy_material_string_rejected(self):
        parsed = output()
        parsed["claims"][0]["material"] = "true"
        self.assertTrue(validate_output(parsed))

    def test_claims_need_unique_ids_and_paired_locators(self):
        parsed = output()
        parsed["claims"].append(dict(parsed["claims"][0]))
        parsed["claims"][1]["locators"] = []
        errors = validate_output(parsed)
        self.assertTrue(any("Duplicate" in error for error in errors))
        self.assertTrue(any("lengths differ" in error for error in errors))

    def test_extra_schema_fields_rejected(self):
        parsed = output()
        parsed["secret_extra"] = "value"
        self.assertTrue(validate_output(parsed))


class StudyTests(unittest.TestCase):
    def setUp(self):
        # Keep test scratch within the checkout; this also works in restricted
        # Windows environments where the operating-system temp root is read-only.
        scratch = Path.cwd() / "results" / "test-work"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="fixture-", dir=scratch)
        self.root = Path(self.temporary.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.case = {
            "case_id": "EXP-001", "category": "ordinary",
            "request": "Approved business rideshare, $42; receipt supplied.",
            "expected_outcomes": ["Eligible preliminary recommendation"],
            "expected_release": "RELEASE", "required_sections": ["4.1", "4.2"],
            "notes": "GOLD_NOTES_MUST_NEVER_LEAK",
            "expected_checks": ["GOLD_CHECK_MUST_NEVER_LEAK"],
            "additional_sources": [{"id": "EXTRA-1", "status": "expired",
                                    "content": "Expired synthetic text", "sections": {"3.1": "Old rule"},
                                    "expected": "HIDDEN_EXTRA_KEY"}],
        }
        (self.data / "cases.jsonl").write_text(json.dumps(self.case) + "\n", encoding="utf-8")
        (self.data / "expense_policy_v1.1.txt").write_text(
            "Source DHS-EXP-001-v1.1. 4.1 Rideshare rule. 4.2 Receipt rule.", encoding="utf-8")
        (self.data / "expense_policy_v0.9.txt").write_text("Expired policy.", encoding="utf-8")
        self.study = self.root / "study"
        self.manifest = prepare_study(self.study, repeats=1, seed=123, data_directory=self.data)

    def tearDown(self):
        self.temporary.cleanup()

    def responses(self, records):
        path = self.root / "responses.jsonl"
        path.write_text("".join(json.dumps(record, allow_nan=False) + "\n" for record in records), encoding="utf-8")
        return path

    def record(self, job=None, parsed=None):
        job = job or self.manifest["jobs"][0]
        return {"job_id": job["job_id"], "model_id": "PINNED-MODEL-1",
                "text": json.dumps(output() if parsed is None else parsed)}

    def test_prepare_generates_each_method_without_gold_leak(self):
        self.assertEqual(self.manifest["generator_jobs"], 4)
        self.assertEqual(self.manifest["full_agp_verifier_jobs"], 1)
        self.assertEqual({job["method"] for job in self.manifest["jobs"]}, {"A", "B", "C", "D"})
        for job in self.manifest["jobs"]:
            prompt = (self.study / job["prompt_file"]).read_text(encoding="utf-8")
            self.assertNotIn("GOLD_NOTES_MUST_NEVER_LEAK", prompt)
            self.assertNotIn("GOLD_CHECK_MUST_NEVER_LEAK", prompt)
            self.assertNotIn("HIDDEN_EXTRA_KEY", prompt)
            self.assertNotIn('"expected_release"', prompt)
            self.assertIn("Expired synthetic text", prompt)
            self.assertIn("COMMON OUTPUT CONTRACT", prompt)
            self.assertIn("CASE-FACTS", prompt)

    def test_c_and_d_generation_prompts_are_identical(self):
        prompts = {job["method"]: (self.study / job["prompt_file"]).read_text(encoding="utf-8")
                   for job in self.manifest["jobs"]}
        self.assertEqual(prompts["C"], prompts["D"])

    def test_hidden_category_cannot_change_generation_prompt(self):
        conflict_label = dict(self.case, category="conflict")
        missing_label = dict(self.case, category="missing evidence")
        for method in ("A", "B", "C", "D"):
            with self.subTest(method=method):
                self.assertEqual(render_prompt(method, conflict_label, "policy"),
                                 render_prompt(method, missing_label, "policy"))

    def test_randomization_is_reproducible(self):
        second = prepare_study(self.root / "second", 1, 123, self.data)
        self.assertEqual(self.manifest["jobs"], second["jobs"])

    def test_existing_study_cannot_be_overwritten(self):
        with self.assertRaises(ValueError):
            prepare_study(self.study, 1, 123, self.data)

    def test_invalid_repeats_rejected(self):
        for invalid in (True, 0, -1, 101):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                prepare_study(self.root / "bad", invalid, 1, self.data)

    def test_frozen_inputs_and_prompts_detect_changes(self):
        path = self.study / self.manifest["jobs"][0]["prompt_file"]
        path.write_text("Tampered prompt", encoding="utf-8")
        with self.assertRaises(ValueError):
            load_study(self.study)

    def test_frozen_gold_detects_changes(self):
        (self.study / "inputs" / "cases.jsonl").write_text("{}\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            load_study(self.study)

    def test_missing_jobs_remain_in_denominator(self):
        summary = score_study(self.study, self.responses([self.record()]), self.root / "scores")
        self.assertEqual(summary["scheduled_jobs"], 4)
        self.assertEqual(summary["received_jobs"], 1)
        self.assertEqual(summary["missing_responses"], 3)
        self.assertTrue(summary["semantic_review_pending"])
        with (self.root / "scores" / "scores.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        missing = [row for row in rows if row["status"] == "MISSING_RESPONSE"]
        self.assertEqual(len(missing), 3)
        self.assertTrue(all(row["FORMAT"] == "0" for row in missing))

    def test_all_required_sections_must_be_cited(self):
        parsed = output()
        parsed["policy_basis"] = ["4.1"]
        summary = score_study(self.study, self.responses([self.record(parsed=parsed)]), self.root / "scores")
        method = self.manifest["jobs"][0]["method"]
        self.assertEqual(summary["by_method"][method]["REQUIRED_SECTIONS_MATCH"], 0)
        self.assertEqual(summary["by_method"][method]["OUTCOME_MATCH"], 1)

    def test_execution_error_counts_as_failure(self):
        record = self.record()
        record.update(text=None, error="Synthetic timeout")
        summary = score_study(self.study, self.responses([record]), self.root / "scores")
        self.assertEqual(summary["execution_errors"], 1)
        method = self.manifest["jobs"][0]["method"]
        self.assertEqual(summary["by_method"][method]["FORMAT"], 0)

    def test_raw_duplicate_json_key_does_not_get_repaired(self):
        record = self.record()
        record["text"] = '{"outcome":"Ineligible","outcome":"Eligible preliminary recommendation"}'
        summary = score_study(self.study, self.responses([record]), self.root / "scores")
        method = self.manifest["jobs"][0]["method"]
        self.assertEqual(summary["by_method"][method]["FORMAT"], 0)

    def test_unknown_duplicate_and_mixed_model_records_stop(self):
        first = self.record()
        second = self.record(self.manifest["jobs"][1])
        for records in ([dict(first, job_id="UNKNOWN")], [first, first],
                        [first, dict(second, model_id="DIFFERENT-MODEL")]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                load_responses(self.responses(records), self.manifest)

    def test_verifier_packet_is_bound_to_raw_draft_without_gold(self):
        d_job = next(job for job in self.manifest["jobs"] if job["method"] == "D")
        record = self.record(d_job)
        result = verifier_packets(self.study, self.responses([record]), self.root / "verify")
        self.assertEqual(len(result["packets"]), 1)
        packet = result["packets"][0]
        self.assertEqual(packet["draft_sha256"], sha256(record["text"].encode()).hexdigest())
        prompt = (self.root / "verify" / packet["prompt_file"]).read_text(encoding="utf-8")
        self.assertNotIn("GOLD_NOTES_MUST_NEVER_LEAK", prompt)
        self.assertNotIn("GOLD_CHECK_MUST_NEVER_LEAK", prompt)
        self.assertIn(record["text"].replace('"', '\\"'), prompt)
        self.assertIn("EVALUATION DATE\n2026-10-29", prompt)

    def test_demo_is_explicit_software_fixture(self):
        result = demo()
        self.assertIn("SOFTWARE FIXTURE", result["kind"])
        self.assertEqual(result["current_source_decision"], "RELEASE")
        self.assertEqual(result["stale_source_decision"], "WITHHOLD")
        self.assertTrue(result["receipt_valid_before_tamper"])
        self.assertFalse(result["receipt_valid_after_tamper"])
        self.assertTrue(result["example_receipt"]["draft_sha256"])
        self.assertTrue(result["example_receipt"]["sources"][0]["sections_sha256"])
        self.assertTrue(result["example_receipt"]["checks"]["evidence"])


if __name__ == "__main__":
    unittest.main()
