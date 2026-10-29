"""Offline command line entry points; no network or model credentials required."""

import argparse
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
from hashlib import sha256
from pathlib import Path

from .benchmark import prepare_study, score_study, verifier_packets
from .core import (
    REQUIRED_CHECKS, Claim, Relationship, Source, TaskProfile, build_receipt,
    decide_release, verify_receipt,
)


def demo() -> dict:
    now = datetime.now(timezone.utc)
    task = TaskProfile(2, 3, 1, 2, 1, 1)
    current = Source("DEMO-1", "Synthetic demo policy", "1.0", True,
                     now - timedelta(days=2), None,
                     {"4.1": "Approved business rideshare is eligible for preliminary recommendation."})
    ledger = [Claim("C-1", "Approved rideshare is preliminarily eligible.",
                    Relationship.DIRECT, ("DEMO-1",), ("4.1",))]
    # Trusted fixtures exercise software branches. They are not LLM judgments.
    checks = {key: True for key in REQUIRED_CHECKS}
    good, _ = decide_release(task, ledger, 2, checks, {"DEMO-1": current}, now=now)
    stale = Source("DEMO-1", "Synthetic demo policy", "0.9", True,
                   now - timedelta(days=2), now - timedelta(days=1), current.sections)
    blocked, reasons = decide_release(task, ledger, 2, checks, {"DEMO-1": stale}, now=now)
    ledger_json = [{"claim_id": item.claim_id, "claim_text": item.claim_text,
                    "relationship": item.relationship.value,
                    "source_ids": list(item.source_ids), "locators": list(item.locators),
                    "material": item.material} for item in ledger]
    draft = {"answer": ledger[0].claim_text, "claims": ledger_json}
    draft_text = json.dumps(draft, sort_keys=True, separators=(",", ":"), allow_nan=False)
    source_sections = dict(current.sections)
    source_text = json.dumps(source_sections, sort_keys=True, separators=(",", ":"), allow_nan=False)
    receipt = build_receipt({
        "task_id": "DEMO-1", "run_kind": "trusted software fixture",
        "profile": asdict(task), "pal": int(task.pal), "vii": 2,
        "draft": draft, "draft_sha256": sha256(draft_text.encode()).hexdigest(),
        "sources": [{"source_id": current.source_id, "version": current.version,
                     "approved": current.approved,
                     "effective_at": current.effective_at.isoformat(), "expires_at": None,
                     "sections": source_sections,
                     "sections_sha256": sha256(source_text.encode()).hexdigest()}],
        "checks": checks, "check_origin": "hard-coded fixture; no model or semantic validation",
        "decision": good.value, "limitations": [
            "Fixture checks exercise software branches and do not establish factual accuracy.",
            "Checksum is not an issuer signature or authenticated audit record."],
    })
    verified_before = verify_receipt(receipt)
    tampered = dict(receipt, decision="WITHHOLD")
    return {
        "kind": "SOFTWARE FIXTURE DEMO - not model performance or validation",
        "current_source_decision": good.value,
        "stale_source_decision": blocked.value, "stale_source_reasons": reasons,
        "receipt_valid_before_tamper": verified_before,
        "receipt_valid_after_tamper": verify_receipt(tampered),
        "example_receipt": receipt,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="AGP experimental offline reference tools")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="Run software fixtures; no model calls")
    prepare = commands.add_parser("prepare", help="Freeze inputs and generate randomized prompts")
    prepare.add_argument("--directory", type=Path, required=True)
    prepare.add_argument("--repeats", type=int, default=3)
    prepare.add_argument("--seed", type=int, default=20261029)
    for name in ("score", "verifier-packets"):
        command = commands.add_parser(name)
        command.add_argument("--study", type=Path, required=True)
        command.add_argument("--responses", type=Path, required=True)
        command.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "demo":
            result = demo()
        elif arguments.command == "prepare":
            manifest = prepare_study(arguments.directory, arguments.repeats, arguments.seed)
            result = {"study_directory": str(arguments.directory),
                      "generator_jobs": manifest["generator_jobs"],
                      "later_verifier_jobs": manifest["full_agp_verifier_jobs"],
                      "next": "Record model configuration, review/freeze gold standards, then run each prompt through one pinned model and preserve raw responses. No model has been called."}
        elif arguments.command == "score":
            result = score_study(arguments.study, arguments.responses, arguments.out)
        else:
            result = verifier_packets(arguments.study, arguments.responses, arguments.out)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"AGP error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
