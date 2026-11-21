"""
Hangman - a console word-guessing game.

Task 01 | Python Programming Internship
Concepts practised: string manipulation, sets, control flow, functions,
file handling, input validation.

How to run:
    python hangman.py
(keep 'google-10000-english-no-swears.txt' in the same folder)
"""

import os
import random
from pathlib import Path

# --------------------------------------------------------------------------
# Settings (constants are written in CAPITALS so they are easy to spot)
# --------------------------------------------------------------------------
MAX_MISTAKES = 6          # wrong guesses allowed before the game is lost
MIN_WORD_LENGTH = 4       # skip tiny words like "a", "to", "of" (too easy)
WORD_FILE = Path(__file__).with_name("google-10000-english-no-swears.txt")

# Used only if the word-list file cannot be found.
FALLBACK_WORDS = [
    "python", "programming", "internship", "keyboard", "variable",
    "function", "algorithm", "database", "developer", "terminal",
]

# One picture for every number of mistakes: index 0 = none ... index 6 = dead.
STAGES = [
    """
      +---+
      |   |
          |
          |
          |
          |
    =========""",
    """
      +---+
      |   |
      O   |
          |
          |
          |
    =========""",
    """
      +---+
      |   |
      O   |
      |   |
          |
          |
    =========""",
    """
      +---+
      |   |
      O   |
     /|   |
          |
          |
    =========""",
    """
      +---+
      |   |
      O   |
     /|\\  |
          |
          |
    =========""",
    """
      +---+
      |   |
      O   |
     /|\\  |
     /    |
          |
    =========""",
    """
      +---+
      |   |
      O   |
     /|\\  |
     / \\  |
          |
    =========""",
]

VICTORY_BANNER = r"""
  __   _____  _   _  __        _____  _   _ _
  \ \ / / _ \| | | | \ \      / / _ \| \ | | |
   \ V / | | | | | |  \ \ /\ / / | | |  \| | |
    | || |_| | |_| |   \ V  V /| |_| | |\  |_|
    |_| \___/ \___/     \_/\_/  \___/|_| \_(_)
"""

DEFEAT_BANNER = r"""
   ____    _    __  __ _____    _____     _______ ____
  / ___|  / \  |  \/  | ____|  / _ \ \   / / ____|  _ \
 | |  _  / _ \ | |\/| |  _|   | | | \ \ / /|  _| | |_) |
 | |_| |/ ___ \| |  | | |___  | |_| |\ V / | |___|  _ <
  \____/_/   \_\_|  |_|_____|  \___/  \_/  |_____|_| \_\
"""


# --------------------------------------------------------------------------
# Word handling
# --------------------------------------------------------------------------
def load_words(path=WORD_FILE):
    """Read the word list and return only clean, usable words."""
    try:
        with open(path, encoding="utf-8") as file:
            words = [line.strip().lower() for line in file]
    except FileNotFoundError:
        print(f"(Word list not found at {path}. Using the built-in words.)")
        return FALLBACK_WORDS

    usable = [w for w in words if w.isalpha() and len(w) >= MIN_WORD_LENGTH]
    return usable or FALLBACK_WORDS


def choose_word(words):
    """Pick one secret word at random."""
    return random.choice(words)


def mask_word(word, correct_letters):
    """Return the word with unguessed letters hidden, e.g. 'P _ T H _ N'."""
    return " ".join(ch.upper() if ch in correct_letters else "_" for ch in word)


def is_word_guessed(word, correct_letters):
    """True when every letter of the word has been found."""
    return set(word) <= correct_letters  # 'is the word's letter-set inside my guesses?'


# --------------------------------------------------------------------------
# Screen output
# --------------------------------------------------------------------------
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def show_game_state(word, correct_letters, wrong_letters):
    """Draw the gallows, the masked word and the guessed letters."""
    mistakes = len(wrong_letters)
    print(STAGES[mistakes])
    print(f"\n  Word:   {mask_word(word, correct_letters)}\n")
    print(f"  Wrong letters: {' '.join(sorted(l.upper() for l in wrong_letters)) or '-'}")
    print(f"  Lives left:    {MAX_MISTAKES - mistakes} / {MAX_MISTAKES}\n")


def show_victory(word, mistakes):
    print(VICTORY_BANNER)
    print(f"  You guessed the word: {word.upper()}")
    print(f"  Mistakes made: {mistakes} / {MAX_MISTAKES}\n")


def show_defeat(word):
    print(DEFEAT_BANNER)
    print(f"  The word was: {word.upper()}")
    print("  Better luck next time!\n")


# --------------------------------------------------------------------------
# Player input
# --------------------------------------------------------------------------
def ask_for_guess(already_guessed):
    """Keep asking until the player types one NEW letter. Returns it in lowercase."""
    while True:
        guess = input("  Guess a letter: ").strip().lower()

        if len(guess) != 1 or not guess.isalpha():
            print("  Please type exactly ONE letter (A-Z).")
        elif guess in already_guessed:
            print(f"  You already tried '{guess.upper()}'. No penalty - try another!")
        else:
            return guess


def ask_play_again():
    while True:
        answer = input("  Play again? (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please type 'y' or 'n'.")


# --------------------------------------------------------------------------
# Game logic
# --------------------------------------------------------------------------
def play_round(word):
    """Play one full game. Returns True if the player won."""
    correct_letters = set()   # right guesses
    wrong_letters = set()     # wrong guesses

    while len(wrong_letters) < MAX_MISTAKES:
        clear_screen()
        print("\n  === H A N G M A N ===")
        show_game_state(word, correct_letters, wrong_letters)

        guess = ask_for_guess(correct_letters | wrong_letters)

        if guess in word:
            correct_letters.add(guess)
            if is_word_guessed(word, correct_letters):
                clear_screen()
                show_game_state(word, correct_letters, wrong_letters)
                show_victory(word, len(wrong_letters))
                return True
        else:
            wrong_letters.add(guess)

    # The loop ended because the player ran out of lives.
    clear_screen()
    show_game_state(word, correct_letters, wrong_letters)
    show_defeat(word)
    return False


def main():
    words = load_words()
    wins = losses = 0

    try:
        while True:
            if play_round(choose_word(words)):
                wins += 1
            else:
                losses += 1

            print(f"  Score  ->  Wins: {wins}   Losses: {losses}\n")
            if not ask_play_again():
                break
    except (KeyboardInterrupt, EOFError):
        print()  # player pressed Ctrl+C - leave quietly

    print("\n  Thanks for playing Hangman. Goodbye!\n")


if __name__ == "__main__":
    main()
