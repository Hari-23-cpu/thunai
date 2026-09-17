import pytest

from agents.intent_agent import INTENT_KEYWORDS, classify_intent


def test_classifies_billing():
    result = classify_intent("I want a refund for my last invoice")
    assert result["intent"] == "billing"
    assert result["confidence"] > 0


def test_classifies_technical_issue():
    result = classify_intent("The app keeps crashing, is it broken?")
    assert result["intent"] == "technical_issue"


def test_classifies_account_access():
    result = classify_intent("I cannot login, my password is not accepted")
    assert result["intent"] == "account_access"


def test_unknown_message_falls_back_to_general_inquiry():
    result = classify_intent("asdf qwerty zxcv")
    assert result["intent"] == "general_inquiry"
    assert result["confidence"] == 0.0


def test_empty_message_raises():
    with pytest.raises(ValueError):
        classify_intent("")


def test_whitespace_message_raises():
    with pytest.raises(ValueError):
        classify_intent("   ")


def test_intent_list_is_configurable():
    # Adding a new intent is a one-line change and classify_intent picks it up.
    INTENT_KEYWORDS["feature_request"] = ["please add", "would be nice"]
    try:
        result = classify_intent("Please add dark mode, it would be nice")
        assert result["intent"] == "feature_request"
    finally:
        del INTENT_KEYWORDS["feature_request"]
