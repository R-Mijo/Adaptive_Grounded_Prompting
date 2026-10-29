# AGP internal critical review

Reviewed the supplied Business Methodology version 0.1 and Independent Testing and Validation Protocol version 0.1. Section references below refer to those originals. This is an internal consistency and implementation audit. It does not verify external market citations or establish novelty, commercial demand, legal protection, or model effectiveness.

## Judgment

The useful core is a practical, inspectable decision process between an AI draft and business use: task requirements, approved evidence, explicit checks, controlled release and a record of the decision. That is a credible project direction. The current documents describe a proposal and starter fragments, not a tested assurance architecture. The strongest public release would be an explicitly experimental reference implementation and benchmark invitation. Claims that nothing comparable exists, that the scoring is validated, that a receipt proves correctness, or that GitHub popularity is likely are not supported by the supplied evidence.

The documents already contain several appropriately cautious statements. Preserve those. Their weakest aspect is not lack of terminology; it is the gap between the claimed control model and what the starter code actually enforces.

## Release blocking implementation findings

### 1 Incorrect PAL boundary unit test

Business section 23 expects `TaskProfile(3,3,2,2,2,2).pal == PAL.OPERATIONAL`. The sum is 14, while section 6 and the policy engine assign 14 through 18 to PAL-3 Controlled. Fix the test to expect Controlled. Add tests for totals 4/5, 8/9, 13/14 and 18/19. This is an arithmetic inconsistency identifiable without any model experiment.

### 2 Empty and malformed check sets can authorize release

Business section 17 computes failures from the supplied check dictionary only. An empty dictionary produces no failures. Missing required evidence, source, authority or schema checks are never detected. Values such as the nonempty string `"FAIL"` are truthy and also pass. A caller can submit an empty claim list and no checks and obtain RELEASE if its claimed VII is high enough.

Correction: derive the complete required check set from trusted policy, reject missing/unknown/malformed checks, accept only exact typed PASS values, reject an empty/unvalidated output when material content is expected, and record the policy version used. A caller or model must not define which checks are required.

### 3 Protocol release engine trusts a top level verifier verdict too much

Protocol section 25 checks only `verification_result`, authority, and selected claim relationships. `verification_result=PASS` combined with `schema_check=FAIL`, `source_freshness_check=FAIL`, `injection_resistance_check=FAIL`, or omitted checks can still lead to RELEASE. A verifier supplied `correct_release_decision` can override the proposed decision without a separately enforced trusted rule set.

Correction: independently require every named applicable check to pass, validate enum/type/schema, and derive release from trusted findings and controls. Treat the verifier output as evidence of a check, not authority to waive the release policy. Malformed/unknown values must fail closed.

### 4 Unknown source checker raises instead of recording a controlled failure

Business section 22 appends an error for an unknown source ID, then unconditionally evaluates `approved_sources[source_id].current` for that same unknown source. That raises KeyError. Skip after logging the unknown ID or use safe lookup. Also validate approved status, applicable date/version, allowed purpose and locator; the `current` boolean alone is insufficient.

### 5 Claimed verification independence is not demonstrated assurance

Business section 20 returns the required VII value even though it does not establish that each check ran, succeeded, covered every material claim, or was operationally independent. Different models can share failure modes. A schema validator does not independently verify factual support. A submitted human review ticket is not approval.

Correction: record required versus achieved checks separately. Record verifier identity, method, coverage, evidence and pass/fail. Human approval requires a resolved, authorized approval record. Do not claim factual verification from a structural validator. Keep VII as a descriptive routing convention rather than an empirically calibrated numerical measure of independence.

### 6 Model controlled claim labels permit evasion

Both code sets trust a model's own claim list, relationship classification and `material` flag. An omitted unsupported sentence, an empty ledger, or a material unsupported claim labeled nonmaterial can evade blockers. Merely citing a real source ID does not prove the source supports the claim.

Correction: define materiality outside the model, independently inspect the delivered content for complete claim coverage, validate locators and source text, and report coverage limitations. The deterministic starter can enforce structural and explicit rule checks; it should not pretend to establish open ended semantic faithfulness.

### 7 Starter is not runnable as an application

Business section 21 references undefined `source_registry`, executor, serializer, verifier, audit store and helper functions. Protocol section 27 deliberately leaves ModelAdapter.generate unimplemented. Only two JSONL case examples are supplied in section 24, not complete machine readable data. PostgreSQL, YAML, schemas and Python fragments are separate sketches with mismatched field names (`text`/`claim_text`, `evidence_ids`/`source_ids`).

Correction: describe the originals as illustrative fragments. Publish one coherent, runnable small library and CLI, complete datasets and explicit provider interface. Do not claim an API is implemented until its dependencies and end to end behavior exist. Do not silently use a mock as evidence of model performance.

## Methodology findings

### 8 Additive PAL scores allow catastrophic risk dilution

Business section 6 permits consequence=4 and the other five dimensions=0 to total 4, hence PAL-0 with optional grounding and VII-0. This contradicts the narrative requirement for restricted handling of serious harm and irreversibility. Unvalidated ordinal scores are also being treated as equally weighted interval quantities. That is acceptable only as a heuristic with explicit limits.

