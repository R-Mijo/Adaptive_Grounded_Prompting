"""Small, deliberately conservative reference release gate.

Callers must supply checks from trusted validators, not from the generator.
The gate validates source identifiers and locators, but semantic entailment,
claim completeness, real verifier independence and approver identity remain
integration responsibilities. This code performs no payments or external action.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from enum import Enum, IntEnum
from hashlib import sha256
from hmac import compare_digest
import json
from types import MappingProxyType
from typing import Any
from uuid import uuid4


POLICY_VERSION = "agp-reference-controls-0.2.0"
REQUIRED_CHECKS = frozenset({
    "schema", "evidence", "authority", "freshness", "calculation", "injection",
    "logic", "missing_information",
})


class PAL(IntEnum):
    EXPLORATORY = 0
    INFORMATIONAL = 1
    OPERATIONAL = 2
    CONTROLLED = 3
    RESTRICTED = 4


class Relationship(str, Enum):
    DIRECT = "DIRECT"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    CONFLICTED = "CONFLICTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNVERIFIABLE = "UNVERIFIABLE"


class ReleaseDecision(str, Enum):
    RELEASE = "RELEASE"
    RELEASE_WITH_DISCLOSURE = "RELEASE_WITH_DISCLOSURE"
    ESCALATE = "ESCALATE"
    WITHHOLD = "WITHHOLD"


def _nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _aware(value: Any, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware datetime")
    return value


@dataclass(frozen=True)
class TaskProfile:
    consequence: int
    evidence_dependence: int
    autonomy: int
    reversibility: int
    data_sensitivity: int
    ambiguity: int

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        for item in fields(self):
            value = getattr(self, item.name)
            # bool is an int subclass and must not be accepted as a risk score.
            if type(value) is not int or not 0 <= value <= 4:
                raise ValueError(f"{item.name} must be an integer from 0 through 4")

    @property
    def total(self) -> int:
        return sum(getattr(self, item.name) for item in fields(self))

    @property
    def base_pal(self) -> PAL:
        for maximum, level in ((4, PAL.EXPLORATORY), (8, PAL.INFORMATIONAL),
                               (13, PAL.OPERATIONAL), (18, PAL.CONTROLLED)):
            if self.total <= maximum:
                return level
        return PAL.RESTRICTED

    @property
    def pal(self) -> PAL:
        """Apply provisional noncompensable floors, versioned by POLICY_VERSION.

        These are explicit conservative design choices, not validated thresholds.
        Local professional, legal or security requirements can demand more.
        """
        level = self.base_pal
        if self.evidence_dependence >= 3:
            level = max(level, PAL.OPERATIONAL)
        if (self.consequence >= 3 or self.data_sensitivity >= 3
                or self.autonomy >= 3 or self.ambiguity == 4):
            level = max(level, PAL.CONTROLLED)
        if self.consequence == 4 or self.reversibility == 4:
            level = PAL.RESTRICTED
        return PAL(level)


@dataclass(frozen=True)
class Source:
    source_id: str
    title: str
    version: str
    approved: bool
    effective_at: datetime
    expires_at: datetime | None
    sections: Mapping[str, str]

    def __post_init__(self) -> None:
        for name in ("source_id", "title", "version"):
            _nonempty(getattr(self, name), name)
        if type(self.approved) is not bool:
            raise ValueError("approved must be a boolean")
        _aware(self.effective_at, "effective_at")
        if self.expires_at is not None:
            _aware(self.expires_at, "expires_at")
            if self.expires_at <= self.effective_at:
                raise ValueError("expires_at must be after effective_at")
        if not isinstance(self.sections, Mapping) or not self.sections:
            raise ValueError("sections must be a nonempty locator-to-text mapping")
        snapshot = dict(self.sections)
        for locator, text in snapshot.items():
            _nonempty(locator, "locator")
            _nonempty(text, "section text")
        object.__setattr__(self, "sections", MappingProxyType(snapshot))

    def is_current(self, now: datetime) -> bool:
        _aware(now, "now")
        # effective_at is inclusive; expires_at is exclusive.
        return (self.approved and self.effective_at <= now
                and (self.expires_at is None or now < self.expires_at))


@dataclass(frozen=True)
class Claim:
    claim_id: str
    claim_text: str
    relationship: Relationship
    source_ids: tuple[str, ...] = ()
    locators: tuple[str, ...] = ()
    material: bool = True

    def __post_init__(self) -> None:
        _nonempty(self.claim_id, "claim_id")
        _nonempty(self.claim_text, "claim_text")
        if not isinstance(self.relationship, Relationship):
            raise ValueError("relationship must be a Relationship enum member")
        if type(self.material) is not bool:
            raise ValueError("material must be a boolean")
        for name in ("source_ids", "locators"):
            value = getattr(self, name)
            if not isinstance(value, (list, tuple)):
                raise ValueError(f"{name} must be a list or tuple of strings")
            snapshot = tuple(value)
            for item in snapshot:
                _nonempty(item, name)
            object.__setattr__(self, name, snapshot)
        if len(self.source_ids) != len(self.locators):
            raise ValueError("source_ids and locators must have matching lengths")
        if (self.relationship in {Relationship.DIRECT, Relationship.DERIVED}
                and not self.source_ids):
            raise ValueError("DIRECT and DERIVED claims require source IDs and locators")


def decide_release(
    profile: TaskProfile,
    claims: Sequence[Claim],
    vii: int,
    checks: Mapping[str, bool],
    sources: Mapping[str, Source],
    *,
    now: datetime | None = None,
    human_approved: bool = False,
    allow_disclosure: bool = True,
    workflow_review_required: bool = False,
) -> tuple[ReleaseDecision, list[str]]:
    """Decide whether a checked draft can be released as a recommendation.

    A failed mandatory check or invalid source always withholds. Conflicted or
    material inferred claims escalate only after those checks pass. A safe
    refusal or request for missing information may itself be released, if it is
    supported; this never authorizes the requested business action.

    ``human_approved`` is a demonstration input, not authenticated authorization.
    Production callers must authenticate and authorize an accountable approver.
    """
    failures: list[str] = []
    if not isinstance(profile, TaskProfile):
        return ReleaseDecision.WITHHOLD, ["Invalid task profile"]
    if type(vii) is not int or not 0 <= vii <= 4:
        failures.append("Verification independence must be an integer from 0 through 4")
    elif vii < int(profile.pal):
        failures.append(f"Verification independence below PAL-{int(profile.pal)} minimum")
    if (type(human_approved) is not bool or type(allow_disclosure) is not bool
            or type(workflow_review_required) is not bool):
        failures.append("Approval, disclosure and workflow review settings must be booleans")
    if not isinstance(checks, Mapping):
        failures.append("Mandatory checks are missing")
    else:
        for name in sorted(REQUIRED_CHECKS):
            if checks.get(name) is not True:
                failures.append(f"Mandatory check missing or failed: {name}")
    if not isinstance(sources, Mapping):
        failures.append("Source registry must be a mapping")
        sources = {}
    try:
        checked_at = _aware(now if now is not None else datetime.now(timezone.utc), "now")
    except ValueError as error:
        failures.append(str(error))
        checked_at = datetime.now(timezone.utc)
    if not isinstance(claims, (list, tuple)) or not claims:
        failures.append("A nonempty claim ledger is required")
        valid_claims: list[Claim] = []
    else:
        valid_claims = []
        identifiers: set[str] = set()
        for claim in claims:
            if not isinstance(claim, Claim):
                failures.append("Malformed claim entry")
                continue
            valid_claims.append(claim)
            if claim.claim_id in identifiers:
                failures.append(f"Duplicate claim ID: {claim.claim_id}")
            identifiers.add(claim.claim_id)
            for source_id, locator in zip(claim.source_ids, claim.locators):
                source = sources.get(source_id)
                if not isinstance(source, Source) or source.source_id != source_id:
                    failures.append(f"{claim.claim_id}: unknown or mismatched source {source_id}")
                    continue
                if not source.is_current(checked_at):
                    failures.append(f"{claim.claim_id}: source is unapproved, future, or expired: {source_id}")
                if locator not in source.sections:
                    failures.append(f"{claim.claim_id}: unknown locator {locator} in {source_id}")
        if not any(claim.material for claim in valid_claims):
            failures.append("At least one material claim is required for this reference workflow")
    unsupported = [claim.claim_id for claim in valid_claims
                   if claim.material and claim.relationship in {
                       Relationship.UNSUPPORTED, Relationship.UNVERIFIABLE}]
    if unsupported:
        failures.append(f"Unsupported or unverifiable material claims: {', '.join(unsupported)}")
    if failures:
        return ReleaseDecision.WITHHOLD, failures
    conflicted = [claim.claim_id for claim in valid_claims
                  if claim.material and claim.relationship == Relationship.CONFLICTED]
    if conflicted:
        return ReleaseDecision.ESCALATE, [f"Conflicted material claims: {', '.join(conflicted)}"]
    inferred = [claim.claim_id for claim in valid_claims
                if claim.material and claim.relationship == Relationship.INFERRED]
    if inferred:
        return ReleaseDecision.ESCALATE, [f"Material inferences require review: {', '.join(inferred)}"]
    if profile.pal == PAL.RESTRICTED and human_approved is not True:
        return ReleaseDecision.ESCALATE, ["Qualified human approval required"]
    if workflow_review_required is True and human_approved is not True:
        return ReleaseDecision.ESCALATE, ["Workflow requires accountable human review"]
    nonmaterial_uncertainty = [claim.claim_id for claim in valid_claims
                              if not claim.material and claim.relationship in {
                                  Relationship.INFERRED, Relationship.UNSUPPORTED,
                                  Relationship.UNVERIFIABLE, Relationship.CONFLICTED}]
    if nonmaterial_uncertainty:
        notes = [f"Nonmaterial uncertainty must be disclosed: {', '.join(nonmaterial_uncertainty)}"]
        if allow_disclosure is not True:
            return ReleaseDecision.WITHHOLD, notes
        return ReleaseDecision.RELEASE_WITH_DISCLOSURE, notes
    return ReleaseDecision.RELEASE, []


def _canonical_json(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def build_receipt(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Snapshot a JSON payload and add a SHA-256 checksum.

    A checksum detects changes only when its original value is trusted. Anyone
    able to edit a receipt can recompute it. This is not a signature, attestation,
    append-only audit log or proof the input claims/checks were true.
    """
    if not isinstance(payload, Mapping):
        raise ValueError("Receipt payload must be a JSON mapping")
    reserved = {"integrity_hash", "receipt_id", "created_at", "policy_version"}
    if reserved.intersection(payload):
        raise ValueError("Receipt payload contains reserved envelope fields")
    # A JSON round trip prevents later caller mutation and rejects NaN/objects.
    body = json.loads(_canonical_json(dict(payload)))
    body.update({
        "receipt_id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy_version": POLICY_VERSION,
    })
    body["integrity_hash"] = sha256(_canonical_json(body)).hexdigest()
    return body


def verify_receipt(receipt: Mapping[str, Any]) -> bool:
    """Verify canonical checksum; this does not authenticate the receipt issuer."""
    if not isinstance(receipt, Mapping):
        return False
    body = dict(receipt)
    expected = body.pop("integrity_hash", None)
    if (not isinstance(expected, str) or len(expected) != 64
            or any(character not in "0123456789abcdef" for character in expected)):
        return False
    if any(not isinstance(body.get(name), str) or not body[name]
           for name in ("receipt_id", "created_at", "policy_version")):
        return False
    try:
        actual = sha256(_canonical_json(body)).hexdigest()
    except (TypeError, ValueError):
        return False
    return compare_digest(actual, expected)
