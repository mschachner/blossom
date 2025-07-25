from pathlib import Path
import string

file_path = Path("wordlist.txt")
words = file_path.read_text(encoding="utf-8").splitlines()

def keep(word: str, *, uniq_limit: int = 7, min_len: int = 4) -> bool:
    letters = {ch.lower() for ch in word if ch in string.ascii_letters}
    return len(letters) <= uniq_limit and len(word) >= min_len

filtered = [w for w in words if keep(w)]

file_path.write_text("\n".join(filtered) + "\n", encoding="utf-8")