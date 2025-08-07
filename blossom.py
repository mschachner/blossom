import os
import subprocess
import sys,time
from datetime import datetime
import argparse
# import questionary

# Aesthetics: color text, typewriter-style print.

def dispWord(word,dict):
  styles = {
      "reset": "\033[0m",
      "boldred": "\033[1;31m",
      "boldgreen": "\033[1;32m",
      "boldyellow": "\033[1;33m",
  }
  color = "red" if word not in dict else "green" if dict[word] else "yellow"
  icon = "❌ " if word not in dict else "🌸 " if len(set(word)) == 7 else "🟡 "
  return icon + f"{styles['bold' + color]}{word.upper()}{styles['reset']}"

def _tprint(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    """Typewriter-style print. Same signature as print()."""
    text = sep.join(map(str, objects)) + end

    # If not an interactive terminal, print fast.
    if not getattr(file, "isatty", lambda: False)():
        file.write(text)
        if flush:
            file.flush()
        return

    # Tuned speeds
    cps = 150                    # characters per second
    punct_pause = 0.10           # pause after . ! ?
    mid_pause = 0.10             # pause after , ; : – —
    base = 1.0 / cps

    for ch in text:
        file.write(ch)
        file.flush()             # ensure immediate display
        if ch in ".!?":
            time.sleep(punct_pause)
        elif ch in ",;:–—":
            time.sleep(mid_pause)
        else:
            time.sleep(base)

def loadDict(bank=None):
  dict = {}
  with open("wordlist.txt") as infile:
    for line in infile:
      word = line[0:-2]
      if not bank or (any(c == bank[0] for c in word) and all(c in bank for c in word)): # word is legal
        dict[word] = line.endswith('!\n')
  return dict

def scoreWord(bank, specialLetter, word):
  baseScore = 2*len(word)-6 if len(word) < 7 else 3*len(word)-9
  specialLetterScore = 5 * word.count(specialLetter)
  pangramScore = 7 if all(c in word for c in bank) else 0
  return baseScore + specialLetterScore + pangramScore

# The blossomBetter agent plans ahead. I don't think it's optimal though.
def allPlays(legalWords, bank, prevPlayed):
  plays = []
  for word in (w for w in legalWords if w not in prevPlayed):
    for i in range(6):
      plays.append((i,word,scoreWord(bank,bank[i+1],word)))
  # Sort by score descending.
  plays.sort(key=lambda x: x[2], reverse=True)
  return plays

def blossomBetter(bank, dict, prevPlayed, round, score):
  chosenPlays = {i:[] for i in range(6)}
  # Determine how many words are still needed for each letter.
  stillNeeded = [int(round <= i) + int(round <= i+6) for i in range(6)]
  placedWords = []
  expectedScore = score
  plays = allPlays(dict, bank, prevPlayed)
  for (i,word,marginalScore) in plays:
    if len(chosenPlays[i]) <  stillNeeded[i] and word not in placedWords:
      chosenPlays[i].append(word)
      placedWords.append(word)
      expectedScore += marginalScore
      if len(chosenPlays.items()) == 12:
        break
  # Optional: print expected score.
  print(f"Expected score: {expectedScore} points.")
  return chosenPlays[round % 6][0]

# Helpers for getting player responses.
def getResponseBy(msg, cond, invalidMsg):
  while True:
    attempt = input(msg + "\n > ")
    if cond(attempt):
      return attempt
    print(invalidMsg)
  
def getResponse(msg, valids):
  return getResponseBy(msg,lambda r: r in valids,f"Invalid response. Valid responses: {', '.join(valids)}.")

def updateWordlist(wordsToValidate, wordsToRemove):
  if wordsToValidate and getResponse(f"Ok to validate: {', '.join(wordsToValidate)}? (yes/no)",["yes","no"]) == "no":
    wordsToValidate = set()
  if wordsToRemove and getResponse(f"Ok to remove: {', '.join(wordsToRemove)}? (yes/no)",["yes","no"]) == "no":
    wordsToRemove = set()

  if not (wordsToValidate + wordsToRemove):
    print("No changes to wordlist.")
    return
  
  dict = loadDict()
  newLines = (word + "!\n" if dict[word] else ".\n" for word in dict if word not in wordsToRemove)
  newLines.extend(word + "!\n" for word in wordsToValidate if word not in dict)
  newLines.sort(key = lambda l: l.rstrip("!.\n"))

  with open("wordlist.txt", "w") as outfile:
    outfile.writelines(newLines)

  # Git add, commit, push
  subprocess.run(
    ["git", "add", "wordlist.txt"],
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )

  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  if wordsToValidate and wordsToRemove:
    summary = f"auto: updated wordlist.txt: validated {len(wordsToValidate)} word{'s' if len(wordsToValidate) != 1 else ''} and removed {len(wordsToRemove)} word{'s' if len(wordsToRemove) != 1 else ''} at {timestamp}"
  elif wordsToValidate:
    summary = f"auto: updated wordlist.txt: validated {len(wordsToValidate)} word{'s' if len(wordsToValidate) != 1 else ''} at {timestamp}"
  else:
    summary = f"auto: updated wordlist.txt: removed {len(wordsToRemove)} word{'s' if len(wordsToRemove) != 1 else ''} at {timestamp}"

  filtered_validated = [w for w in sorted(wordsToValidate) if w.strip()]
  filtered_removed = [w for w in sorted(wordsToRemove) if w.strip()]
  body = "Validated words:\n" + "\n".join(filtered_validated) + "\n\n" if filtered_validated else ""
  body += "Removed words:\n" + "\n".join(filtered_removed) + "\n\n" if filtered_removed else ""

  subprocess.run(
      ["git", "commit", "-m", summary, "-m", body],
      check=True,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.PIPE,
  )

  subprocess.run(
      ["git", "push", "origin", "main"],
      check=True,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )
  print(f"Done.")
  return

def searchWords(queries=None):
  if not queries:
    response = input("Enter words to search (comma or space separated):\n > ")
    queries = [w.strip() for w in response.replace(',', ' ').split() if w.strip()]
  queries = set(queries)
  dict = loadDict()
  padding = 5 + max(len(dispWord(word,dict)) for word in queries)

  print("Search results:")
  for word in queries:
    dword = dispWord(word,dict)
    msg = ": Not found" if word not in dict else ": Validated" if dict[word] else ": Present, not validated"
    print(dword + (padding - len(dword)) * " " + msg)

  # Prompt if user wants to add/validate all words.
  if any(word not in dict or not dict[word] for word in queries) and getResponse("Add/validate all words? (yes/no)", ["yes", "no"]) == "yes":
    updateWordlist(queries, set())
  return

def sevenUniques(s):
  return len(s) == 7 and len(set(s)) == 7 and s.isalpha()

# Time to play!
def playBlossom(bank=None, fast=False):
  wordsToRemove = set()
  wordsToValidate = set()
  playAgain = True
  tprint = print if fast else _tprint
  while playAgain:
    os.system("clear")
    print(r"""
,-----.  ,--.                                       
|  |) /_ |  | ,---.  ,---.  ,---.  ,---. ,--,--,--. 
|  .-.  \|  || .-. |(  .-' (  .-' | .-. ||        | 
|  '--' /|  |' '-' '.-'  `).-'  `)' '-' '|  |  |  | 
`------' `--' `---' `----' `----'  `---' `--`--`--' 
🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸
  """)
    prevPlayed = []
    score = 0
    if not bank:
      match getResponseBy("What's the bank? (Center letter first)",lambda b : sevenUniques(b) or b == "quit","Please enter seven unique letters, or \"quit\".").lower():
        case "quit" | "q":
          return
        case bk:
          bank = [bk[0]] + sorted(list(bk)[1:])
      tprint("Okay, let's play!")
    else:
      tprint(f"Bank: {bank.upper()}.")
      bank = bank[0] + ''.join(sorted(list(bank[1:])))
    dict = loadDict(bank)
    for i in range(12):
      specialLetter = bank[(i % 6) + 1] # Rotate through bank
      tprint(f"---\nRound {i+1}. Special letter: {specialLetter.upper()}.\n")
      ouch = False
      while True:
        word = blossomBetter(bank, dict, prevPlayed, i, score)
        prevPlayed.append(word)
        tprint(f"{"Okay, then instead " if ouch else ''}I play: {dispWord(word,dict)}{", a validated word!" if dict[word] else ''}")

        if dict[word]:
          break
        match getResponse("Is that valid? (yes/no)",["yes","no","quit"]):
          case "quit" | "q":
            return
          case "no":
            wordsToRemove.add(word)
            ouch = True
          case "yes":
            wordsToValidate.add(word)
            break
    
      wordScore = scoreWord(bank,specialLetter,word)
      score += wordScore
      tprint(f"{"Great! " if not dict[word] else ''}We scored {wordScore} {"additional " if i != 0 else ''}points, for a total of {score} points.")
        
    tprint(f"\n🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸\n\nGame over! We scored {score} points.")
    playAgain = getResponse("Play again? (yes/no)",["yes","no"]) == "yes"
    bank = None
  updateWordlist(wordsToValidate, wordsToRemove)
  return

def main():
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(dest="mode", required=True)

  playParser = subparsers.add_parser("play", help="Play Blossom with optionally specified bank")
  playParser.add_argument("bank", nargs="?", default=None, help="Bank of letters (optional)")
  playParser.add_argument("-f","--fast", action="store_true", help="Play fast")

  searchParser = subparsers.add_parser("search", help="Search for words")
  searchParser.add_argument("queries", nargs="*",help="Words to be searched")

  args = parser.parse_args()

  if args.mode == "play":
    if not args.bank or sevenUniques(args.bank):
      playBlossom(fast=args.fast,bank=args.bank)
    else:
      print("Invalid bank. Please provide seven unique letters.")
      return
  else: # args.mode == "search"
    searchWords(args.queries)

if __name__ == "__main__":
  main()

# Some high scores:
# 
# R ENOSTU : 716 points
# R ENLSTU : 659 points
# T EILNRS : 657 points
# R EINOST : 624 points
# T EINORS : 616 points
#