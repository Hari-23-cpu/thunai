import csv
import json
import os
import re
from collections import Counter, defaultdict
from itertools import combinations

TAXONOMY_FILE = "data/golden/intent_taxonomy.json"
SAMPLE_FILE = "data/golden/intent_discovery_sample.csv"
JSON_REPORT = "data/golden/taxonomy_validation_report.json"
TXT_REPORT = "data/golden/taxonomy_validation_report.txt"
MD_REPORT = "data/golden/taxonomy_manual_review.md"

STOP_WORDS = {
    "the", "to", "i", "a", "and", "my", "is", "in", "it", "for",
    "you", "on", "with", "this", "of", "have", "your", "me", "that",
    "im", "am", "was", "so", "but", "be", "at", "can", "are", "if",
    "not", "do", "we", "as", "will", "just", "amazon", "help", "hi",
    "hello", "please", "thanks", "thank", "now", "been", "get", "its",
    "hey", "checking", "dm", "sent", "regards", "team", "service",
    "customer", "care", "want", "need", "issue", "problem", "order",
    "de", "no", "que", "y", "en", "el", "la"
}

GENERIC_WORDS = {
    "help", "please", "amazon", "order", "item", "product", "issue",
    "problem", "thanks", "thank", "hello", "hi", "hey", "there",
    "need", "want", "service", "customer", "care", "today", "now"
}

def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        value = value.strip()
        return [value] if value else []
    return [str(value).strip()]

