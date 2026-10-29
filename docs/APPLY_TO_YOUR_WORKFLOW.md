# Connect AGP to a workflow

This release contains a working generic gate and offline evaluation tools. It does not contain a complete model-provider, expense-policy, or approval integration. Follow these steps to make a specific workflow concrete before expanding the system.

## 1 Name the artifact and its owner

Choose one output, such as a preliminary expense report. State who may receive it, what it may say, and what it may never do. Assign a workflow owner to resolve source conflicts and review exceptions. Keep report delivery separate from payments or changes to external systems.

## 2 Define approved evidence

Create Source records using trusted registry metadata, timezone-aware validity dates and a section-to-text mapping. Preserve the exact content or its digest. Do not let the generator mark its own citations approved or current. The reference date check is simple: historical applicability and version precedence still need your workflow's rules.

For case facts, explicitly identify their provenance and scope. A request narrative may establish what was asserted without establishing that an administrator actually approved an exception. Embedded instructions cannot change the workflow's governing policy.

## 3 Set controls before generation

Have the owner select the six TaskProfile inputs and review the resulting PAL. Treat the provisional scoring floors as a starting policy. Choose checks and verifiers with relevant coverage. Define how missing evidence, calculation defects and approval requirements affect release.

The gate's eight required check names are schema, evidence, authority, freshness, calculation, injection, logic and missing_information. Each must be a real boolean from a trusted checking process. A check that cannot be performed is not a pass. An inapplicable check needs a documented rationale outside the boolean field.

## 4 Generate a draft

An adapter sends only allowed instructions, source content and facts to the selected model, records the raw response and model configuration, and validates its structure. It preserves the exact draft for review. Model-proposed claim relationships, materiality and release decisions remain untrusted assertions.

The CLI's study prompts can be submitted manually or by a future provider adapter. The repository's response JSONL format is the import boundary. A provider adapter must preserve failures, usage and timing, respect the frozen schedule and keep gold labels out of the model request.

## 5 Verify the entire output

Use appropriate independent checks against the exact draft and sources. Inspect every material statement, including statements outside the claim ledger. A source-ID match checks identity; it does not establish support. Check arithmetic with a deterministic calculation where applicable. Record the verifier identity, method, coverage and limitations.

For D, verifier-packets prepares prompts bound to draft SHA-256 values. It does not ingest the answers. An integration still needs strict parsing, an exact draft-hash match, trusted findings, all eight check results, performed-versus-required VII, and the workflow-required review decision. Treat unverifiable or malformed responses as failures. A verifier's suggested release value cannot waive policy. If it recommends withholding or escalation, resolve that finding before any release rather than discarding it.

## 6 Apply the gate with trusted workflow decisions

Convert reviewed claims to Claim objects, pass the applicable Source registry, actual achieved VII, all eight checks and evaluation time to decide_release. Set workflow_review_required from the trusted business policy, not from the generator's preferred answer. Missing advance approval, Finance referral and other manual-review rules need this explicit integration.

For PAL 4 or workflow-required review, obtain qualified approval tied to the exact draft. The current human_approved boolean represents the result of that process for demonstration. It does not implement identity, authentication, qualification, expiry or authorization. Do not connect the boolean directly to a user-supplied or model-supplied field in production.

Withhold on a failed required check. Route escalation to an actual accountable reviewer. Only expose a draft when the permitted delivery decision is satisfied. An ESCALATE packet may be sent to the designated reviewer; it is not an approved operational result for the end recipient. Rechecking a changed draft is mandatory.

## 7 Keep a bound receipt

Use build_receipt with the exact draft or its digest, input and source identifiers/content digests, profile, required and achieved checks, policy version, verifier information, approval reference, final decision and limitations. Store the result with the reviewed artifacts. verify_receipt checks its checksum, not authenticity or truth. A production audit store needs separate access, signing and retention design.

## 8 Test against a baseline

First exercise allowed, missing, stale, conflicting, malformed and unauthorized cases. Then run the matched model comparison and independent human review in the protocol. Measure usable supported outputs and unnecessary escalation alongside blocked failures, cost and latency. A gate that blocks everything is not a useful success.

The first contributor milestone should be one tested adapter and one reproducible model study. Retrieval, authenticated approvals, final D ingestion, reviewer tooling, security review and a controlled external pilot remain separate milestones on the roadmap.
