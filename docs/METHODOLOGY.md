# Adaptive Grounded Prompting methodology

Developed by Marco A. Version 0.2 experimental specification. 29 October 2026.

Adaptive Grounded Prompting (AGP) is a proposed method for deciding whether an AI-assisted task result has the evidence and checks required by a stated policy before it enters a business workflow. It combines task classification, evidence records, verification requirements, and an execution receipt. The intended benefit is more consistent review and a clearer explanation of delivery decisions. That benefit remains a hypothesis to evaluate.

This release is a bounded reference implementation. It does not establish improved model accuracy, production safety, regulatory compliance, or invention of the underlying practices. Read [related work](RELATED_WORK.md) before making originality claims. The [policy implementation](../agp/core.py) is authoritative for exact behavior.

## Scope and operating boundary

AGP separates generating an answer from deciding whether that answer may be delivered. The generator may propose a result, supporting claims, and a delivery decision. Application policy evaluates the supplied evidence and verification record. A model's declaration that its own answer is correct must not be treated as proof.

The initial policy workflow concerns preliminary recommendations. Releasing a recommendation does not approve a payment, alter an account, waive a policy, or authorize another business action. Those actions need their own permissions and controls. An integration must prevent rejected drafts from reaching the intended recipient or triggering a tool. Calling a gate without enforcing its result provides no release control.

## Three phases and nine stages

1. **Qualify — Frame.** Record the objective, recipient, allowed actions, prohibited actions, required output, and criteria for a usable result. Identify the accountable workflow owner.
2. **Qualify — Classify.** Score the six task characteristics below. A responsible person should review consequential classifications; the model must not be free to lower its own controls.
3. **Qualify — Assign.** Calculate the base Prompt Assurance Level (PAL), apply mandatory floors, and establish required verification and approval.
4. **Compile — Ground.** Select applicable sources and preserve their identity, version, approval status, validity period, and usable locators. Resolve applicability before treating one source as controlling.
5. **Compile — Configure.** Choose generation, retrieval, calculations, deterministic rules, and verification methods suited to the task. Define what each check can establish.
6. **Compile — Constrain.** Enforce access and action permissions outside the model. Specify stop conditions, output structure, reviewer responsibility, and bounded correction or retry handling.
7. **Assure — Execute.** Produce a draft and preserve the relevant inputs, source versions, model and prompt identifiers, and tool results.
8. **Assure — Verify.** Perform the required checks against the actual draft and evidence. Record findings rather than copying generator assertions.
9. **Assure — Release.** Apply the gate, enforce the decision, and record a receipt bound to the reviewed task and result. Changes to the reviewed result require another decision.

## Task profile and provisional PAL policy

`TaskProfile` uses six integer dimensions, each from 0 through 4. Booleans, missing values, strings, and values outside that range are invalid. Scores are policy inputs, not measured probabilities of loss.

| Dimension | Lower score means | Higher score means |
|---|---|---|
| Consequence | Disposable output or minor inconvenience | Financial, contractual, regulated, or serious harmful impact |
| Evidence dependence | Little external evidence needed | Current authoritative evidence or multiple controlling sources |
| Autonomy | Draft or recommendation | Business action, particularly without prior review |
| Reversibility | Easy to discard or correct | Difficult or effectively impossible to reverse |
| Data sensitivity | Public or ordinary internal information | Personal, regulated, or highly restricted information |
| Ambiguity | Clear instructions and sufficient facts | Material missing facts, conflict, or uncertainty |

Add the six values to obtain the base level:

| Total | Base PAL |
|---|---|
| 0–4 | 0 |
| 5–8 | 1 |
| 9–13 | 2 |
| 14–18 | 3 |
| 19–24 | 4 |

Apply these provisional minimum levels after calculating the total:

- Consequence 4 or reversibility 4 requires PAL 4.
- Consequence 3, data sensitivity at least 3, autonomy at least 3, or ambiguity 4 requires at least PAL 3.
- Evidence dependence at least 3 requires at least PAL 2.

The highest applicable level controls. Floors prevent an extreme characteristic from being cancelled by low scores elsewhere. They are engineering choices, not validated universal thresholds. Calibration should examine reviewer agreement, missed hazards, unnecessary escalation, and workflow outcomes. Local policy can require stronger controls.

## Evidence and authority

Maintain a source registry and a claim ledger. A registry entry should identify the approved source, relevant version, validity interval, owner, content digest, and available locators. A ledger should identify the exact material claim, its relationship to evidence, supporting source identifiers, and locators precise enough for a reviewer to find the support.

Authority depends on the task and jurisdiction. A universal list that always places organizational policy above a contract can be wrong. Establish applicable authority with the workflow owner; conflicting controlling documents may require qualified review. A source identifier or citation is not itself evidence that the source entails the claim.

The gate requires a nonempty ledger with at least one material claim and unique claim identifiers. It blocks referenced sources that are unapproved, unknown, expired, or not yet effective, and references to unknown locators. Direct and derived claims require paired source identifiers and locators. Unsupported or unverifiable material claims block release; material conflicts and inferences require escalation after mandatory checks pass. Derived claims also need the calculation or transformation checked.

