Blossom AI
==========

This program plays [Blossom](https://www.merriam-webster.com/games/blossom-word-game), a word game similar to
*Spelling Bee*. Feed this program a seven-letter bank, and it picks high-scoring
words from a dictionary in `wordlist.txt`, which approximates the Merriam-Webster wordlist. It displays each move in bright
colors and tallies the score along the way.

Running the game
----------------

    python blossom.py           # prompt for a bank
    python blossom.py resanto   # provide the bank directly (center letter first)

Since Blossom's wordlist is proprietary, the user is asked to validate words. Once a
round is over, it optionally commits any approved validations or removals to
`wordlist.txt` via Git.

Files
-----

- `blossom.py` – the main program.
- `wordlist.txt` – candidate words with a final “.” (unverified) or “!”
  (validated).
- `wordlist_unedited.txt` – the original dictionary.
- `wordlist_edit.py` – currently empty, intended for future wordlist tooling.

