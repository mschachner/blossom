from pathlib import Path
import string

file_path = Path("wordlist.txt")
words = file_path.read_text(encoding="utf-8").splitlines()

def keep(word: str, *, uniq_limit: int = 7, min_len: int = 4) -> bool:
    letters = {ch.lower() for ch in word if ch in string.ascii_letters}
    return len(letters) <= uniq_limit and len(word) >= min_len

out, seen = [], set()

# Filter and deduplicate
for w in words:
    if keep(w) and w not in seen:
        out.append(w)
        seen.add(w)

# Ensure “…nesses” partner exists
for w in out[:]:
    if w.lower().endswith("ness"):
        plural = f"{w}es"
        if keep(plural) and plural not in seen:
            out.append(plural)
            seen.add(plural)

# Write back: each word followed by a single period, then newline
file_path.write_text("\n".join(f"{w}." for w in out) + "\n", encoding="utf-8")