Freshness uses a timezone-aware evaluation time; effective dates are inclusive and expiry dates exclusive. Date checks do not establish that a document is the latest version, applicable to this customer, or free of conflicting amendments. Maintain those facts through a trusted process.

## Verification requirements

The minimum Verification Independence Index (VII) equals PAL: PAL 0 requires at least VII 0, through PAL 4 requiring at least VII 4. The conceptual scale is:

| VII | Intended configuration |
|---|---|
| 0 | No material verification |
| 1 | Generator performs a same-pass check |
| 2 | Separate verification call with fresh context |
| 3 | An appropriate technical verification method distinct from generation |
| 4 | Technical verification plus qualified human approval |

This ordinal index is a routing shorthand. It is not an assurance score. Verification has several dimensions: different reasoning method, separate evidence, model diversity, organizational independence, and relevant coverage. Different models can share errors. A deterministic schema validator can establish structure while missing a fabricated factual claim. A calculator validates arithmetic, not policy interpretation. Neither justifies treating the whole answer as independently verified.

At every PAL, the starter requires explicit boolean results for `schema`, `evidence`, `authority`, `freshness`, `calculation`, `injection`, `logic`, and `missing_information`. Missing values, strings such as `"PASS"`, and truthy substitutes fail. Assess inapplicable checks under a documented rule and retain the reason; do not omit them.

The starter accepts supplied check results and VII. It does not establish that a real verifier performed the checks or has sufficient independence and coverage. Integrations must supply trusted results and preserve their provenance. Likewise, a boolean human-approval input is not authenticated approval. PAL 4 requires human approval, but reviewer identity, qualification, authority, approval expiry, and binding to the exact draft remain integration responsibilities.

An integration must also set the trusted `workflow_review_required` flag when its business policy requires manager, executive, Finance, or other designated review. The core does not interpret expense prose to discover that requirement. If the flag is true and qualified human approval is absent, the gate escalates. Human approval does not clear failed checks, unresolved material conflict, or material inference. This flag governs review of the report; it never grants payment authority.

## Decisions and correction handling

| Decision | Meaning and next action |
|---|---|
| `RELEASE` | Deliver only the reviewed recommendation within its stated scope. |
| `RELEASE_WITH_DISCLOSURE` | Deliver with a specific recorded limitation when all required controls pass and uncertainty is nonmaterial. |
| `ESCALATE` | Route the draft and evidence to an accountable reviewer; do not deliver it as an approved operational result. |
| `WITHHOLD` | Do not deliver a usable result because required evidence, checks, or assurance are missing or failed. |
| Correct and reverify | A lifecycle action: revise the artifact and repeat the required checks before making another terminal decision. |
| Retry | A lifecycle action: attempt execution again only under a predefined limit and record every attempt. |

The core gate makes terminal delivery decisions; it does not implement the correction/retry workflow, a reviewer queue, or incident handling. Human escalation is unresolved until an integration defines an owner, routing destination, response time, and what happens if review is unavailable. Escalating must never silently become approval. Fixing one issue does not clear unrelated failed checks, and adding a disclosure does not make a material unsupported claim acceptable.

## Receipts and integrity

A receipt records the decision context. Preserve enough information to connect it to the exact input, draft, sources, prompt/model versions, checks, and approvals. Store content digests or other stable identifiers in the context when the receipt API does not store the full artifacts. A receipt that cannot be tied to the reviewed draft cannot justify delivering a later edited draft.

The starter's SHA-256 value is a checksum over a canonical representation. It can detect a change when compared with a trusted original digest. Someone able to change the receipt can also recompute its hash. The checksum does not establish author identity, authentic approval, completeness, correctness, or an immutable audit history. Signing, trusted timestamping, restricted storage, and retention controls are separate work.

## Evaluation and business hypotheses

Evaluate the complete process against a strong conventional baseline using the same policy, cases, and outcomes. Keep development examples separate from held-out evaluation cases. Report generator accuracy separately from verification and gate behavior; counting every withheld result as a success would hide an unusable system. Measure unsupported claims, incorrect releases, unnecessary withholding and escalation, reviewer effort, latency, and total cost. Software checks alone do not demonstrate better AI behavior. See the evaluation protocol supplied with this project for study details.

The offline tools prepare and screen generation drafts and prepare separate verifier packets. They do not ingest verifier results, authenticate review, or run a completed Full AGP study. Those integrations and independent semantic ratings remain required before reporting D's final release performance.

The initial business hypothesis is that workflow owners will value reduced review effort and clearer evidence records enough to adopt this layer. A second hypothesis is that a portable implementation will help developers add these controls to existing tools. Both require interviews and controlled pilots. No market size, valuation, price, revenue, or GitHub popularity is established by this release. A sensible first milestone is one bounded workflow whose owner can compare AGP with the current process and publish the tradeoffs, including failures.
