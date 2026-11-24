# Datheon Support Bot

A rule-based, interactive customer-support terminal chatbot developed in pure Python. The bot is fully data-driven, answering customer questions based on a JSON knowledge base without any external machine learning models or internet access.

---

## 🌟 Key Features

1. **Pure Python Standard Library**: Built strictly with Python 3 built-ins (`json`, `re`, `pathlib`, `datetime`, `enum`, `dataclasses`, `sys`).
2. **Data-Driven Architecture**: All FAQs and greetings are loaded dynamically from `data/sample_faq.json`. If you add a new FAQ to the JSON file, the bot matches it automatically without modifying any Python code.
3. **Text Normalization & Stemming**:
   - Lowercases and strips whitespace.
   - Cleans standard punctuation and typographic/curly quotes (`’`, `“`, `”`).
   - Replaces synonyms (e.g., `open`/`timing` $\rightarrow$ `hours`, `upload`/`hand in` $\rightarrow$ `submit`, `cert` $\rightarrow$ `certificate`).
   - Filters out non-informative English stop words.
   - Applies regex-based stemming for `-ing`, `-es`, and plural `-s` suffixes.
4. **Smart Greeting Detection**: Uses regex word boundaries (`\b`) so words like `"this"` or `"they"` are never misclassified as `"hi"` or `"hey"`. If a greeting comes with a question (e.g., `"Hi, what are your hours?"`), the bot greets and answers the question together.
5. **Multi-Intent Handling**: Splits multi-part questions on `?`, `;`, commas, and conjunctions (`and`, `also`, `plus`), scores each clause, and answers all matched intents under clear headings without duplicates.
6. **Confidence Scoring & Clarification**:
   - Scores clauses using keyword overlap weighted by Inverse Document Frequency (IDF) rarity.
   - **Score $\ge 0.6$ (High)**: Directly answers the question.
   - **$0.3 \le \text{Score} < 0.6$ (Low to High)**: Enters `CLARIFYING` state and asks: `Did you mean: "<FAQ Question>"? (yes/no)`.
   - **Score $< 0.3$ (Low)**: Displays a friendly fallback listing available topics and suggests typing `"help"`.
7. **Business Hours Context**:
   - Evaluates operating hours (Mon–Fri, 09:00 to 18:00 IST, UTC+05:30) whenever hours are queried.
   - Appends a real-time status: `"Right now (IST) we are OPEN."` or `"Right now (IST) we are CLOSED, we reopen <day> at 9:00 AM."`.
   - Clock is fully injectable for testing.
8. **State Machine**: Powered by a clean `enum` (`GREETING`, `LISTENING`, `CLARIFYING`, `ENDED`) and a dataclass `BotSession`.
9. **Graceful Error Handling**: Validates JSON dataset integrity, caps input length at 500 characters, handles empty inputs, and exits cleanly on `Ctrl+C` or `Ctrl+Z` without stack traces.

---

## 📁 Project Structure

```text
Task 04/
├── .gitignore               # Ignores __pycache__/, .venv/, etc.
├── README.md                # Project documentation
├── chatbot.py               # Main pure-Python support bot implementation
├── data/
│   └── sample_faq.json      # Knowledge base (greetings + FAQs)
└── tests/
    ├── __init__.py
    └── test_chatbot.py      # Comprehensive pytest test suite (32 tests)
```

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.10+
- `pytest` (only required for running tests)

### 2. Run the Interactive Chatbot
Execute the script from the project root:
```bash
python chatbot.py
```

### 3. Run the Pytest Test Suite
To run all 32 parametrized unit tests:
```bash
pytest -v
```

---

## 💬 Sample Conversation

```text
=================================================================
Welcome to Datheon Support Bot!
Dataset: C:\...\Task 04\data\sample_faq.json
Ask me anything, or type 'help' for topics and 'bye' to exit.
=================================================================

You: hi
Bot: Hello! How can I help you today? Ask me anything, or type 'help' for topics.

You: when are you open and when do I get my certificate?
Bot: Here is what I found:
[Hours] We operate Monday through Friday from 9:00 AM to 6:00 PM IST. Right now (IST) we are OPEN.
[Certificate] Certificates are reviewed and issued within 3-5 business days after your project is verified.

You: where do I upload my github link
Bot: You can submit your internship project by uploading your GitHub repository link through the student submission portal.

You: how do I exit the internship
Bot: Did you mean: "How can I submit my internship project?"? (yes/no)

You: yes
Bot: You can submit your internship project by uploading your GitHub repository link through the student submission portal.

You: tell me a joke
Bot: I'm sorry, I didn't quite understand that.
Here are some topics you can ask me about:
• What are your business hours?
• How can I submit my internship project?
• When do I get my certificate?
You can also type 'help' to see available questions or 'bye' to exit.

You: bye
Bot: Goodbye! Feel free to reach out if you have any more questions.
```
