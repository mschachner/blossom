Blossom AI
==========

Blossom AI is a command-line assistant for Merriam-Webster's [Blossom word game](https://www.merriam-webster.com/games/blossom-word-game).
Given a seven-letter bank (with the center letter first), it chooses high-scoring
plays from `wordlist.txt`, prints them with colorful typewriter-style output, and
keeps score.

Features
--------

- Plays a full Blossom round using a look-ahead strategy.
- Rotates the special letter each round and scores words using the Blossom rules
  (length bonuses, +5 for each special letter, +7 for pangrams).
- Prompts to validate or remove unknown words and commits changes to
  `wordlist.txt` via Git.
- **Fast mode** to skip the typewriter effect.
- **Dictionary search** to check or add words.

Usage
-----

```
python blossom.py                  # prompt for a bank
python blossom.py resanto          # play using a provided bank (center letter first)
python blossom.py fast resanto     # play fast
python blossom.py search           # interactive dictionary lookup/add
python blossom.py search foo bar   # search specific words
python blossom.py --help           # show all options
```

Wordlists and tools
-------------------

- `wordlist.txt` – candidate words. Lines end with `.` when unverified and `!`
  once validated.
- `wordlist_unedited.txt` – the original dictionary source.
- `wordlist_edit.py` – lowercases words and strips ANSI color codes from
  `wordlist.txt`.

`blossom.py` is the main program that orchestrates the game, handles dictionary
search, and updates the wordlist.

