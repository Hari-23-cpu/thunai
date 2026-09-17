# Hiver AI Support Agent — Project Instructions

## Project Goal

Build the Hiver SDE Intern take-home assignment: an AI customer-support agent trained/evaluated using the Customer Support on Twitter dataset.

The system should:

1. Classify an incoming customer message into a small intent taxonomy.
2. Draft a support reply grounded in historical AmazonHelp resolutions.
3. Decide whether to auto-handle or escalate, with a clear reason.
4. Provide reproducible evaluation and evidence.

## Selected Brand

AmazonHelp

Do not change the selected brand unless explicitly requested.

## Dataset

Primary dataset:

Customer Support on Twitter — thoughtvector/customer-support-on-twitter

Raw file:

data/raw/twcs.csv

The complete raw dataset should NOT be committed to GitHub.

Prepared dataset:

data/processed/support_tweets.csv

Current preparation:

* Selected brand: AmazonHelp
* Conversation threads: 5,000
* Prepared tweets: approximately 23,927
* Customer/inbound messages: approximately 12,842
* AmazonHelp/outbound messages: approximately 11,066
* Customer messages with explicit AmazonHelp response linkage: approximately 9,731

These numbers are current project facts. If code changes the preparation pipeline, rerun the analysis scripts before updating documentation.

## Current Taxonomy

The current taxonomy contains 9 intents:

* delivery_delay
* missing_delivered
* damaged_item
* refund_request
* cancellation_request
* account_access
* prime_membership
* technical_support
* other_unclear

Do NOT modify the taxonomy automatically.

Taxonomy changes must be based on evidence from the human-labelled golden set or explicit project discussion.

## Golden Evaluation Set

The assignment requires a 150–250 example HAND-LABELLED evaluation set.

Target:

200 examples.

File:

data/golden/golden_set.csv

LLM-assisted labels may be used as suggestions, but they must NOT be described as hand labels until manually verified.

The final `gold_intent` must represent the human-verified label.

## Important Evaluation Rule

Never claim classifier accuracy from:

* heuristic taxonomy validation
* LLM-generated labels
* automatically generated labels
* discovery samples

Actual classifier metrics should be calculated against the manually verified golden set.

## Current Discovery Data

Discovery sample:

data/golden/intent_discovery_sample.csv

This contains 400 examples and is for taxonomy discovery/analysis.

It is NOT the final golden evaluation set.

## Architecture

Preferred pipeline:

Twitter Support Data
↓
Brand Filtering
↓
Data Cleaning
↓
Intent Taxonomy
↓
Intent Classifier
↓
Historical Response Retrieval
↓
LLM
↓
Reply + Evidence
↓
Auto-handle / Escalate
↓
Evaluation

## Baselines

The evaluation must include at least:

1. Majority-class baseline
2. TF-IDF + Logistic Regression baseline

Compare the final classifier against these baselines.

Use appropriate metrics including:

* accuracy
* macro-F1
* per-intent precision
* per-intent recall
* per-intent F1
* confusion matrix

Do not report accuracy alone.

## Reply Generation

Replies must be grounded in retrieved historical support conversations/resolutions.

The LLM should not invent Amazon policies, refunds, delivery promises, or procedures that are unsupported by retrieved evidence.

Keep retrieved evidence associated with each generated reply so that evaluation can determine whether the response is grounded.

## Escalation

The escalation decision should be explicit and explainable.

Potential escalation signals include:

* low classifier confidence
* insufficient historical evidence
* sensitive billing/payment situations
* security/account concerns
* customer explicitly requesting a human
* cases outside the supported taxonomy

Do not hard-code arbitrary thresholds without documenting why they were chosen.

## Code Change Rules

Before making changes:

1. Inspect the relevant file(s).
2. Understand the existing implementation.
3. Make the smallest change necessary.
4. Do not rewrite unrelated files.
5. Preserve working functionality.
6. Run the relevant tests after changes.

For a small bug, prefer a small targeted fix instead of a full rewrite.

Do not modify data files unless the task explicitly requires it.

Do not regenerate the raw dataset.

## Token / Context Efficiency

Avoid reading the entire repository for a small change.

For a task affecting one file:

* inspect only that file and directly related code
* modify only the necessary section
* run the relevant test/script
* show a concise summary of the changes

Do not repeatedly recreate files that already exist.

Do not replace working code with a completely new implementation unless explicitly requested.

## Data Integrity

Never fabricate:

* dataset statistics
* customer messages
* historical resolutions
* evaluation results
* classifier metrics
* taxonomy examples
* benchmark results

If a value has not been measured, clearly label it as unknown or an estimate.

## Files That Matter

### Data preparation

scripts/brand_analysis.py
scripts/prepare_data.py
scripts/analyze_prepared_data.py

### Taxonomy

scripts/discover_intents.py
scripts/sample_intent_examples.py
data/golden/intent_taxonomy.json

### Evaluation

evaluation/

### Agent

agents/
backend/
memory/

## Current Project Status

Completed:

* Raw Twitter dataset downloaded
* AmazonHelp selected
* 5,000 conversation threads prepared
* Prepared dataset analyzed
* 400-example intent discovery sample created
* Initial 9-intent taxonomy created
* Taxonomy validation performed

Current next task:

Build a 200-example manually verified golden evaluation set.

Expected files:

scripts/build_golden_set.py
data/golden/golden_set.csv
data/golden/GOLDEN_SET_README.md

After the golden set is labelled:

1. Analyze actual intent distribution.
2. Reassess taxonomy.
3. Build majority baseline.
4. Build TF-IDF + Logistic Regression baseline.
5. Build final classifier.
6. Build historical-response retrieval.
7. Build grounded reply generation.
8. Build escalation logic.
9. Evaluate the complete system.
10. Document failure modes and misleading headline metrics.

## Interview Readiness

All implementation decisions should be understandable by the candidate.

Do not introduce unnecessary frameworks, abstractions, or complex infrastructure when a simpler implementation is sufficient.

Prefer readable Python and explainable components.

The candidate must be able to explain:

* why AmazonHelp was selected
* how conversations were reconstructed
* how intents were designed
* why the golden set is valid
* why the baselines were chosen
* how retrieval works
* how hallucination is reduced
* how escalation works
* why the evaluation metrics were selected
* limitations and failure modes

## Do Not Do

Do NOT:

* claim the candidate built the system entirely without AI assistance
* fabricate evaluation results
* fabricate historical support policies
* call the 400 discovery examples a golden set
* call LLM-generated labels "hand-labelled"
* change taxonomy merely because a heuristic validator has many no-match cases
* process the entire 3M-row dataset unnecessarily
* commit the 492 MB raw dataset
* add unnecessary dependencies
* rewrite unrelated working files

## Preferred Working Style

For each task:

1. State what you inspected.
2. Make the smallest appropriate change.
3. Run a relevant test or script.
4. Report what changed.
5. Report the actual result.
6. If something is uncertain, say so instead of guessing.
