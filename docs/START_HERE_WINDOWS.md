# Start AGP on Windows and publish a credible first release

This guide is for Marco A., the creator of AGP. Start by running the existing examples. You do not need to understand every line of Python to inspect a result or ask a contributor to reproduce a bug.

The first useful public milestone is a working research prototype with honest limits. The repository is [R-Mijo/Adaptive_Grounded_Prompting](https://github.com/R-Mijo/Adaptive_Grounded_Prompting). Software tests can be completed now. Claims about better AI answers require the separate model study described below.

## 1 Open the project folder

On the computer where this package was prepared, the folder is:

```text
C:\Users\14802\Documents\Codex\2026-10-29\i-built-a-prospectus-and-i-4\outputs\agp-starter
```

Open that folder in File Explorer. Click its address bar, type `powershell`, and press Enter. A terminal should open in that folder. You can also open PowerShell and paste:

```powershell
Set-Location -LiteralPath 'C:\Users\14802\Documents\Codex\2026-10-29\i-built-a-prospectus-and-i-4\outputs\agp-starter'
```

If you downloaded the project from GitHub, unzip it first and open the extracted folder containing README.md, agp, data, and tests. Do not run commands from inside the ZIP file or from the agp subfolder.

## 2 Select Python

On this computer the work was tested with the Python bundled with Codex. Paste these lines once into the PowerShell window:

```powershell
$agpPython = 'C:\Users\14802\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $agpPython --version
```

The `&` means run the program named by the variable. Keep this terminal open; the variable lasts for this window. No package installation or virtual environment is required.

On another computer, use an existing Python 3.11 or newer installation. Run `python --version`. If that works, replace `& $agpPython` in the commands below with `python`. A Store window or “not recognized” message means that command is not reaching a usable Python installation; use the bundled path on this computer, or obtain Python from [python.org](https://www.python.org/downloads/) on the other computer.

## 3 Run the software tests

```powershell
& $agpPython -m unittest discover -s tests -v
```

Success ends with `OK` and the number of tests run. If it ends with `FAILED` or an exception, save the complete output and fix the failure before calling the software checked. A passing result establishes behavior covered by these tests, not absence of every possible bug.

These tests include invalid scores, minimum assurance controls, missing check results, stale and fabricated source references, material claim handling, receipt changes, and malformed benchmark responses. See [the test report](TEST_RESULTS.md) for the actual release verification.

## 4 Run the demonstration

```powershell
& $agpPython -m agp.cli demo
```

Look for the current source result `RELEASE`, the stale source result `WITHHOLD`, a valid receipt before modification, and an invalid receipt after modification. The program uses a fictional source and hand-authored check results. No AI model is called and no money moves.

To understand the main behavior, read `agp/core.py`: TaskProfile chooses a control level, Source and Claim describe evidence, decide_release applies required controls, and the receipt functions snapshot and check a JSON record. Read [the methodology](METHODOLOGY.md) before changing the policy.

## 5 Know what was corrected

The original documents remain unchanged at their original locations. The revised public methodology and protocol are editable Markdown files under docs. GitHub displays these files as readable documents. To change wording, edit the .md file with a text editor, save it, and review the resulting change before uploading.

The release fixes an incorrect risk-level expectation, missing-check acceptance, source-lookup crashes, and several benchmark scoring defects. It adds minimum controls so a serious consequence cannot receive exploratory treatment simply because the other scores are low. The synthetic policy now distinguishes a safe preliminary report from expense approval or payment. The new cases were corrected before any model-effectiveness comparison.

For a detailed explanation of the weaknesses in the originals, read [the critical review](CRITICAL_REVIEW.md). For novelty and competing approaches, read [related work](RELATED_WORK.md).

## 6 Prepare an exploratory model study

Read [the protocol](VALIDATION_PROTOCOL.md) first. Choose and record a generator model version, verifier method, settings, budget, reviewer identities, and an analysis plan. Use only fictional cases. Keep gold answers away from generator and verifier prompts.

Start with one repeat to learn the process:

```powershell
& $agpPython -m agp.cli prepare --directory results/smoke --repeats 1 --seed 20261029
```

This creates 120 generator packets: 30 cases times four conditions. It does not submit them. For a smaller rehearsal, run a few selected packets but describe it as an incomplete smoke run. The scorer counts all scheduled missing responses, so a partial rehearsal is not a completed study.

For a separately frozen pilot after the rehearsal:

```powershell
& $agpPython -m agp.cli prepare --directory results/pilot --repeats 3 --seed 20261029
```

That schedules 360 generation runs and up to 90 later verifier calls. Five repeats schedule 600 plus up to 150 verifier calls. These are work counts, not a guarantee of statistical power. Do not start paid calls before setting a budget. This release has no automatic paid provider connection.

The new study folder contains study_manifest.json, frozen inputs, prompts, and RESPONSE_FORMAT.txt. A manifest is the list of scheduled jobs and their file checksums. Do not edit a frozen study. Create a new study folder and version if prompts, sources, or gold answers need correction.

## 7 Collect actual model responses

Use the same generator model and configuration for A, B, C and D. A model-provider API adapter is the practical route for a full study; a contributor can implement one against the JSONL interface without changing the gate. The initial release supports manual collection and response import.

For manual rehearsal, open a prompt file listed in the manifest, paste its entire content into a fresh model session, and save the complete raw response. Do not show the model the gold case file, and do not repair the response before recording it. Record its job ID and exact model identifier. D's first stage is a generator draft under the same instructions as C; it still needs the separate verification stage.

To record one answer without hand-escaping quotation marks, save it as `results/smoke/raw-J-000001.txt`, then run this example after replacing the model ID with the model you actually used:

```powershell
$agpRecord = [ordered]@{
    job_id = 'J-000001'
    model_id = 'REPLACE-WITH-ACTUAL-MODEL-ID'
    text = Get-Content -LiteralPath 'results/smoke/raw-J-000001.txt' -Raw
    latency_ms = $null
    input_tokens = $null
    output_tokens = $null
    error = $null
}
$agpRecord | ConvertTo-Json -Compress -Depth 20 | Add-Content -LiteralPath 'results/smoke/responses.jsonl' -Encoding utf8
```

Repeat with a different scheduled job ID and matching raw file for each response. Record a provider error with `text = $null` and `error = 'actual error description'`; keep the job in the record. Do not append the same job twice. If you accidentally duplicate a job, correct the operator log and preserve the raw originals; the importer will reject duplicates rather than pick one.

Unknown timing/token usage should stay null. Do not invent cost or latency. Store actual provider accounting separately when available. In a chat interface, an exact model snapshot may be unavailable; disclose this reproducibility limitation and use a pinned API model for a formal comparison.

## 8 Prepare D verifier packets

After collecting generator drafts:

```powershell
& $agpPython -m agp.cli verifier-packets --study results/smoke --responses results/smoke/responses.jsonl --out results/smoke-verifiers
```

The program prepares verification prompts for recorded D drafts and binds each to a draft checksum. It makes no verifier calls and does not apply verifier answers to the core gate. The independent reviewer or future adapter must validate actual coverage, combine trusted checks, call decide_release, and record the final delivery decision. The generator's proposed decision remains a proposal.

Use a fresh verification context and an appropriate checking method. Record the verifier's identity, raw findings, draft hash, checks performed, limitations and final decision separately. A different model may share errors with the first one. A structural validator cannot establish that a statement follows from a policy. See the protocol for the conventional-plus-verifier comparison that helps isolate the value of extra verification.

## 9 Screen responses and arrange human review

```powershell
& $agpPython -m agp.cli score --study results/smoke --responses results/smoke/responses.jsonl --out results/smoke-scores
```

Open scores.csv and summary.json in the output folder. The program checks formatting and mechanical matches of outcome labels, required cited sections, and proposed release values. Missing and failed responses remain in the scheduled denominator. A correctly typed answer can still be factually wrong; semantic review remains pending.

Ask at least two qualified independent reviewers to judge the complete output against the policy and expected_checks without seeing method labels. Prepare common-format copies with randomized review IDs and keep the mapping separately; this release does not automate reviewer blinding or calculate final semantic statistics. Reviewers must inspect text outside the claim ledger, missing facts, calculations and refusal to pay. Preserve independent scores before adjudicating disagreements. Report cases as the unit of evidence, accounting for repeated outputs within case. Do not claim AGP wins until the reviewed data support that comparison.

## 10 Publish or update GitHub

If the repository has already been populated, open [the repository](https://github.com/R-Mijo/Adaptive_Grounded_Prompting) and confirm README, LICENSE, agp, data, docs, tests and the test workflow are present. The Actions tab shows server-side test runs. A local pass does not imply a server-side pass.

To update a document through the website, open it, choose the pencil edit button, make the change, and propose it on a new branch. Review the comparison, then merge when checks pass. For code changes, make and test the change locally first. A branch is a separate proposed version; a commit is a saved set of changes; a pull request is the review page; merging makes the proposed change part of main.

If an upload is needed, use Add file then Upload files and upload the package contents into the repository root. Do not upload the enclosing ZIP, a nested agp-starter folder, results, __pycache__, local credentials, or the whole Documents directory. Include the hidden .github workflow folder; if the browser omits dotfolders, create `.github/workflows/tests.yml` through Add file then Create new file and paste that file's content. Preserve directory structure.

GitHub's instructions for [creating a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository) and [uploading files](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository) explain the current interface. The MIT license permits reuse and requires retention of its notice; it does not reserve exclusive rights to the broad methodology. See [GitHub's license guidance](https://choosealicense.com/licenses/mit/).

## 11 Use the next 24 hours well

| Time from starting | Concrete result |
|---|---|
| Hours 0 to 2 | Read the verdict and limitations, run tests and demo, inspect a receipt and a blocked result. |
| Hours 2 to 4 | Review the public README, attribution, MIT license, methodology and corrected cases. |
| Hours 4 to 6 | Confirm the GitHub upload and automated checks; fix any reproducible failure. |
| Hours 6 to 12 | Rehearse a few fresh baseline and AGP prompts; retain actual responses and record limitations. |
| Hours 12 to 24 | Invite independent testing, select a bounded workflow owner, and freeze a real pilot plan. |

Publication of the research prototype is achievable within this window. A credible, independently reviewed performance claim may take longer. Publish the prototype with that status rather than rushing an unsupported superiority claim.

## 12 Build recognition through useful evidence

Keep your creator credit visible, preserve version history, credit related work and contributors, and respond to reproducible issues. The strongest demonstration is a real failure caught with a clear explanation and reproducible evidence. Ask contributors for a provider adapter, a replication, or a specific missing control rather than asking someone to build an undefined enterprise platform.

A reasonable first business conversation is with a workflow owner who can show a recurring error and current review time. Measure whether the complete AGP process improves that outcome after counting model, human review, integration and maintenance costs. GitHub stars are attention; measured usefulness and retained users are stronger evidence of value.

## Common problems

| Message or observation | What to do |
|---|---|
| No module named agp | Open the folder containing README.md, then run the command again. |
| Python opens the Store | Use the bundled Python path in step 2 on this computer. |
| Study directory already exists | Use a new folder name; do not mix changed runs into a frozen study. |
| Frozen input or prompt changed | Restore the exact version or start a new versioned study; do not suppress the check. |
| Duplicate or unknown job ID | Compare the response log with the manifest; preserve raw originals and correct the operator record. |
| Multiple model IDs rejected | Separate changed models into distinct study blocks and rerun matched comparisons. |
| Poor scores after a few manual answers | Missing scheduled answers count as failures; this is an incomplete rehearsal, not a completed benchmark. |
| A model says PASS | That is a model assertion. Confirm independent evidence, coverage and required checks before release. |
| All software tests pass | Continue with model and human evaluation; no empirical quality improvement has been established. |
