# Contributing to AGP

AGP was created by Marco A. This repository is an experimental reference implementation. Contributions should improve reproducibility, clarity, or a concrete control; claims of improved model performance require evidence.

1. Open an issue describing the problem, expected behavior, observed behavior, and a minimal synthetic example. Do not include personal records or credentials.
2. Propose a focused change on a branch. Explain which policy version and tests it affects.
3. Run `python -m unittest discover -s tests -v` and `python -m agp.cli demo` from the repository root.
4. For changes to cases, gold answers, prompts, or scoring, document the reason before running a new experiment. Preserve the old version and rerun every affected comparison condition.
5. Include failure cases and tradeoffs in performance reports. Record model versions, source and prompt hashes, all scheduled outcomes, and review methods.

The most useful initial projects are provider adapters, reviewer tooling, independent benchmark replication, authenticated approvals bound to exact output hashes, trusted source applicability rules, and integration with established orchestration tools. Do not add a new assurance claim based only on a unit test.

Contributions to this repository are made under its MIT license. Keep creator attribution and give contributors appropriate credit in commit history and release notes. The maintainer should review changes before merging.
