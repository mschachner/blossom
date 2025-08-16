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
python blossom.py play                  # prompt for a bank
python blossom.py play resanto          # play using a provided bank (center letter first)
python blossom.py play -f resanto       # play fast
python blossom.py search                # interactive dictionary lookup/add
python blossom.py search foo bar        # search specific words
python blossom.py stats                 # show stats
python blossom.py --help                # show all options
```

Wordlists and tools
-------------------

- `wordlist.txt` – candidate words. Lines end with `.` when unverified and `!`
  once validated.
- `wordlist_unedited.txt` – the original dictionary source.
- `wordlist_edit.py` – lowercases words and strips ANSI color codes from
  `wordlist.txt`.

The code is organized as a package in the `blossom/` directory with modules for
the command-line interface, game logic, and wordlist management.
`blossom.py` is a small entry point that delegates to `blossom/cli.py`.

