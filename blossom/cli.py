import argparse

from .game import playBlossom, showStats
from .wordlist import searchWords
from .utils import sevenUniques


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)

    playParser = subparsers.add_parser(
        "play", help="Play Blossom with optionally specified bank"
    )
    playParser.add_argument("bank", nargs="?", default=None, help="Bank of letters (optional)")
    playParser.add_argument("-f", "--fast", action="store_true", help="Play fast")

    subparsers.add_parser("stats", help="Show stats")
    searchParser = subparsers.add_parser("search", help="Search for words")
    searchParser.add_argument("queries", nargs="*", help="Words to be searched")

    args = parser.parse_args()
    match args.mode:
        case "play":
            if not args.bank or sevenUniques(args.bank):
                playBlossom(fast=args.fast, bank=args.bank)
            else:
                print("Invalid bank. Please provide seven unique letters.")
                return
        case "stats":
            showStats()
        case "search":
            searchWords(args.queries)