Correction: keep the simple score as a provisional workload routing aid, and apply mandatory, documented floors for severe consequence, irreversible action, restricted data, unresolved controlling conflicts and organization specific rules. Preserve independent approval controls even if other scores are low. Calibrate classifications with reviewer agreement and incident data before claims of validity.

### 9 Source authority must be scoped to applicability

Business section 8 gives current organizational policy a globally higher rank than a customer contract or plan. That cannot be assumed across workflows. A current source also need not govern a transaction that occurred under an older applicable version. Conversely, a source labeled current in retrieved text is not authenticated by that label.

Correction: require workflow owner approved applicability rules with subject, jurisdiction, contract/plan, event date and version. Preserve prior versions for valid historical use. Distinguish expired for present tasks from applicable historical evidence. Equal authority conflicts should escalate. Treat source approval metadata as trusted registry data, not arbitrary text supplied by the model or requester.

### 10 Release decision mixes several different questions

Business section 11 combines final delivery states RELEASE/WITHHOLD with workflow actions CORRECT_AND_REVERIFY/RETRY. Protocol uses four final decisions but section 17 returns a fifth correction state. Expense eligibility, output quality, human approval needed, and authorization to transfer money are different axes.

Correction: separate business recommendation, final delivery decision, next workflow action and action authorization. Define whether the artifact being released is a preliminary report, decision, transaction or escalation packet. State transition precedence and bounded retry/correction counts. A safe preliminary refusal may be releasable even when the requested payment is prohibited.

### 11 Bare SHA-256 is not tamper proof or proof of correctness

Business section 12/16 and protocol section 25 hash serialized receipts. Anyone who can replace the record can recompute its hash. The hash neither authenticates the author nor establishes that the output is true. `default=str` can also hide unsupported data types rather than enforce a canonical schema.

Correction: call it a content checksum, document exact canonical serialization and verify it on load. Reserve authenticity/tamper evidence claims for an implemented signature or HMAC with separately managed keys and trusted append only storage. Even signed receipts attest to the recorded process, not factual correctness.

### 12 Conformance and commercial claims are premature

AGP Assured, certificates, market share, prices and financial projections in business sections 26 through 39 are proposed products and scenarios. No measured willingness to pay, renewal, delivered margin, incident reduction or independent assessment is supplied. Several overlapping benefits may double count the same avoided labor/rework.

Correction: lead the public repository with problem, working example, limitations, tests and contribution requests. Keep pricing and company projections in a clearly hypothetical separate business appendix. Require a measured baseline, fully loaded implementation/model/reviewer/maintenance costs and explicit benefit nonoverlap in ROI. The one minute saving across one million cases at $35/hour equals $583,333.33 before rounding; the original rounds hours first and reports $583,345. The difference is small, but compute currency from unrounded inputs.

## Benchmark validity findings

### 13 Baselines receive different tasks and output opportunities

Protocol sections 13 through 16 give A free text, B a five field text template and C/D JSON with claims and release decisions. Policy section 12 simultaneously requires every recommendation to contain material claims and a release decision. B has no release field at all. The scorer in section 26 assumes JSON and `policy_basis`; evaluating its schema/claim/release metrics directly against A/B unfairly penalizes their requested format. C/D also receive additional sources, while A/B templates include only current_policy and request, compromising stale/conflict tests.

Correction: use the same business objective, evidence package and common minimal machine readable output contract for every primary condition. Vary the assurance instructions/process being studied. Keep free text Basic as an illustrative separate baseline if desired. A secondary resource matched conventional plus independent verifier baseline helps distinguish the benefit of extra calls from the AGP vocabulary/structure.

### 14 Gold release labels contradict the written release rules

EXP-005, 027 and 028 require WITHHOLD merely because an injection is present. Protocol section 17 permits release when required checks pass; it does not require withholding every answer to an attacked input. A model that ignores a receipt instruction and correctly produces an Ineligible preliminary recommendation can satisfy the policy but fail the gold label. EXP-030 similarly mandates WITHHOLD when the request asks for payment, even if the assistant refuses payment and safely provides the permitted recommendation. This rewards blanket abstention rather than demonstrated safe task completion.

Correction: distinguish attempted/committed unauthorized behavior from a safely rejected request. Gold labels should score the actual artifact and actions. Decide and state whether a separate operational policy intentionally quarantines attacked inputs. If so, put that trusted policy in every condition and score safe refusal separately from attack success. Do not infer prompt injection resistance from the gate withholding everything.

### 15 Gold cases need shared assumptions and precise scope

Several requests omit facts needed for a full eligibility determination: EXP-008 does not state approved travel or the daily total; EXP-015 does not explicitly state approved travel; EXP-025 lacks rate period/tax scope and approval evidence; many cases omit dates/timeliness. EXP-017 says all route facts are supplied but does not supply actual date/purpose/origin/destination. EXP-007 introduces Finance handling not specified in the policy and assumes RELEASE_WITH_DISCLOSURE without identifying bounded nonmaterial uncertainty. EXP-004/021 must distinguish missing evidence of advance approval from evidence that required advance approval was never obtained; post purchase approval cannot satisfy a before purchase rule by implication. EXP-024 says 75 days late whereas EXP-023 says 75 days after transaction.

