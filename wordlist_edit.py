from pathlib import Path
import string

FILE = Path("wordlist.txt")

def keep(word: str, *, uniq_limit: int = 7, min_len: int = 4) -> bool:
    letters = {c.lower() for c in word if c in string.ascii_letters}
    return len(letters) <= uniq_limit and len(word) >= min_len

# Read, strip trailing newlines, discard empty lines
raw_words = [w.strip() for w in FILE.read_text(encoding="utf-8").splitlines() if w.strip()]

kept = []
seen = set()          # for fast “no duplicates” checks

for w in raw_words:
    if not keep(w):
        continue
    if w not in seen:
        kept.append(w)
        seen.add(w)

    # Ensure the “-ness” → “-nesses” variant is present (subject to same filters)
    if w.endswith("ness"):
        plural = w + "es"          # kindness → kindnesses
        if plural not in seen and keep(plural):
            kept.append(plural)
            seen.add(plural)

# Overwrite the file
FILE.write_text("\n".join(kept) + "\n", encoding="utf-8")