"""Regression and adversarial checks for the experimental reference gate."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import copy
import itertools
import unittest

from agp.core import (
    POLICY_VERSION, REQUIRED_CHECKS, Claim, PAL, Relationship, ReleaseDecision,
    Source, TaskProfile, build_receipt, decide_release, verify_receipt,
)


NOW = datetime(2026, 10, 29, 12, 0, tzinfo=timezone.utc)


def profile() -> TaskProfile:
    return TaskProfile(2, 3, 1, 2, 1, 1)


def source(**overrides) -> Source:
    data = dict(
        source_id="POLICY-1", title="Synthetic policy", version="1.0",
        approved=True, effective_at=NOW - timedelta(days=1), expires_at=None,
        sections={"4.1": "Approved business rideshare is reimbursable."},
    )
    data.update(overrides)
    return Source(**data)


def claim(**overrides) -> Claim:
    data = dict(
        claim_id="C-1", claim_text="Approved rideshare is preliminarily eligible.",
        relationship=Relationship.DIRECT, source_ids=("POLICY-1",),
        locators=("4.1",), material=True,
    )
    data.update(overrides)
    return Claim(**data)


def gate(**overrides):
    data = dict(
        profile=profile(), claims=[claim()], vii=2,
        checks={key: True for key in REQUIRED_CHECKS},
        sources={"POLICY-1": source()}, now=NOW,
    )
    data.update(overrides)
    return decide_release(**data)


class ProfileTests(unittest.TestCase):
    def test_sum_thresholds_exhaustively(self):
        # Independently check all 15,625 allowed profiles against base thresholds.
        for scores in itertools.product(range(5), repeat=6):
            with self.subTest(scores=scores):
                current = TaskProfile(*scores)
                total = sum(scores)
                expected = (0 if total <= 4 else 1 if total <= 8 else
                            2 if total <= 13 else 3 if total <= 18 else 4)
                self.assertEqual(current.total, total)
                self.assertEqual(int(current.base_pal), expected)
                self.assertGreaterEqual(current.pal, current.base_pal)

    def test_wrong_original_boundary_is_corrected(self):
        current = TaskProfile(3, 3, 2, 2, 2, 2)
        self.assertEqual(current.total, 14)
        self.assertEqual(current.pal, PAL.CONTROLLED)

    def test_critical_consequence_cannot_be_diluted_by_zeros(self):
        self.assertEqual(TaskProfile(4, 0, 0, 0, 0, 0).pal, PAL.RESTRICTED)

    def test_irreversibility_cannot_be_diluted_by_zeros(self):
        self.assertEqual(TaskProfile(0, 0, 0, 4, 0, 0).pal, PAL.RESTRICTED)

    def test_controlled_floors(self):
        for dimension, value in ((0, 3), (2, 3), (4, 3), (5, 4)):
            scores = [0] * 6
            scores[dimension] = value
            self.assertEqual(TaskProfile(*scores).pal, PAL.CONTROLLED)

    def test_current_evidence_floor(self):
        self.assertEqual(TaskProfile(0, 3, 0, 0, 0, 0).pal, PAL.OPERATIONAL)

    def test_invalid_dimension_types_rejected(self):
        for invalid in (True, False, 1.0, "1", None, -1, 5):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                TaskProfile(invalid, 0, 0, 0, 0, 0)

    def test_profile_is_immutable(self):
        current = profile()
        with self.assertRaises(FrozenInstanceError):
            current.consequence = 0


class SourceAndClaimTests(unittest.TestCase):
    def test_timezone_naive_source_rejected(self):
        with self.assertRaises(ValueError):
            source(effective_at=datetime(2026, 10, 1))

    def test_invalid_source_expiration_rejected(self):
        with self.assertRaises(ValueError):
            source(expires_at=NOW - timedelta(days=2))

    def test_truthy_source_approval_rejected(self):
        with self.assertRaises(ValueError):
            source(approved="true")

    def test_source_sections_are_snapshot_and_immutable(self):
        original = {"4.1": "Original text"}
        current = source(sections=original)
        original["4.1"] = "Changed text"
        self.assertEqual(current.sections["4.1"], "Original text")
        with self.assertRaises(TypeError):
            current.sections["4.1"] = "Changed text"

    def test_source_timestamp_boundaries(self):
        current = source(effective_at=NOW, expires_at=NOW + timedelta(days=1))
        self.assertTrue(current.is_current(NOW))
        self.assertFalse(current.is_current(NOW + timedelta(days=1)))

    def test_empty_claim_fields_rejected(self):
        for field in ("claim_id", "claim_text"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                claim(**{field: " "})

    def test_claim_support_requires_both_source_and_locator(self):
        for fields in (dict(source_ids=(), locators=()),
                       dict(source_ids=("POLICY-1",), locators=())):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                claim(**fields)

    def test_claim_enum_and_material_are_strict(self):
        for fields in (dict(relationship="DIRECT"), dict(material="false")):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                claim(**fields)

    def test_claim_lists_are_snapshot(self):
        sources = ["POLICY-1"]
        current = claim(source_ids=sources)
        sources[0] = "OTHER"
        self.assertEqual(current.source_ids, ("POLICY-1",))


class GateTests(unittest.TestCase):
    def test_supported_recommendation_releases(self):
        self.assertEqual(gate(), (ReleaseDecision.RELEASE, []))

    def test_missing_each_required_check_withholds(self):
        for missing in REQUIRED_CHECKS:
            checks = {key: True for key in REQUIRED_CHECKS if key != missing}
            with self.subTest(missing=missing):
                self.assertEqual(gate(checks=checks)[0], ReleaseDecision.WITHHOLD)

    def test_empty_checks_do_not_pass_vacuously(self):
        self.assertEqual(gate(checks={})[0], ReleaseDecision.WITHHOLD)

    def test_truthy_strings_numbers_and_false_do_not_pass(self):
        for invalid in ("PASS", "FAIL", 1, [], None, False):
            checks = {key: True for key in REQUIRED_CHECKS}
            checks["evidence"] = invalid
            with self.subTest(invalid=invalid):
                self.assertEqual(gate(checks=checks)[0], ReleaseDecision.WITHHOLD)

    def test_unknown_source_withholds_without_lookup_crash(self):
        self.assertEqual(gate(sources={})[0], ReleaseDecision.WITHHOLD)

    def test_fabricated_locator_withholds(self):
        self.assertEqual(gate(claims=[claim(locators=("99.99",))])[0],
                         ReleaseDecision.WITHHOLD)

    def test_registry_key_must_match_source_identity(self):
        self.assertEqual(gate(sources={"POLICY-1": source(source_id="OTHER")})[0],
                         ReleaseDecision.WITHHOLD)

    def test_stale_future_and_unapproved_sources_withhold(self):
        for overrides in (dict(expires_at=NOW),
                          dict(effective_at=NOW + timedelta(seconds=1)),
                          dict(approved=False)):
            with self.subTest(overrides=overrides):
                self.assertEqual(gate(sources={"POLICY-1": source(**overrides)})[0],
                                 ReleaseDecision.WITHHOLD)

    def test_empty_and_malformed_claim_ledgers_withhold(self):
        for claims in ([], None, {}, ["not a claim"]):
            with self.subTest(claims=claims):
                self.assertEqual(gate(claims=claims)[0], ReleaseDecision.WITHHOLD)

    def test_duplicate_claim_ids_withhold(self):
        self.assertEqual(gate(claims=[claim(), claim()])[0], ReleaseDecision.WITHHOLD)

    def test_material_coverage_cannot_be_evaded_by_empty_material_set(self):
        self.assertEqual(gate(claims=[claim(material=False)])[0], ReleaseDecision.WITHHOLD)

    def test_unsupported_and_unverifiable_material_claims_withhold(self):
        for relationship in (Relationship.UNSUPPORTED, Relationship.UNVERIFIABLE):
            current = claim(relationship=relationship, source_ids=(), locators=())
            with self.subTest(relationship=relationship):
                self.assertEqual(gate(claims=[current])[0], ReleaseDecision.WITHHOLD)

    def test_material_conflict_escalates(self):
        self.assertEqual(gate(claims=[claim(relationship=Relationship.CONFLICTED)])[0],
                         ReleaseDecision.ESCALATE)

    def test_material_inference_escalates(self):
        self.assertEqual(gate(claims=[claim(relationship=Relationship.INFERRED)])[0],
                         ReleaseDecision.ESCALATE)

    def test_nonmaterial_inference_requires_disclosure(self):
        ledger = [claim(), claim(claim_id="C-2", relationship=Relationship.INFERRED,
                                 material=False)]
        self.assertEqual(gate(claims=ledger)[0], ReleaseDecision.RELEASE_WITH_DISCLOSURE)
        self.assertEqual(gate(claims=ledger, allow_disclosure=False)[0],
                         ReleaseDecision.WITHHOLD)

    def test_failure_overrides_conflict_and_human_approval(self):
        self.assertEqual(gate(claims=[claim(relationship=Relationship.CONFLICTED)],
                              checks={}, human_approved=True)[0],
                         ReleaseDecision.WITHHOLD)

    def test_source_failure_overrides_restricted_approval(self):
        self.assertEqual(gate(profile=TaskProfile(4, 0, 0, 0, 0, 0), vii=4,
                              sources={}, human_approved=True)[0], ReleaseDecision.WITHHOLD)

    def test_vii_range_type_and_minimum(self):
        for invalid in (True, 2.0, "2", -1, 5, 1):
            with self.subTest(invalid=invalid):
                self.assertEqual(gate(vii=invalid)[0], ReleaseDecision.WITHHOLD)

    def test_pal4_needs_vii4_and_actual_human_boolean(self):
        restricted = TaskProfile(4, 0, 0, 0, 0, 0)
        self.assertEqual(gate(profile=restricted, vii=3, human_approved=True)[0],
                         ReleaseDecision.WITHHOLD)
        self.assertEqual(gate(profile=restricted, vii=4)[0], ReleaseDecision.ESCALATE)
        self.assertEqual(gate(profile=restricted, vii=4, human_approved="approved")[0],
                         ReleaseDecision.WITHHOLD)
        self.assertEqual(gate(profile=restricted, vii=4, human_approved=True)[0],
                         ReleaseDecision.RELEASE)

    def test_naive_check_time_withholds(self):
        self.assertEqual(gate(now=datetime(2026, 10, 29))[0], ReleaseDecision.WITHHOLD)

    def test_workflow_review_is_separate_from_pal(self):
        self.assertEqual(gate(workflow_review_required=True)[0], ReleaseDecision.ESCALATE)
        self.assertEqual(gate(workflow_review_required=True, human_approved=True)[0],
                         ReleaseDecision.RELEASE)

    def test_workflow_review_setting_must_be_a_boolean(self):
        self.assertEqual(gate(workflow_review_required="no")[0], ReleaseDecision.WITHHOLD)

    def test_workflow_approval_cannot_waive_evidence_or_inference(self):
        self.assertEqual(gate(workflow_review_required=True, human_approved=True,
                              checks={})[0], ReleaseDecision.WITHHOLD)
        self.assertEqual(gate(workflow_review_required=True, human_approved=True,
                              claims=[claim(relationship=Relationship.INFERRED)])[0],
                         ReleaseDecision.ESCALATE)
        self.assertEqual(gate(workflow_review_required=True, human_approved=True,
                              claims=[claim(relationship=Relationship.CONFLICTED)])[0],
                         ReleaseDecision.ESCALATE)

    def test_generator_cannot_pass_a_release_override(self):
        with self.assertRaises(TypeError):
            gate(proposed_release_decision="RELEASE")

    def test_all_registry_controls_are_structural_not_entailment(self):
        # A lie can cite a real locator. The trusted evidence check must detect it.
        incorrect = claim(claim_text="This source authorizes a million-dollar payment.")
        checks = {key: True for key in REQUIRED_CHECKS}
        checks["evidence"] = False
        self.assertEqual(gate(claims=[incorrect], checks=checks)[0], ReleaseDecision.WITHHOLD)


class ReceiptTests(unittest.TestCase):
    def test_round_trip_receipt_and_policy_version(self):
        receipt = build_receipt({"task_id": "TASK-1", "decision": "RELEASE"})
        self.assertTrue(verify_receipt(receipt))
        self.assertEqual(receipt["policy_version"], POLICY_VERSION)

    def test_nested_mutation_is_detected(self):
        receipt = build_receipt({"checks": {"evidence": True}})
        receipt["checks"]["evidence"] = False
        self.assertFalse(verify_receipt(receipt))

    def test_payload_is_snapshot(self):
        payload = {"checks": {"evidence": True}}
        receipt = build_receipt(payload)
        payload["checks"]["evidence"] = False
        self.assertTrue(receipt["checks"]["evidence"])
        self.assertTrue(verify_receipt(receipt))

    def test_reordered_keys_verify(self):
        receipt = build_receipt({"z": 1, "a": {"y": 2, "x": 3}})
        self.assertTrue(verify_receipt(dict(reversed(list(receipt.items())))))

    def test_non_finite_numbers_rejected(self):
        for number in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(number=number), self.assertRaises(ValueError):
                build_receipt({"metric": number})

    def test_reserved_fields_cannot_be_injected(self):
        for field in ("integrity_hash", "receipt_id", "created_at", "policy_version"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                build_receipt({field: "forged"})

    def test_malformed_hash_and_envelope_fail_closed(self):
        original = build_receipt({"task_id": "TASK-1"})
        for invalid in (None, {}, {"integrity_hash": "not-a-hash"}):
            self.assertFalse(verify_receipt(invalid))
        changed = copy.deepcopy(original)
        del changed["receipt_id"]
        self.assertFalse(verify_receipt(changed))

    def test_nonascii_and_nonhex_hashes_fail_closed_without_exception(self):
        original = build_receipt({"task_id": "TASK-1"})
        for invalid in ("é" * 64, "g" * 64, "A" * 64, " " * 64):
            changed = dict(original, integrity_hash=invalid)
            with self.subTest(invalid=invalid):
                self.assertFalse(verify_receipt(changed))


if __name__ == "__main__":
    unittest.main()