Correction: state explicit shared assumptions or supply complete structured case facts, and restrict expected conclusions to the line item/rule actually tested. Define partial reimbursement versus denial and exception handling in the policy. Add explicit expected calculations and unambiguous accepted outcome enums. Freeze corrected gold before model runs.

### 16 Current scorer does not measure the stated outcomes

Protocol section 26 never checks `expected_outcome`. It checks at least one expected section using intersection, not all necessary sections. Missing release decision is allowed because mismatch is checked only if `proposed` is truthy. An empty required section set always fails. JSON can parse to a scalar/list/null but is not validated as an object before `.get`. No JSON schema, enum, required field, duplicate claim ID, locator/support, arithmetic, freshness or evidence completeness check is actually implemented.

Substring scoring is especially unsafe: required `eligible` appears inside `ineligible`; prohibited `approved` flags safe language such as `not approved` or `approved business travel`; synonyms can be unfairly rejected. The included EXP-002 machine example prohibits `approved`, creating these false positives.

Correction: compare typed outcome/release fields, validate full schema, require the specified controlling sections, check calculations with decimal arithmetic and stable tolerances, and use human adjudication for semantic support/authority. Keyword flags can be triage signals, not definitive semantic truth tests. Track separate metric pass/fail fields rather than one composite `passed` flag.

### 17 Repeated outputs do not create hundreds of independent scenarios

Thirty hand selected cases with five repeats produce 150 outputs per method, but only 30 unique scenarios. No prospective power analysis supports detecting the proposed eight percentage point gain. Repeats are correlated within case and case variants may also be correlated by rule. Section 29 acknowledges aggregating repeats but does not define an analysis. Its zip-based helper silently truncates unequal lists and does not join by case ID.

Correction: predefine the primary case level unit and a paired method (e.g., compare per case repeat averaged rates with a case cluster bootstrap and paired effect estimates). Use McNemar only with one predefined binary result per matched case; do not flatten all repeats as independent observations. Validate nonempty, equal length and case aligned inputs. Report uncertainty, denominators and coverage limits; treat the initial 30-case pack as an exploratory pilot.

### 18 Primary metric definitions are not stable across documents

Business section 38 defines unsupported claim rate as material unsupported claims per output. Protocol section 2/31 defines unsupported claims divided by material claims. Both can be useful but they are different. Claim counts are generated by the treatment, so verbose outputs or missing claim lists change denominators and can game the result. Zero material claims, zero accepted outputs, zero positive escalation predictions, and zero baseline unsupported claims have no defined handling.

Correction: independently annotate material claims in the delivered artifact; report unsupported claims per output, proportion of outputs with any material unsupported claim, claim level rate and completeness. Define zero denominators as not applicable with counts, not perfect scores. Report accepted output quality alongside abstention/withholding and false escalation. Report relative reduction only where the baseline denominator is nonzero, plus absolute differences.

### 19 Security acceptance gate has an undefined denominator

Protocol section 34 permits no more than one prohibited release in 30 cases across aggregate analysis, yet only a few of those cases are attacks and each is repeated. It is unclear whether failures count per unique case, output, repeat or method. One unsafe outcome in a tiny selected set cannot establish a low production risk. A text representation of an invisible/encoded instruction in EXP-027 does not test actual invisible or encoded content.

Correction: report per attack family and per run denominators; require every material unauthorized action/release to receive review, with a strict no unresolved critical defect gate for a release candidate. Distinguish direct text injection tests from encoded, retrieval, tool or attachment attacks not implemented. Do not claim comprehensive injection prevention from this pack.

### 20 Blinding and order need more detail

Removing labels does not blind obvious JSON/receipt formats versus free text. Sequential loops case then method then repeat can confound condition with outages, load or model drift. Review correction time depends on reviewer skill, learning, tool support and familiarity.

Correction: use a common reviewer presentation for business correctness while evaluating traceability separately, report likely partial unblinding, randomize/interleave execution with a reproducible seed, record exact timestamps and provider-returned model identifiers, and balance reviewer assignments. Lock independent initial ratings before adjudication. Raw agreement needs kappa/alpha and missing-item handling. Section 30 also divides by zero for empty reviewer lists.

## Responsible 24 hour public release scope

Release an experimental alpha with a small working offline demo, regression tests for the defects above, complete synthetic policy/case assets, corrected definitions, related work, reproducibility steps and a clear statement that live model comparison and independent review are pending. Publish actual test evidence only for checks executed. Invite contributors to add provider adapters, benchmark runs and stronger verification. Avoid certification language, production safety claims, novelty absolutes and unsupported growth forecasts. A visible honest failure analysis will contribute more to credibility than a broad unsupported claim.

The release can be useful within 24 hours. Independent empirical validation, calibrated assurance levels, commercial proof and production readiness cannot honestly be compressed into that deadline.
