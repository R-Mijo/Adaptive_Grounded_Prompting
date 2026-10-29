# AGP release software verification

Verified on 29 October 2026 for version 0.2.0, using Python 3.12.14 on Windows.

## Results actually obtained

- **73 software tests passed.** The complete suite ran successfully from the repository root.
- Base-score boundary verification enumerates all 15,625 combinations of six scores from zero through four. Separate tests exercise the added assurance floors.
- The fixture demo released a supported example, withheld the same example with an expired source, accepted the original receipt checksum, and rejected a modified receipt.
- The actual 30-case input pack prepared 120 randomized generator packets and 30 planned verifier jobs at one repetition. Input and prompt checksums were recorded.
- An end-to-end offline screening rehearsal imported one deliberately malformed software fixture, counted the other 119 scheduled responses as missing, and kept semantic review pending. It prepared one bound verifier packet and recorded 29 unavailable drafts.
- The corrected case pack contains 30 unique case IDs, 23 safe-report RELEASE labels and seven ESCALATE labels. These are predefined gold labels, not model results.

## Defects covered

The suite covers strict score types and boundaries; conservative assurance floors; missing and false check results; unapproved, future, expired, unknown and mismatched sources; fabricated locators; empty and duplicate claims; material unsupported content, conflict and inference; workflow review and restricted-task approval; immutable snapshots; receipt tampering and malformed Unicode hashes; strict JSON parsing; common output fields; all required policy citations; missing-response denominators; pinned model IDs; duplicate/unknown job IDs; frozen input changes; hidden-category leakage; and verifier draft binding.

## What these results do not establish

No real model-provider calls were made. No independent model-performance study or blind semantic human review was completed. There are no measured AGP-versus-baseline improvements, hallucination rates, attack resistance rates, cost savings or customer results in this release.

Condition D is not connected end to end: the CLI prepares verifier packets, but does not ingest verifier responses or automatically combine them with the core gate. Source and locator checks are structural; trusted verification must establish support, complete claim coverage and actual independence. The workflow review and approval flags are trusted demonstration inputs, not authenticated authorization. The checksum is not a signature.

The test run above was local. The repository also includes an automated Python 3.11, 3.12 and 3.13 workflow; check the GitHub Actions page for its separate execution status. Local verification does not imply a remote workflow has passed.

## Reproduce

From the directory containing README.md:

```powershell
python -m unittest discover -s tests -v
python -m agp.cli demo
python -m agp.cli prepare --directory results/new-rehearsal --repeats 1 --seed 20261029
```

The preparation directory must not already exist. The demonstration and preparation make no model calls. Follow VALIDATION_PROTOCOL.md for the separate empirical study.
