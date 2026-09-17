# Decision Log

This document records the main non-obvious design decisions made while building the AmazonHelp AI support agent.

## 1. Selected AmazonHelp as the target brand

I selected `AmazonHelp` as the single target brand because it provides a large number of customer-support interactions and sufficient linked customer-to-brand responses for building both intent and historical-resolution components.

## 2. Used a subset of the full Twitter support dataset

The source dataset contains millions of tweets, but the assignment explicitly encourages subsampling. I prepared a focused AmazonHelp dataset instead of processing the entire corpus for every experiment, keeping the workflow practical and reproducible.

## 3. Limited the prepared data to 5,000 conversation threads

I used 5,000 AmazonHelp conversation threads for the working dataset. This provides enough conversational variety for experimentation while keeping local preprocessing, retrieval, and evaluation manageable.

## 4. Defined a small nine-intent taxonomy

I used nine intents:
`delivery_delay`, `missing_delivered`, `damaged_item`, `refund_request`, `cancellation_request`, `account_access`, `prime_membership`, `technical_support`, and `other_unclear`.

The goal was to keep the taxonomy small enough for reliable routing rather than creating a large number of fine-grained labels from noisy Twitter conversations.

## 5. Added `other_unclear` as a fallback intent

Real support messages frequently contain incomplete context, multiple issues, or requests that do not fit the selected taxonomy. `other_unclear` prevents the classifier from forcing every message into an inappropriate actionable category.

## 6. Protected the golden set from training leakage

The 200 golden examples were excluded before creating the silver training dataset. This prevents the classifier from training on the same examples used for final evaluation.

## 7. Used silver labels for classical-model training

The raw dataset does not contain the project's custom intent labels, so deterministic rules were used to create a silver-labelled training set. These labels are treated as weak supervision for model training rather than as ground truth.

## 8. Kept the golden evaluation set separate from silver training data

The golden set is used only for evaluation. This separation makes the comparison between the majority baseline, TF-IDF baseline, and AI intent agent more meaningful.

## 9. Used Majority Class as the trivial baseline

The majority-class classifier establishes the performance floor. It is intentionally simple and shows how much performance comes from the intent model rather than class distribution alone.

## 10. Used TF-IDF + Logistic Regression as the simple baseline

TF-IDF with Logistic Regression was selected because it is fast, interpretable, reproducible, and appropriate for short noisy text. It provides a stronger non-LLM baseline without requiring a large training infrastructure.

## 11. Used an LLM for the final intent agent

The final intent agent uses the defined taxonomy and an LLM to interpret customer language beyond exact keyword matches. This is particularly useful for conversational, noisy, and multilingual support messages.

## 12. Used historical retrieval before reply generation

The reply agent retrieves similar AmazonHelp customer conversations and their linked AmazonHelp responses. The retrieved examples provide concrete historical context for drafting replies instead of relying only on general model knowledge.

## 13. Kept reply generation separate from intent classification

Intent classification and reply generation solve different problems. Separating them makes each component easier to evaluate, modify, and debug independently.

## 14. Added capability and grounding safeguards

The agent is not given real Amazon account, order, or payment access. Therefore, it must not claim to have checked an order, processed a refund, changed an account, or completed another action that it cannot actually perform. When evidence is insufficient, the system falls back to supported guidance or escalation-oriented language.

## 15. Used an LLM judge for reply-quality evaluation

Traditional automated metrics are useful for classification but do not adequately capture conversational reply quality. A separate LLM judge evaluates correctness, grounding, helpfulness, brand consistency, and safety on a representative sample of generated replies.

## Final design principle

The overall system favors a bounded, evidence-aware support agent over an agent that attempts to complete actions it cannot actually perform. The architecture therefore combines classification, historical retrieval, conversational generation, and guardrails rather than relying on a single unrestricted LLM response.
