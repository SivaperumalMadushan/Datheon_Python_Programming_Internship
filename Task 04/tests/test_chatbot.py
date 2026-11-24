"""
Test Suite for Datheon Support Bot
----------------------------------
Uses pytest to verify all functional requirements:
- Greeting detection (boundary checks)
- Single FAQ queries
- Combined greeting + FAQ
- Multi-intent queries
- Confidence scoring and clarification ('Did you mean' yes/no)
- Exit command handling
- Fallbacks for unanswerable queries
- Business hours logic with fake datetimes
- Data-driven extensibility (4th FAQ with zero code change)
- Error handling (missing files, malformed JSON)
"""

import datetime
import json
import pathlib
import pytest
from chatbot import (
    IST,
    BotSession,
    BotState,
    build_hours_status,
    load_dataset,
    respond,
    validate_dataset,
    DEFAULT_DATA_PATH,
)


@pytest.fixture
def dataset():
    """Fixture providing the default loaded FAQ dataset."""
    return load_dataset(DEFAULT_DATA_PATH)


@pytest.fixture
def session():
    """Fixture providing a fresh BotSession instance."""
    return BotSession()


# ---------------------------------------------------------------------------
# 1. Greetings & Word Boundaries
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "user_input,should_greet",
    [
        ("hi", True),
        ("GOOD MORNING!!", True),
        ("hello", True),
        ("good evening", True),
        ("this is a test", False),  # 'this' must not trigger 'hi'
        ("they said so", False),    # 'they' must not trigger 'hey'
    ],
)
def test_greetings(dataset, session, user_input, should_greet):
    reply = respond(user_input, session, dataset)
    if should_greet:
        assert "Hello!" in reply or "How can I help" in reply
    else:
        assert "Hello!" not in reply
        # Should drop into fallback
        assert "didn't quite understand" in reply


# ---------------------------------------------------------------------------
# 2. Single FAQ Matching
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "user_input",
    [
        "when are you open?",
        "what time do you close",
    ],
)
def test_faq_hours(dataset, session, user_input):
    reply = respond(user_input, session, dataset)
    assert "Monday through Friday" in reply
    assert "9:00 AM to 6:00 PM IST" in reply
    assert "Right now (IST) we are" in reply


@pytest.mark.parametrize(
    "user_input",
    [
        "how can I submit my project",
        "where do I upload my github link",
    ],
)
def test_faq_submit(dataset, session, user_input):
    reply = respond(user_input, session, dataset)
    assert "Student Workspace" in reply
    assert "GitHub repository link" in reply


@pytest.mark.parametrize(
    "user_input",
    [
        "when do I get my certificate",
        "certificate",
    ],
)
def test_faq_certificate(dataset, session, user_input):
    reply = respond(user_input, session, dataset)
    assert "Certificates are reviewed and issued" in reply
    assert "3-5 business days" in reply


# ---------------------------------------------------------------------------
# 3. Greeting Combined with Question
# ---------------------------------------------------------------------------

def test_greeting_with_question(dataset, session):
    user_input = "hi, what are your hours?"
    reply = respond(user_input, session, dataset)
    assert reply.startswith("Hello!")
    assert "Monday through Friday" in reply
    assert "Right now (IST) we are" in reply


# ---------------------------------------------------------------------------
# 4. Multi-Intent Matching
# ---------------------------------------------------------------------------

def test_multi_intent(dataset, session):
    user_input = "what are your hours and when will I get my certificate"
    reply = respond(user_input, session, dataset)
    assert "[Hours]" in reply
    assert "[Certificate]" in reply
    assert "Monday through Friday" in reply
    assert "3-5 business days" in reply


# ---------------------------------------------------------------------------
# 5. Fallback Responses
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("user_input", ["tell me a joke", "asdfgh"])
def test_fallback(dataset, session, user_input):
    reply = respond(user_input, session, dataset)
    assert "didn't quite understand" in reply
    assert "What are your hours of operation?" in reply
    assert "type 'help'" in reply


# ---------------------------------------------------------------------------
# 6. Exit Commands
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "user_input,should_exit",
    [
        ("bye", True),
        ("ok bye", True),
        ("QUIT", True),
        ("goodbye", True),
        ("how do I exit the internship", False),  # > 3 words, not an exit command
    ],
)
def test_exit(dataset, session, user_input, should_exit):
    reply = respond(user_input, session, dataset)
    if should_exit:
        assert session.state == BotState.ENDED
        assert "Goodbye" in reply
    else:
        assert session.state != BotState.ENDED


