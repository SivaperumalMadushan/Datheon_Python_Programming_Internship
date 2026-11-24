"""
Datheon Support Bot
-------------------
A data-driven, rule-based customer support chatbot written in Python.
Uses keyword matching, regular expressions, and weighted overlap scoring
to answer customer inquiries without external machine learning libraries.

Author: Python Intern
"""

import dataclasses
import datetime
import enum
import json
import math
import pathlib
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Constants & Configurations
# ---------------------------------------------------------------------------

# Path to the default FAQ dataset relative to this script
DEFAULT_DATA_PATH = pathlib.Path(__file__).resolve().parent / "data" / "sample_faq.json"

# Fixed IST timezone: UTC + 05:30 (do not use zoneinfo as per requirements)
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
BUSINESS_OPEN_HOUR = 9
BUSINESS_CLOSE_HOUR = 18

# Confidence scoring thresholds
CONFIDENCE_HIGH = 0.6
CONFIDENCE_LOW = 0.3

# Maximum allowed input length to prevent overly long inputs
MAX_INPUT_LENGTH = 500

# Exit keywords
EXIT_WORDS = {"bye", "exit", "quit", "goodbye"}

# Synonyms dictionary mapping variations and keywords to canonical forms
SYNONYMS: Dict[str, str] = {
    # Business hours synonyms
    "open": "hours",
    "opening": "hours",
    "timing": "hours",
    "timings": "hours",
    "schedule": "hours",
    "close": "hours",
    "closing": "hours",
    # Project submission synonyms
    "upload": "submit",
    "send": "submit",
    "hand in": "submit",
    "submitting": "submit",
    "submission": "submit",
    "github": "project",
    "repo": "project",
    "repository": "project",
    "link": "project",
    # Certificate synonyms
    "cert": "certificate",
    "certification": "certificate",
    "certificates": "certificate",
}

# Common English stop words that carry little semantic distinction
STOP_WORDS: Set[str] = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "to", "at", "in", "on", "for", "of", "with",
    "my", "your", "our", "i", "you", "we", "they", "it", "me", "what",
    "when", "where", "how", "can", "will", "would", "should", "could",
    "get", "from", "or", "and", "so", "as"
}


# ---------------------------------------------------------------------------
# State Machine & Data Models
# ---------------------------------------------------------------------------

class BotState(enum.Enum):
    """Enumeration of possible conversation states."""
    GREETING = "GREETING"      # Waiting for the first message
    LISTENING = "LISTENING"    # Normal state, ready for questions
    CLARIFYING = "CLARIFYING"  # Waiting for yes/no to a clarification question
    ENDED = "ENDED"            # Session has finished


@dataclasses.dataclass
class BotSession:
    """Holds conversation state and pending questions without global variables."""
    state: BotState = BotState.GREETING
    pending_faq: Optional[Dict[str, str]] = None


# ---------------------------------------------------------------------------
# Dataset Loading & Validation
# ---------------------------------------------------------------------------