def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"www\.\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = text.replace("’", "'")
    text = re.sub(r"[^\w\s']", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()

def tokenize(text):
    return normalize_text(text).split()

def meaningful_words(text):
    words = tokenize(text)
    return [
        word for word in words
        if len(word) > 2
        and word not in STOP_WORDS
        and word not in GENERIC_WORDS
        and not word.isdigit()
    ]

def phrase_in_text(text, phrase):
    text = normalize_text(text)
    phrase = normalize_text(phrase)

    if not text or not phrase:
        return False

    return bool(
        re.search(
            r"(?<!\w)" + re.escape(phrase) + r"(?!\w)",
            text,
            flags=re.UNICODE
        )
    )

def is_multilingual(text):
    return isinstance(text, str) and any(ord(ch) > 127 for ch in text)

def is_short_or_noisy(text):
    cleaned = normalize_text(text)
    return len(cleaned) < 35 or len(cleaned.split()) <= 4

def load_taxonomy():
    with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
        taxonomy = json.load(f)

    if "intents" not in taxonomy:
        raise ValueError(
            "intent_taxonomy.json does not contain an 'intents' list."
        )

    return taxonomy

def load_sample():
    messages = []

    with open(SAMPLE_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError("Discovery sample CSV has no header.")

        if "tweet_id" not in reader.fieldnames:
            raise ValueError(
                "Discovery sample must contain a 'tweet_id' column."
            )

        if "text" not in reader.fieldnames:
            raise ValueError(
                "Discovery sample must contain a 'text' column."
            )

        for row in reader:
            messages.append({
                "tweet_id": str(row.get("tweet_id", "")).strip(),
                "text": str(row.get("text", "") or "").strip()
            })

    return messages

def get_fields(intent):
    return {
        "intent_id": str(intent.get("intent_id", "")),
        "name": str(intent.get("name", "")),
        "description": as_list(intent.get("description")),
        "customer_problem": as_list(intent.get("customer_problem")),
        "inclusion": as_list(intent.get("inclusion_criteria")),
        "exclusion": as_list(intent.get("exclusion_criteria")),
        "signals": as_list(intent.get("common_signals")),
        "examples": as_list(intent.get("example_messages"))
    }

def contains_any(text, phrases):
    return [
        phrase for phrase in phrases
        if phrase_in_text(text, phrase)
    ]

def contains_any_phrase(text, phrases):
    for phrase in phrases:
        if phrase_in_text(text, phrase):
            return True
    return False

def intent_specific_rules(intent_id, text):
    text = normalize_text(text)

    rules = {
        "delivery_delay": {
            "positive": [
                "late", "delayed", "delay", "overdue", "past due",
                "hasn't arrived", "hasnt arrived", "haven't received",
                "havent received", "still waiting", "not arrived",
                "where is my package", "where is my order",
                "expected delivery", "delivery date", "delivery today",
                "not shipped", "not dispatched", "stuck in transit",
                "tracking hasn't changed", "tracking hasnt changed"
            ],
            "negative": [
                "delivered but", "marked delivered", "says delivered",
                "shows delivered", "received it", "arrived today",
                "arrived safely", "delivery was on time",
                "delivered on time"
            ]
        },
        "missing_delivered": {
            "positive": [
                "says delivered", "says it was delivered",
                "marked delivered", "shows delivered",
                "tracking says delivered", "tracking shows delivered",
                "delivery says delivered", "delivered but",
                "was delivered but", "it says it was delivered",
                "said delivered"
            ],
            "negative": [
                "delivery fee", "delivery charge", "delivery cost",
                "can be delivered", "deliver to my", "delivery date",
                "expected delivery", "free delivery"
            ]
        },
        "damaged_item": {
            "positive": [
                "damaged", "broken", "cracked", "defective", "faulty",
                "not working", "doesn't work", "doesnt work",
                "won't work", "wont work", "arrived damaged",
                "arrived broken", "damaged item", "broken item",
                "leaking", "leaked", "damaged package"
            ],
            "negative": [
                "wrong item", "wrong product", "wrong size",
                "return it", "return this", "refund only"
            ]
        },
        "refund_request": {
            "positive": [
                "refund", "refunded", "money back", "give my money back",
                "want my money", "money taken", "charged twice",
                "charged two times", "double charged", "unauthorized charge",
                "unauthorised charge", "charged for something",
                "charged me", "payment issue", "payment problem"
            ],
            "negative": [
                "delivery fee", "delivery charge", "price question",
                "how much", "shipping cost"
            ]
        },
        "cancellation_request": {
            "positive": [
                "cancel order", "cancel my order", "want to cancel",
                "please cancel", "can i cancel", "how do i cancel",
                "cancel it", "cancel this order", "cancellation"
            ],
            "negative": [
                "amazon cancelled", "you cancelled",
                "order was cancelled", "already cancelled"
            ]
        },
        "account_access": {
            "positive": [
                "can't login", "cant login", "cannot login",
                "can't log in", "cant log in", "cannot log in",
                "incorrect password", "forgot password", "password",
                "hacked account", "stolen password", "account hacked",
                "email address changed", "locked out", "can't access",
                "cant access", "account access"
            ],
            "negative": []
        },
        "prime_membership": {
            "positive": [
                "prime member", "prime membership", "amazon prime",
                "prime subscription", "prime account", "prime video",
                "prime renewal", "prime fee", "prime charge",
                "not a prime customer", "cancel prime"
            ],
            "negative": []
        },
        "technical_support": {
            "positive": [
                "app", "website", "browser", "ios", "iphone", "android",
                "kindle", "roku", "login error", "error message",
                "technical", "software", "screen", "device",
                "not working", "doesn't work", "doesnt work"
            ],
            "negative": [
                "damaged", "broken", "cracked", "refund",
                "cancel my order", "marked delivered"
            ]
        },
        "other_unclear": {
            "positive": [],
            "negative": []
        }
    }

    return rules.get(
        intent_id,
        {"positive": [], "negative": []}
    )

def score_intent(message, intent):
    cleaned = normalize_text(message)
    fields = get_fields(intent)
    intent_id = fields["intent_id"]

    if not cleaned:
        return 0.0, {
            "matched_rules": [],
            "matched_taxonomy_signals": [],
            "matched_inclusion": [],
            "matched_exclusion": []
        }

    rules = intent_specific_rules(intent_id, cleaned)

    score = 0.0
    evidence = {
        "matched_rules": [],
        "matched_taxonomy_signals": [],
        "matched_inclusion": [],
        "matched_exclusion": []
    }

    positive_rules = contains_any(cleaned, rules["positive"])
    negative_rules = contains_any(cleaned, rules["negative"])

    if positive_rules:
        score += 4.0
        evidence["matched_rules"].extend(positive_rules)

    if len(positive_rules) >= 2:
        score += 1.5

    if negative_rules:
        score -= 5.0
        evidence["matched_exclusion"].extend(negative_rules)

    specific_signals = []

    for signal in fields["signals"]:
        signal_words = meaningful_words(signal)

        if not signal_words:
            continue

        meaningful_matches = [
            word
            for word in signal_words
            if phrase_in_text(cleaned, word)
        ]

        if len(signal_words) == 1:
            if meaningful_matches:
                specific_signals.extend(meaningful_matches)
        else:
            if phrase_in_text(cleaned, signal):
                specific_signals.append(signal)

    specific_signals = [
        item for item in specific_signals
        if normalize_text(item) not in GENERIC_WORDS
    ]

    if specific_signals:
        score += min(2.0, len(specific_signals) * 0.75)
        evidence["matched_taxonomy_signals"].extend(
            specific_signals
        )

    inclusion_hits = []

    for criterion in fields["inclusion"]:
        criterion_words = meaningful_words(criterion)

        if not criterion_words:
            continue

        matched = [
            word
            for word in criterion_words
            if phrase_in_text(cleaned, word)
        ]

        if len(matched) >= 2:
            inclusion_hits.append(criterion)

    if inclusion_hits:
        score += min(2.0, len(inclusion_hits))
        evidence["matched_inclusion"].extend(inclusion_hits)

    for exclusion in fields["exclusion"]:
        exclusion_words = meaningful_words(exclusion)

        if not exclusion_words:
            continue

        matched = [
            word
            for word in exclusion_words
            if phrase_in_text(cleaned, word)
        ]

        if len(matched) >= 2:
            score -= 2.0
            evidence["matched_exclusion"].append(exclusion)

    score = max(0.0, score)

    return round(score, 2), evidence

def validate_message(message, taxonomy):
    text = message["text"]
    tweet_id = message["tweet_id"]

    scored = []

    for intent in taxonomy["intents"]:
        score, evidence = score_intent(text, intent)

        if score > 0:
            fields = get_fields(intent)

            scored.append({
                "intent_id": fields["intent_id"],
                "name": fields["name"],
                "score": score,
                "evidence": evidence
            })

    scored.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    if not scored:
        status = "no_match"
        best = None

    else:
        best = scored[0]
        second = scored[1]["score"] if len(scored) > 1 else 0
        margin = best["score"] - second

        if best["score"] >= 5.0 and margin >= 2.0:
            status = "clear_match"
        elif best["score"] >= 4.0 and margin >= 1.0:
            status = "weak_match"
        elif best["score"] >= 4.0 and margin < 1.0:
            status = "ambiguous_multiple_matches"
        elif best["score"] >= 2.0:
            status = "weak_match"
        else:
            status = "no_match"

    return {
        "tweet_id": tweet_id,
        "text": text,
        "status": status,
        "best_intent": best,
        "candidates": scored,
        "multilingual": is_multilingual(text),
        "short_or_noisy": is_short_or_noisy(text)
    }

def validate_sample(messages, taxonomy):
    return [
        validate_message(message, taxonomy)
        for message in messages
    ]

def build_summary(results):
    return {
        "total_messages": len(results),
        "clear_matches": sum(
            r["status"] == "clear_match"
            for r in results
        ),
        "weak_matches": sum(
            r["status"] == "weak_match"
            for r in results
        ),
        "ambiguous_matches": sum(
            r["status"] == "ambiguous_multiple_matches"
            for r in results
        ),
        "no_matches": sum(
            r["status"] == "no_match"
            for r in results
        ),
        "multilingual_messages": sum(
            r["multilingual"]
            for r in results
        ),
        "short_or_noisy_messages": sum(
            r["short_or_noisy"]
            for r in results
        )
    }

def build_intent_coverage(results, taxonomy):
    coverage = []

    for intent in taxonomy["intents"]:
        fields = get_fields(intent)
        intent_id = fields["intent_id"]

        best_matches = [
            r for r in results
            if r["best_intent"]
            and r["best_intent"]["intent_id"] == intent_id
        ]

        candidate_matches = [
            r for r in results
            if any(
                c["intent_id"] == intent_id
                for c in r["candidates"]
            )
        ]

        coverage.append({
            "intent_id": intent_id,
            "intent_name": fields["name"],
            "best_match_count": len(best_matches),
            "candidate_match_count": len(candidate_matches),
            "percentage_best_match": round(
                len(best_matches) / len(results) * 100,
                1
            ) if results else 0,
            "percentage_candidate_match": round(
                len(candidate_matches) / len(results) * 100,
                1
            ) if results else 0,
            "representative_examples": [
                {
                    "tweet_id": r["tweet_id"],
                    "customer_message": r["text"],
                    "score": r["best_intent"]["score"],
                    "evidence": r["best_intent"]["evidence"]
                }
                for r in best_matches[:5]
            ]
        })

    return coverage

def build_overlap_analysis(results):
    pairs = Counter()
    examples = defaultdict(list)

    for result in results:
        candidates = [
            c for c in result["candidates"]
            if c["score"] >= 4.0
        ]

        for a, b in combinations(candidates, 2):
            pair = tuple(
                sorted(
                    [a["intent_id"], b["intent_id"]]
                )
            )

            pairs[pair] += 1

            if len(examples[pair]) < 10:
                examples[pair].append({
                    "tweet_id": result["tweet_id"],
                    "customer_message": result["text"],
                    "intent_a": a["intent_id"],
                    "score_a": a["score"],
                    "evidence_a": a["evidence"],
                    "intent_b": b["intent_id"],
                    "score_b": b["score"],
                    "evidence_b": b["evidence"]
                })

    output = []

    for pair, count in pairs.most_common():
        if count >= 2:
            output.append({
                "intent_a": pair[0],
                "intent_b": pair[1],
                "overlap_count": count,
                "examples": examples[pair]
            })

    return output

def analyze_other_unclear(results, taxonomy):
    exists = any(
        intent.get("intent_id") == "other_unclear"
        for intent in taxonomy["intents"]
    )

    if not exists:
        return {
            "present": False,
            "message_count": 0,
            "percentage": 0,
            "examples": [],
            "observations": []
        }

    selected = [
        r for r in results
        if r["best_intent"]
        and r["best_intent"]["intent_id"] == "other_unclear"
    ]

    observations = []

    if selected:
        observations.append(
            "Review these examples manually because "
            "Other / Unclear should not become a catch-all "
            "for messages containing generic words such as help."
        )

    if len(selected) > len(results) * 0.20:
        observations.append(
            "Other / Unclear represents more than 20% of the "
            "sample and may indicate missing actionable intents "
            "or an overly broad taxonomy."
        )

    return {
        "present": True,
        "message_count": len(selected),
        "percentage": round(
            len(selected) / len(results) * 100,
            1
        ) if results else 0,
        "examples": [
            {
                "tweet_id": r["tweet_id"],
                "customer_message": r["text"],
                "score": r["best_intent"]["score"],
                "evidence": r["best_intent"]["evidence"]
            }
            for r in selected[:30]
        ],
        "observations": observations
    }

def analyze_no_matches(results):
    no_matches = [
        r for r in results
        if r["status"] == "no_match"
    ]

    unigrams = Counter()
    bigrams = Counter()

    for result in no_matches:
        words = meaningful_words(result["text"])

        unigrams.update(words)

        for i in range(len(words) - 1):
            bigrams[
                f"{words[i]} {words[i + 1]}"
            ] += 1

    themes = []

    for phrase, count in unigrams.most_common(15):
        examples = [
            {
                "tweet_id": r["tweet_id"],
                "customer_message": r["text"]
            }
            for r in no_matches
            if phrase_in_text(r["text"], phrase)
        ][:3]

        themes.append({
            "theme": phrase,
            "type": "unigram",
            "count": count,
            "examples": examples
        })

    for phrase, count in bigrams.most_common(15):
        examples = [
            {
                "tweet_id": r["tweet_id"],
                "customer_message": r["text"]
            }
            for r in no_matches
            if phrase_in_text(r["text"], phrase)
        ][:3]

        themes.append({
            "theme": phrase,
            "type": "bigram",
            "count": count,
            "examples": examples
        })

    themes.sort(
        key=lambda x: x["count"],
        reverse=True
    )

    return {
        "no_match_count": len(no_matches),
        "no_match_percentage": round(
            len(no_matches) / len(results) * 100,
            1
        ) if results else 0,
        "examples": [
            {
                "tweet_id": r["tweet_id"],
                "customer_message": r["text"]
            }
            for r in no_matches[:30]
        ],
        "recurring_themes": themes[:20]
    }

def analyze_multilingual(results):
    multilingual = [
        r for r in results
        if r["multilingual"]
    ]

    status_breakdown = Counter(
        r["status"]
        for r in multilingual
    )

    return {
        "total_multilingual": len(multilingual),
        "percentage_of_sample": round(
            len(multilingual) / len(results) * 100,
            1
        ) if results else 0,
        "status_breakdown": dict(status_breakdown),
        "examples": [
            {
                "tweet_id": r["tweet_id"],
                "customer_message": r["text"],
                "status": r["status"],
                "best_intent": (
                    r["best_intent"]["intent_id"]
                    if r["best_intent"]
                    else None
                )
            }
            for r in multilingual[:30]
        ]
    }

def analyze_delivery_delay(results):
    selected = [
        r for r in results
        if any(
            c["intent_id"] == "delivery_delay"
            for c in r["candidates"]
        )
    ]

    suspicious = []

    for result in selected:
        text = normalize_text(result["text"])

        if any(
            phrase_in_text(text, phrase)
            for phrase in [
                "delivered but",
                "marked delivered",
                "says delivered",
                "shows delivered"
            ]
        ):
            suspicious.append({
                "tweet_id": result["tweet_id"],
                "customer_message": result["text"],
                "reason": (
                    "Contains delivered-status language and "
                    "should be reviewed against missing_delivered."
                )
            })

    return {
        "candidate_count": len(selected),
        "best_match_count": sum(
            r["best_intent"]
            and r["best_intent"]["intent_id"] == "delivery_delay"
            for r in selected
        ),
        "suspicious_delivered_status_examples": suspicious[:20],
        "review_note": (
            "Delivery delay should cover late, overdue, stuck, "
            "or not-yet-received orders without delivered-status "
            "language. Delivered-status complaints should normally "
            "be reviewed under missing_delivered."
        )
    }

def build_intent_reviews(results, taxonomy):
    reviews = []

    for intent in taxonomy["intents"]:
        fields = get_fields(intent)
        intent_id = fields["intent_id"]

        best = [
            r for r in results
            if r["best_intent"]
            and r["best_intent"]["intent_id"] == intent_id
        ]

        candidates = [
            r for r in results
            if any(
                c["intent_id"] == intent_id
                for c in r["candidates"]
            )
        ]

        overlap_count = sum(
            len([
                c for c in r["candidates"]
                if c["score"] >= 4.0
            ]) > 1
            for r in candidates
        )

        notes = []

        if not best:
            notes.append(
                "No examples were selected as the best match."
            )

        if len(best) <= 2:
            notes.append(
                "Low representation in this discovery sample; "
                "manual review is required."
            )

        if overlap_count:
            notes.append(
                f"{overlap_count} candidate examples have "
                "high-confidence overlap with another intent."
            )

        reviews.append({
            "intent_id": intent_id,
            "intent_name": fields["name"],
            "best_match_count": len(best),
            "candidate_match_count": len(candidates),
            "percentage_best_match": round(
                len(best) / len(results) * 100,
                1
            ) if results else 0,
            "overlap_candidate_count": overlap_count,
            "notes": notes,
            "representative_examples": [
                {
                    "tweet_id": r["tweet_id"],
                    "customer_message": r["text"],
                    "score": r["best_intent"]["score"],
                    "evidence": r["best_intent"]["evidence"]
                }
                for r in best[:5]
            ]
        })

    return reviews

def build_recommendations(
    summary,
    overlaps,
    other_unclear,
    no_match_analysis,
    delivery_review
):
    recommendations = []

    if summary["clear_matches"] < 20:
        recommendations.append(
            "The heuristic validator is intentionally conservative. "
            "Do not interpret the low clear-match count as poor taxonomy "
            "quality; use it to identify examples for manual review."
        )

    if overlaps:
        top = overlaps[0]

        recommendations.append(
            f"Manually review the strongest overlap between "
            f"{top['intent_a']} and {top['intent_b']}."
        )

    if other_unclear["message_count"] > 0:
        recommendations.append(
            "Review Other / Unclear examples manually and ensure "
            "generic words such as help, please, or there are not "
            "driving intent assignment."
        )

    if no_match_analysis["no_match_count"] > 0:
        recommendations.append(
            "Review no-match examples for recurring actionable "
            "customer problems before adding any new intent."
        )

    if delivery_review["suspicious_delivered_status_examples"]:
        recommendations.append(
            "Review delivered-status examples because delivery_delay "
            "and missing_delivered require a clear boundary."
        )

    if summary["multilingual_messages"] > 0:
        recommendations.append(
            "Include multilingual examples in the manual golden-set "
            "review so taxonomy decisions are not English-only."
        )

    recommendations.append(
        "Do not use this heuristic report as classifier accuracy. "
        "The final taxonomy should be validated through manual labeling "
        "of the 150–250 example golden evaluation set."
    )

    return recommendations

def build_report(messages, taxonomy, results):
    summary = build_summary(results)
    coverage = build_intent_coverage(
        results,
        taxonomy
    )
    overlaps = build_overlap_analysis(results)
    other_unclear = analyze_other_unclear(
        results,
        taxonomy
    )
    no_match_analysis = analyze_no_matches(
        results
    )
    multilingual = analyze_multilingual(
        results
    )
    delivery_review = analyze_delivery_delay(
        results
    )
    intent_reviews = build_intent_reviews(
        results,
        taxonomy
    )

    recommendations = build_recommendations(
        summary,
        overlaps,
        other_unclear,
        no_match_analysis,
        delivery_review
    )

    return {
        "brand": taxonomy.get(
            "brand",
            "AmazonHelp"
        ),
        "taxonomy_file": TAXONOMY_FILE,
        "sample_file": SAMPLE_FILE,
        "sample_size": len(messages),
        "validation_method": (
            "Conservative heuristic validation using intent-specific "
            "rules, taxonomy signals, inclusion/exclusion criteria, "
            "and manual-review evidence. This is not classifier accuracy "
            "and does not replace human labeling."
        ),
        "summary": summary,
        "intent_coverage": coverage,
        "overlap_analysis": overlaps,
        "other_unclear_analysis": other_unclear,
        "no_match_analysis": no_match_analysis,
        "multilingual_analysis": multilingual,
        "delivery_delay_review": delivery_review,
        "intent_by_intent_review": intent_reviews,
        "recommendations": recommendations,
        "message_results": results
    }

def save_json_report(report):
    with open(
        JSON_REPORT,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            report,
            f,
            indent=2,
            ensure_ascii=False
        )

def save_text_report(report):
    summary = report["summary"]

    with open(
        TXT_REPORT,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(
            "=== TAXONOMY VALIDATION ===\n"
        )
        f.write(
            "Conservative heuristic validation for manual review.\n"
        )
        f.write(
            "This is NOT classifier accuracy.\n\n"
        )

        f.write("=== SUMMARY ===\n")

        for key, value in summary.items():
            f.write(
                f"{key}: {value}\n"
            )

        f.write(
            "\n=== INTENT COVERAGE ===\n"
        )

        for item in report["intent_coverage"]:
            f.write(
                f"\n{item['intent_name']} "
                f"({item['intent_id']})\n"
            )
            f.write(
                f"  Best matches: "
                f"{item['best_match_count']}\n"
            )
            f.write(
                f"  Candidate matches: "
                f"{item['candidate_match_count']}\n"
            )
            f.write(
                f"  Percentage: "
                f"{item['percentage_best_match']}%\n"
            )

        f.write(
            "\n=== OVERLAPS ===\n"
        )

        for overlap in report["overlap_analysis"][:10]:
            f.write(
                f"\n{overlap['intent_a']} <-> "
                f"{overlap['intent_b']} "
                f"({overlap['overlap_count']})\n"
            )

            for example in overlap["examples"][:3]:
                f.write(
                    f"  - {example['tweet_id']}: "
                    f"{example['customer_message']}\n"
                )

        f.write(
            "\n=== OTHER / UNCLEAR ===\n"
        )

        other = report["other_unclear_analysis"]

        f.write(
            f"Count: {other['message_count']}\n"
        )
        f.write(
            f"Percentage: {other['percentage']}%\n"
        )

        for example in other["examples"][:10]:
            f.write(
                f"- {example['tweet_id']}: "
                f"{example['customer_message']}\n"
            )

        f.write(
            "\n=== NO MATCHES ===\n"
        )

        no_match = report["no_match_analysis"]

        f.write(
            f"Count: {no_match['no_match_count']}\n"
        )
        f.write(
            f"Percentage: "
            f"{no_match['no_match_percentage']}%\n"
        )

        for theme in no_match["recurring_themes"][:15]:
            f.write(
                f"- {theme['theme']} "
                f"({theme['count']})\n"
            )

        f.write(
            "\n=== MULTILINGUAL ===\n"
        )

        multilingual = report["multilingual_analysis"]

        f.write(
            f"Count: "
            f"{multilingual['total_multilingual']}\n"
        )
        f.write(
            f"Percentage: "
            f"{multilingual['percentage_of_sample']}%\n"
        )
        f.write(
            f"Status breakdown: "
            f"{multilingual['status_breakdown']}\n"
        )

        f.write(
            "\n=== DELIVERY DELAY REVIEW ===\n"
        )

        delivery = report["delivery_delay_review"]

        f.write(
            f"Candidate count: "
            f"{delivery['candidate_count']}\n"
        )
        f.write(
            f"Best match count: "
            f"{delivery['best_match_count']}\n"
        )
        f.write(
            f"Suspicious delivered-status examples: "
            f"{len(delivery['suspicious_delivered_status_examples'])}\n"
        )
        f.write(
            f"Review note: "
            f"{delivery['review_note']}\n"
        )

        f.write(
            "\n=== INTENT REVIEWS ===\n"
        )

        for review in report["intent_by_intent_review"]:
            f.write(
                f"\n{review['intent_name']} "
                f"({review['intent_id']})\n"
            )
            f.write(
                f"  Best matches: "
                f"{review['best_match_count']}\n"
            )
            f.write(
                f"  Candidate matches: "
                f"{review['candidate_match_count']}\n"
            )

            for note in review["notes"]:
                f.write(
                    f"  Review: {note}\n"
                )

        f.write(
            "\n=== RECOMMENDATIONS ===\n"
        )

        for recommendation in report["recommendations"]:
            f.write(
                f"- {recommendation}\n"
            )

def save_markdown_report(report):
    with open(
        MD_REPORT,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(
            "# Taxonomy Manual Review\n\n"
        )

        f.write(
            "This report uses conservative heuristic evidence to "
            "identify taxonomy coverage, overlaps, no-match themes, "
            "and examples requiring manual review. It is not classifier "
            "accuracy.\n\n"
        )

        f.write(
            "## 1. Dataset and method\n\n"
        )
        f.write(
            f"- Brand: `{report['brand']}`\n"
        )
        f.write(
            f"- Taxonomy: `{report['taxonomy_file']}`\n"
        )
        f.write(
            f"- Discovery sample: `{report['sample_file']}`\n"
        )
        f.write(
            f"- Sample size: {report['sample_size']}\n"
        )
        f.write(
            "- Method: conservative intent-specific heuristic validation\n"
        )
        f.write(
            "- No LLM, embeddings, external APIs, or classifier training "
            "are used by this validator.\n"
        )

        f.write(
            "\n## 2. Summary\n\n"
        )
        f.write(
            "| Metric | Count |\n"
        )
        f.write(
            "|---|---:|\n"
        )

        for key, value in report["summary"].items():
            f.write(
                f"| {key} | {value} |\n"
            )

        f.write(
            "\n## 3. Intent coverage\n\n"
        )
        f.write(
            "| Intent | Best matches | Candidate matches | % best |\n"
        )
        f.write(
            "|---|---:|---:|---:|\n"
        )

        for item in report["intent_coverage"]:
            f.write(
                f"| {item['intent_name']} "
                f"| {item['best_match_count']} "
                f"| {item['candidate_match_count']} "
                f"| {item['percentage_best_match']}% |\n"
            )

        f.write(
            "\n## 4. Intent overlaps\n\n"
        )

        if not report["overlap_analysis"]:
            f.write(
                "No high-confidence overlap pairs met the reporting threshold.\n"
            )

        for overlap in report["overlap_analysis"][:10]:
            f.write(
                f"### {overlap['intent_a']} vs "
                f"{overlap['intent_b']}\n\n"
            )
            f.write(
                f"Overlap count: "
                f"{overlap['overlap_count']}\n\n"
            )

            for example in overlap["examples"][:5]:
                f.write(
                    f"- **{example['tweet_id']}**: "
                    f"{example['customer_message']}\n"
                )
                f.write(
                    f"  - `{example['intent_a']}` score: "
                    f"{example['score_a']}\n"
                )
                f.write(
                    f"  - `{example['intent_b']}` score: "
                    f"{example['score_b']}\n"
                )

        f.write(
            "\n## 5. Other / Unclear\n\n"
        )

        other = report["other_unclear_analysis"]

        f.write(
            f"- Count: {other['message_count']}\n"
        )
        f.write(
            f"- Percentage: {other['percentage']}%\n\n"
        )

        for observation in other["observations"]:
            f.write(
                f"- {observation}\n"
            )

        f.write(
            "\n### Examples\n\n"
        )

        for example in other["examples"][:15]:
            f.write(
                f"- **{example['tweet_id']}**: "
                f"{example['customer_message']}\n"
            )

        f.write(
            "\n## 6. No-match analysis\n\n"
        )

        no_match = report["no_match_analysis"]

        f.write(
            f"- No-match count: "
            f"{no_match['no_match_count']}\n"
        )
        f.write(
            f"- Percentage: "
            f"{no_match['no_match_percentage']}%\n\n"
        )

        f.write(
            "### Recurring themes\n\n"
        )

        for theme in no_match["recurring_themes"]:
            f.write(
                f"- `{theme['theme']}` "
                f"({theme['count']})\n"
            )

        f.write(
            "\nThese themes require manual review and should not "
            "automatically become new intents.\n"
        )

        f.write(
            "\n## 7. Multilingual analysis\n\n"
        )

        multilingual = report["multilingual_analysis"]

        f.write(
            f"- Multilingual examples: "
            f"{multilingual['total_multilingual']}\n"
        )
        f.write(
            f"- Percentage: "
            f"{multilingual['percentage_of_sample']}%\n\n"
        )

        f.write(
            "| Status | Count |\n"
        )
        f.write(
            "|---|---:|\n"
        )

        for status, count in multilingual["status_breakdown"].items():
            f.write(
                f"| {status} | {count} |\n"
            )

        f.write(
            "\n## 8. Delivery delay review\n\n"
        )

        delivery = report["delivery_delay_review"]

        f.write(
            f"- Candidate count: "
            f"{delivery['candidate_count']}\n"
        )
        f.write(
            f"- Best matches: "
            f"{delivery['best_match_count']}\n"
        )
        f.write(
            f"- Suspicious delivered-status examples: "
            f"{len(delivery['suspicious_delivered_status_examples'])}\n\n"
        )
        f.write(
            f"{delivery['review_note']}\n\n"
        )

        for example in delivery[
            "suspicious_delivered_status_examples"
        ][:10]:
            f.write(
                f"- **{example['tweet_id']}**: "
                f"{example['customer_message']}\n"
            )

        f.write(
            "\n## 9. Intent-by-intent review\n\n"
        )

        for review in report["intent_by_intent_review"]:
            f.write(
                f"### {review['intent_name']} "
                f"(`{review['intent_id']}`)\n\n"
            )
            f.write(
                f"- Best matches: "
                f"{review['best_match_count']}\n"
            )
            f.write(
                f"- Candidate matches: "
                f"{review['candidate_match_count']}\n"
            )
            f.write(
                f"- Percentage: "
                f"{review['percentage_best_match']}%\n"
            )

            for note in review["notes"]:
                f.write(
                    f"- Review note: {note}\n"
                )

            f.write(
                "\nRepresentative examples:\n\n"
            )

            for example in review[
                "representative_examples"
            ]:
                f.write(
                    f"- **{example['tweet_id']}**: "
                    f"{example['customer_message']}\n"
                )

        f.write(
            "\n## 10. Recommendations\n\n"
        )

        for recommendation in report["recommendations"]:
            f.write(
                f"- {recommendation}\n"
            )

        f.write(
            "\n## 11. Important limitation\n\n"
        )
        f.write(
            "This validator is for taxonomy discovery and manual review. "
            "It must not be reported as intent-classifier accuracy. "
            "The final classifier evaluation should use the manually "
            "labeled 150–250 example golden set.\n"
        )

def print_summary(report):
    summary = report["summary"]

    print("=" * 60)
    print("TAXONOMY VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Total messages:       "
        f"{summary['total_messages']}"
    )
    print(
        f"Clear matches:        "
        f"{summary['clear_matches']}"
    )
    print(
        f"Weak matches:         "
        f"{summary['weak_matches']}"
    )
    print(
        f"Ambiguous matches:    "
        f"{summary['ambiguous_matches']}"
    )
    print(
        f"No matches:           "
        f"{summary['no_matches']}"
    )
    print(
        f"Multilingual:         "
        f"{summary['multilingual_messages']}"
    )
    print(
        f"Short/noisy:          "
        f"{summary['short_or_noisy_messages']}"
    )

    print("\nIntent coverage:")

    for item in sorted(
        report["intent_coverage"],
        key=lambda x: x["best_match_count"],
        reverse=True
    ):
        print(
            f"  {item['intent_name']}: "
            f"{item['best_match_count']}"
        )

    print("\nHigh-confidence overlaps:")

    for overlap in report["overlap_analysis"][:5]:
        print(
            f"  {overlap['intent_a']} <-> "
            f"{overlap['intent_b']}: "
            f"{overlap['overlap_count']}"
        )

    print("\nReports written:")
    print(f"- {JSON_REPORT}")
    print(f"- {TXT_REPORT}")
    print(f"- {MD_REPORT}")

    print("=" * 60)

def main():
    print("Loading taxonomy...")
    taxonomy = load_taxonomy()

    print("Loading discovery sample...")
    messages = load_sample()

    print(
        f"Loaded {len(messages)} discovery examples."
    )

    print(
        "Running conservative heuristic validation..."
    )

    results = validate_sample(
        messages,
        taxonomy
    )

    print(
        "Building validation report..."
    )

    report = build_report(
        messages,
        taxonomy,
        results
    )

    os.makedirs(
        "data/golden",
        exist_ok=True
    )

    save_json_report(report)
    save_text_report(report)
    save_markdown_report(report)

    print_summary(report)

if __name__ == "__main__":
    main()