# ---------------------------------------------------------------------------
# 7. Empty Input
# ---------------------------------------------------------------------------

def test_empty_input(dataset, session):
    reply = respond("", session, dataset)
    assert "Please enter a question" in reply
    reply_spaces = respond("    ", session, dataset)
    assert "Please enter a question" in reply_spaces


# ---------------------------------------------------------------------------
# 8. Ambiguous Input & Clarification Flow (State: CLARIFYING)
# ---------------------------------------------------------------------------

def test_clarification_yes(dataset, session):
    ambiguous_input = "how do I exit the internship"
    # First turn: Bot prompts for clarification
    reply1 = respond(ambiguous_input, session, dataset)
    assert "Did you mean:" in reply1
    assert session.state == BotState.CLARIFYING
    assert session.pending_faq is not None

    # Second turn: User confirms with 'yes'
    reply2 = respond("yes", session, dataset)
    assert "Student Workspace" in reply2
    assert session.state == BotState.LISTENING
    assert session.pending_faq is None


def test_clarification_no(dataset, session):
    ambiguous_input = "how do I exit the internship"
    respond(ambiguous_input, session, dataset)
    assert session.state == BotState.CLARIFYING

    # User declines with 'no'
    reply2 = respond("no", session, dataset)
    assert "No problem!" in reply2
    assert session.state == BotState.LISTENING
    assert session.pending_faq is None


def test_clarification_other_input(dataset, session):
    ambiguous_input = "how do I exit the internship"
    respond(ambiguous_input, session, dataset)
    assert session.state == BotState.CLARIFYING

    # User replies with something else
    reply2 = respond("maybe later", session, dataset)
    assert "Please reply with 'yes' or 'no'" in reply2
    assert session.state == BotState.CLARIFYING


# ---------------------------------------------------------------------------
# 9. Business Hours with Mocked/Injected Datetime
# ---------------------------------------------------------------------------

def test_hours_saturday_closed(dataset, session):
    # Fake Saturday 14:00 IST
    fake_sat = datetime.datetime(2026, 11, 28, 14, 0, tzinfo=IST)
    reply = respond("what are your hours", session, dataset, current_time=fake_sat)
    assert "CLOSED" in reply
    assert "we reopen Monday at 9:00 AM" in reply


def test_hours_tuesday_open(dataset, session):
    # Fake Tuesday 10:00 IST
    fake_tue = datetime.datetime(2026, 11, 24, 10, 0, tzinfo=IST)
    reply = respond("what are your hours", session, dataset, current_time=fake_tue)
    assert "OPEN" in reply


# ---------------------------------------------------------------------------
# 10. Data-Driven Dynamic FAQ (4th FAQ with no code changes)
# ---------------------------------------------------------------------------

def test_data_driven_new_faq(dataset, session):
    new_faq = {
        "question": "Where can I find the internship stipend details?",
        "answer": "Internship stipend details are provided in your offer letter.",
    }
    dataset_copy = json.loads(json.dumps(dataset))
    dataset_copy["faqs"].append(new_faq)

    # Bot automatically derives keywords from the new question without any code change
    reply = respond("tell me about the stipend details", session, dataset_copy)
    assert "Internship stipend details are provided in your offer letter." in reply


# ---------------------------------------------------------------------------
# 11. Error Handling (Missing File & Invalid JSON)
# ---------------------------------------------------------------------------

def test_missing_dataset_file(tmp_path):
    missing_file = tmp_path / "does_not_exist.json"
    with pytest.raises(SystemExit) as exc_info:
        load_dataset(missing_file)
    assert exc_info.value.code == 1


def test_invalid_json_dataset(tmp_path):
    bad_json_file = tmp_path / "invalid.json"
    bad_json_file.write_text("{invalid_json_content", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        load_dataset(bad_json_file)
    assert exc_info.value.code == 1


def test_invalid_dataset_structure():
    bad_structure = {"greetings": "hello", "faqs": []}  # greetings must be a list
    with pytest.raises(SystemExit) as exc_info:
        validate_dataset(bad_structure)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# 12. Help / Topics Command
# ---------------------------------------------------------------------------

def test_help_menu(dataset, session):
    reply = respond("help", session, dataset)
    assert "Here are the topics I can help you with:" in reply
    for number, faq in enumerate(dataset["faqs"], start=1):
        assert f"{number}. {faq['question']}" in reply
