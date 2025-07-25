from pathlib import Path
import string

# Path to your word-list file
file_path = Path("wordlist.txt")

# Read all words (one per line)
words = file_path.read_text(encoding="utf-8").splitlines()

def too_many_unique_letters(word: str, limit: int = 7) -> bool:
    """Return True if *word* contains more than *limit* distinct letters."""
    # Keep only ASCII letters so “O’Neil” → “ONeil”; remove punctuation/digits.
    letters = {ch.lower() for ch in word if ch in string.ascii_letters}
    return len(letters) > limit

# Filter the list
filtered = [w for w in words if not too_many_unique_letters(w)]

# Overwrite the original file
file_path.write_text("\n".join(filtered) + "\n", encoding="utf-8")