def load_dataset(filepath: pathlib.Path | str) -> Dict[str, Any]:
    """
    Load and parse the JSON dataset from the given path.
    Exits cleanly without a traceback if the file is missing or invalid.
    """
    path = pathlib.Path(filepath)
    if not path.exists():
        print(f"Error: Dataset file not found at '{path}'.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"Error: Invalid JSON format in '{path}': {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Error: Failed to read dataset file '{path}': {exc}", file=sys.stderr)
        sys.exit(1)

    validate_dataset(data)
    return data


def validate_dataset(data: Any) -> None:
    """
    Validate that the loaded dataset matches the expected schema.
    Exits cleanly without a traceback on validation failure.
    """
    if not isinstance(data, dict):
        print("Error: Dataset root must be a JSON object (dictionary).", file=sys.stderr)
        sys.exit(1)

    # Validate greetings list
    greetings = data.get("greetings")
    if not isinstance(greetings, list) or not all(isinstance(g, str) for g in greetings):
        print("Error: Dataset 'greetings' field must be a list of strings.", file=sys.stderr)
        sys.exit(1)

    # Validate faqs list
    faqs = data.get("faqs")
    if not isinstance(faqs, list):
        print("Error: Dataset 'faqs' field must be a list of FAQ objects.", file=sys.stderr)
        sys.exit(1)

    for index, item in enumerate(faqs):
        if not isinstance(item, dict):
            print(f"Error: FAQ item at index {index} must be an object.", file=sys.stderr)
            sys.exit(1)
        if "question" not in item or not isinstance(item["question"], str):
            print(f"Error: FAQ item at index {index} is missing a string 'question'.", file=sys.stderr)
            sys.exit(1)
        if "answer" not in item or not isinstance(item["answer"], str):
            print(f"Error: FAQ item at index {index} is missing a string 'answer'.", file=sys.stderr)
            sys.exit(1)


# ---------------------------------------------------------------------------
# Text Processing & Normalization
# ---------------------------------------------------------------------------

def stem_word(word: str) -> str:
    """
    Apply beginner-friendly regex-based stemming for common plurals and verb endings.
    """
    # Handle -ing endings (e.g. submitting -> submit, opening -> open)
    if word.endswith("ing") and len(word) > 5:
        # Double consonant reduction before ing (e.g., submitting -> submit)
        word = re.sub(r"([a-z])\1ing$", r"\1", word)
        word = re.sub(r"ing$", "", word)
    # Handle -es endings (e.g. watches -> watch)
    elif word.endswith("es") and len(word) > 4:
        word = re.sub(r"es$", "", word)
    # Handle plural -s endings (e.g. certificates -> certificate, hours -> hour)
    elif word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        word = re.sub(r"s$", "", word)

    return word


def normalize(text: str) -> str:
    """
    Normalize text:
    1. Lowercase and strip whitespace.
    2. Replace punctuation and curly quotes with spaces.
    3. Replace synonyms (multi-word first, then single words).
    4. Collapse repeated whitespace.
    """
    # 1. Lowercase and trim
    text = text.lower().strip()

    # 2. Replace typographic/curly apostrophes and quotes with spaces
    text = re.sub(r"[’'“”\"`´]", " ", text)

    # Replace standard punctuation with spaces
    text = re.sub(r"[^\w\s]", " ", text)

    # 3. Apply multi-word synonyms first (e.g., "hand in" -> "submit")
    for phrase, replacement in SYNONYMS.items():
        if " " in phrase:
            pattern = r"\b" + re.escape(phrase) + r"\b"
            text = re.sub(pattern, replacement, text)

    # 4. Collapse repeated whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> List[str]:
    """
    Extract normalized, stopword-filtered, and stemmed tokens from text.
    """
    normalized_text = normalize(text)
    raw_words = re.findall(r"\b[a-z0-9]+\b", normalized_text)

    tokens: List[str] = []
    for word in raw_words:
        # Apply single-word synonyms
        word = SYNONYMS.get(word, word)
        if word not in STOP_WORDS:
            stemmed = stem_word(word)
            # Re-check synonym after stemming
            stemmed = SYNONYMS.get(stemmed, stemmed)
            tokens.append(stemmed)

    return tokens


# ---------------------------------------------------------------------------
# Intent Knowledge Base & Scoring
# ---------------------------------------------------------------------------

def build_intents(faqs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Automatically derive keyword tokens and Inverse Document Frequency (IDF)
    rarity weights for all FAQs. No hardcoded FAQ keywords are required.
    """
    intents: List[Dict[str, Any]] = []
    n_faqs = len(faqs)

    # Count document frequency for each word across all FAQ questions
    doc_freq: Dict[str, int] = {}
    faq_tokens_list: List[List[str]] = []

    for faq in faqs:
        tokens = tokenize(faq["question"])
        faq_tokens_list.append(tokens)
        for token in set(tokens):
            doc_freq[token] = doc_freq.get(token, 0) + 1

    # Compute IDF weight for each token: rarer tokens receive higher weight
    for faq, tokens in zip(faqs, faq_tokens_list):
        weights: Dict[str, float] = {}
        for token in set(tokens):
            # Smooth IDF formula: ln(1 + N / df) + 1.0
            df = doc_freq.get(token, 1)
            weights[token] = 1.0 + math.log(1.0 + (n_faqs / df))

        intents.append({
            "faq": faq,
            "tokens": set(tokens),
            "weights": weights,
        })

    return intents


def score_clause(clause_tokens: List[str], intent: Dict[str, Any]) -> float:
    """
    Score how well a single user clause matches an FAQ intent.
    Calculates weighted overlap relative to both the user query and the FAQ.
    Returns a float between 0.0 and 1.0.
    """
    if not clause_tokens or not intent["tokens"]:
        return 0.0

    clause_set = set(clause_tokens)
    intent_tokens = intent["tokens"]
    weights = intent["weights"]

    # Matched tokens between query clause and FAQ
    overlap = clause_set.intersection(intent_tokens)
    if not overlap:
        return 0.0

    # Weight of matched tokens (fallback to 1.0 for words not in FAQ weights)
    matched_weight = sum(weights.get(w, 1.0) for w in overlap)

    # Total weight of query tokens
    query_total_weight = sum(weights.get(w, 1.0) for w in clause_set)

    # Total weight of FAQ tokens
    faq_total_weight = sum(weights.get(w, 1.0) for w in intent_tokens)

    # Coverage ratios
    query_coverage = matched_weight / query_total_weight if query_total_weight > 0 else 0.0
    faq_coverage = matched_weight / faq_total_weight if faq_total_weight > 0 else 0.0

    # Balanced score: 50% query coverage + 50% FAQ coverage
    final_score = (0.5 * query_coverage) + (0.5 * faq_coverage)
    return round(final_score, 4)


def split_clauses(text: str) -> List[str]:
    """
    Split a message into distinct clauses on ?, ;, commas, and coordinating conjunctions.
    """
    # Replace conjunction separators with a delimiter pipe
    text_with_delims = re.sub(
        r"(\?+|;+|,|\band\b|\balso\b|\bplus\b)",
        "|",
        text,
        flags=re.IGNORECASE
    )

    clauses = [c.strip() for c in text_with_delims.split("|") if c.strip()]
    return clauses if clauses else [text.strip()]


def find_intents(clauses: List[str], intents: List[Dict[str, Any]]) -> List[Tuple[Dict[str, str], float]]:
    """
    Score each clause against every FAQ intent and return unique matched FAQs
    with their highest score, ordered by appearance.
    """
    matched_faqs: List[Tuple[Dict[str, str], float]] = []
    seen_questions: Set[str] = set()

    for clause in clauses:
        clause_tokens = tokenize(clause)
        if not clause_tokens:
            continue

        best_faq: Optional[Dict[str, str]] = None
        best_score = 0.0

        for intent in intents:
            score = score_clause(clause_tokens, intent)
            if score > best_score:
                best_score = score
                best_faq = intent["faq"]

        if best_faq is not None and best_faq["question"] not in seen_questions:
            seen_questions.add(best_faq["question"])
            matched_faqs.append((best_faq, best_score))

    return matched_faqs


# ---------------------------------------------------------------------------
# Greetings & Exit Detection
# ---------------------------------------------------------------------------

def is_greeting(text: str, greetings: List[str]) -> bool:
    """
    Determine if text contains a greeting word or phrase using word boundaries (\b).
    Ensures substrings in words like 'this' or 'they' are never misidentified.
    """
    # Always include 'good evening' alongside dataset greetings
    all_greetings = set(greetings) | {"good evening"}

    for greeting in all_greetings:
        pattern = r"\b" + re.escape(greeting.strip().lower()) + r"\b"
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def is_exit(text: str) -> bool:
    """
    Check if the user message is an exit command.
    Must contain an exit word AND contain at most 3 words.
    """
    words = re.findall(r"\b\w+\b", text.lower())
    if len(words) <= 3 and any(w in EXIT_WORDS for w in words):
        return True
    return False


# ---------------------------------------------------------------------------
# Business Hours Logic
# ---------------------------------------------------------------------------

def build_hours_status(current_time: Optional[datetime.datetime] = None) -> str:
    """
    Generate the current operational status for Datheon Support in IST.
    Injectable current_time parameter allows tests to verify different times.
    """
    if current_time is None:
        current_time = datetime.datetime.now(IST)
    elif current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=IST)
    else:
        current_time = current_time.astimezone(IST)

    # Monday = 0, Friday = 4, Saturday = 5, Sunday = 6
    weekday = current_time.weekday()
    hour = current_time.hour
    minute = current_time.minute
    time_float = hour + (minute / 60.0)

    # Check if currently open: Mon-Fri between 09:00 and 18:00
    is_open = (weekday < 5) and (BUSINESS_OPEN_HOUR <= time_float < BUSINESS_CLOSE_HOUR)

    if is_open:
        return "Right now (IST) we are OPEN."

    # Determine reopening day
    if weekday < 5 and time_float < BUSINESS_OPEN_HOUR:
        # Before 9:00 AM on a weekday
        reopen_day = current_time.strftime("%A")
    elif weekday < 4 and time_float >= BUSINESS_CLOSE_HOUR:
        # After 18:00 PM on Mon-Thu -> opens next morning
        next_day = current_time + datetime.timedelta(days=1)
        reopen_day = next_day.strftime("%A")
    else:
        # After 18:00 on Friday, or anytime Saturday/Sunday -> opens Monday
        reopen_day = "Monday"

    return f"Right now (IST) we are CLOSED, we reopen {reopen_day} at 9:00 AM."


def get_faq_heading(faq: Dict[str, str]) -> str:
    """
    Derive a concise, beginner-friendly heading for an FAQ item.
    """
    q_lower = faq["question"].lower()
    if any(k in q_lower for k in ("hour", "timing", "open", "close")):
        return "Hours"
    if any(k in q_lower for k in ("submit", "submission", "upload", "project")):
        return "Submission"
    if "cert" in q_lower:
        return "Certificate"

    # Fallback: extract the first two informative words from the question
    tokens = [w for w in re.findall(r"\b[A-Za-z]+\b", faq["question"]) if w.lower() not in STOP_WORDS]
    if tokens:
        return " ".join(tokens[:2]).title()
    return "Topic"


# ---------------------------------------------------------------------------
# Core Response Engine (Pure Function)
# ---------------------------------------------------------------------------

def respond(
    user_input: str,
    session: BotSession,
    dataset: Dict[str, Any],
    current_time: Optional[datetime.datetime] = None,
) -> str:
    """
    Pure response generation function: maps input and state to a response string.
    Contains no print() or input() calls so it can be easily and thoroughly tested.
    """
    # Cap input length at 500 characters
    clean_input = user_input[:MAX_INPUT_LENGTH].strip()

    # 1. Handle empty input
    if not clean_input:
        return "Please enter a question or message, or type 'help' for topics."

    # 2. Check for exit commands
    if is_exit(clean_input):
        session.state = BotState.ENDED
        return "Goodbye! Feel free to reach out if you have any more questions."

    # 3. Handle CLARIFYING state
    if session.state == BotState.CLARIFYING:
        norm_input = normalize(clean_input)
        if norm_input in {"yes", "y", "yeah", "yep", "sure"}:
            confirmed_faq = session.pending_faq
            session.pending_faq = None
            session.state = BotState.LISTENING

            if confirmed_faq is not None:
                answer = confirmed_faq["answer"]
                if "hour" in confirmed_faq["question"].lower():
                    answer = f"{answer} {build_hours_status(current_time)}"
                return answer
            return "How can I help you today?"

        if norm_input in {"no", "n", "nope"}:
            session.pending_faq = None
            session.state = BotState.LISTENING
            return "No problem! Feel free to ask another question, or type 'help' for topics."

        # Any other response keeps clarifying
        pending_q = session.pending_faq["question"] if session.pending_faq else ""
        return f"Please reply with 'yes' or 'no'. Did you mean: \"{pending_q}\"?"

    # 4. Check for 'help' or 'topics'
    norm_full = normalize(clean_input)
    if norm_full in {"help", "topics", "menu"}:
        session.state = BotState.LISTENING
        topics_list = [f"{i + 1}. {f['question']}" for i, f in enumerate(dataset.get("faqs", []))]
        menu_text = "\n".join(topics_list)
        return (
            "Here are the topics I can help you with:\n"
            f"{menu_text}\n"
            "Ask me about any of these, or type 'bye' to exit."
        )

    # 5. Check for greeting in the input
    greetings = dataset.get("greetings", [])
    has_greeting = is_greeting(clean_input, greetings)

    # Transition from GREETING to LISTENING
    if session.state == BotState.GREETING:
        session.state = BotState.LISTENING

    # 6. Parse and score clauses against FAQs
    faqs = dataset.get("faqs", [])
    intents = build_intents(faqs)
    clauses = split_clauses(clean_input)

    # Filter out clauses that are purely greetings
    content_clauses = [c for c in clauses if not (is_greeting(c, greetings) and len(re.findall(r"\b\w+\b", c)) <= 2)]
    if not content_clauses:
        content_clauses = clauses

    matched = find_intents(content_clauses, intents)

    # Separate into high-confidence and clarification matches
    high_matches = [faq for faq, score in matched if score >= CONFIDENCE_HIGH]
    clarify_matches = [(faq, score) for faq, score in matched if CONFIDENCE_LOW <= score < CONFIDENCE_HIGH]

    # Greeting prefix when user included a greeting
    greeting_prefix = "Hello! " if has_greeting else ""

    # Case A: One or more high-confidence FAQ matches
    if high_matches:
        if len(high_matches) == 1:
            faq = high_matches[0]
            answer = faq["answer"]
            if "hour" in faq["question"].lower():
                answer = f"{answer} {build_hours_status(current_time)}"
            return f"{greeting_prefix}{answer}".strip()

        # Multi-intent matches: format each under its own heading
        output_parts: List[str] = []
        if greeting_prefix:
            output_parts.append(f"{greeting_prefix}Here is what I found:")
        else:
            output_parts.append("Here is what I found:")

        for faq in high_matches:
            heading = get_faq_heading(faq)
            ans = faq["answer"]
            if "hour" in faq["question"].lower():
                ans = f"{ans} {build_hours_status(current_time)}"
            output_parts.append(f"[{heading}] {ans}")

        return "\n".join(output_parts)

    # Case B: Ambiguous query needing clarification (LOW <= score < HIGH)
    if clarify_matches:
        best_faq, _ = max(clarify_matches, key=lambda x: x[1])
        session.state = BotState.CLARIFYING
        session.pending_faq = best_faq
        prefix = f"{greeting_prefix}" if greeting_prefix else ""
        return f"{prefix}Did you mean: \"{best_faq['question']}\"? (yes/no)".strip()

    # Case C: Only greeting was provided without questions
    if has_greeting:
        return "Hello! How can I help you today? Ask me anything, or type 'help' for topics."

    # Case D: Low confidence fallback
    topics_list = [f"• {f['question']}" for f in faqs]
    topics_str = "\n".join(topics_list)
    return (
        "I'm sorry, I didn't quite understand that.\n"
        "Here are some topics you can ask me about:\n"
        f"{topics_str}\n"
        "You can also type 'help' to see available questions or 'bye' to exit."
    )


# ---------------------------------------------------------------------------
# Terminal Interactive CLI Loop
# ---------------------------------------------------------------------------

def run_chat(dataset_path: Optional[pathlib.Path | str] = None) -> None:
    """
    Run the interactive terminal chat session.
    """
    path = pathlib.Path(dataset_path) if dataset_path else DEFAULT_DATA_PATH
    dataset = load_dataset(path)
    session = BotSession()

    print("=" * 65)
    print("Welcome to Datheon Support Bot!")
    print(f"Dataset: {path}")
    print("Ask me anything, or type 'help' for topics and 'bye' to exit.")
    print("=" * 65)

    while session.state != BotState.ENDED:
        try:
            user_input = input("\nYou: ")
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! Have a great day!")
            break

        reply = respond(user_input, session, dataset)
        print(f"Bot: {reply}")


def main() -> None:
    """Main entry point of the script."""
    run_chat()


if __name__ == "__main__":
    main()
