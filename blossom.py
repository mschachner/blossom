import os
import subprocess
import sys,time
from datetime import datetime
import argparse

# Aesthetics: color text, typewriter-style print.
def dispWord(word,dictionary):
  styles = {
      "reset": "\033[0m",
      "boldred": "\033[1;31m",
      "boldgreen": "\033[1;32m",
      "boldyellow": "\033[1;33m",
  }
  color = "red" if word not in dictionary else "yellow" if not dictionary[word] else "green"
  icon = "❌ " if word not in dictionary else "🟡 " if not dictionary[word] else "🌸 " if len(set(word)) == 7 else "✅ "
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
  dictionary = {}
  with open("wordlist.txt") as infile:
    for line in infile:
      word = line[0:-2]
      if not bank or (any(c == bank[0] for c in word) and all(c in bank for c in word)): # word is legal
        dictionary[word] = line.endswith('!\n')
  return dictionary

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

def blossomBetter(bank, dictionary, prevPlayed, round, score):
  chosenPlays = {i:[] for i in range(6)}
  # Determine how many words are still needed for each letter.
  stillNeeded = [int(round <= i) + int(round <= i+6) for i in range(6)]
  placedWords = []
  expectedScore = score
  plays = allPlays(dictionary, bank, prevPlayed)
  for (i,word,marginalScore) in plays:
    if len(chosenPlays[i]) <  stillNeeded[i] and word not in placedWords:
      chosenPlays[i].append(word)
      placedWords.append(word)
      expectedScore += marginalScore
      if len(chosenPlays.items()) == 12:
        break
  # Debug: print game forecast.
  # print(f"Plays: {chosenPlays}")
  # expectedScore = score
  # print(f"Forecast:")
  # for i in range(round, 12):
  #   toBePlayed = chosenPlays[i % 6][0] if i < 6 else chosenPlays[i % 6][-1]
  #   delta = scoreWord(bank,bank[i % 6 + 1],toBePlayed)
  #   expectedScore += delta
  #   print(f"Round {i+1}: {toBePlayed.upper()}, {delta} points. Total: {expectedScore} points.")
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

  if not wordsToRemove and not wordsToValidate:
    print("No changes to wordlist.")
    return
  
  dictionary = loadDict()
  newLines = list(word + ("!\n" if dictionary[word] or word in wordsToValidate else ".\n") for word in dictionary if word not in wordsToRemove)
  newLines.extend(word + "!\n" for word in wordsToValidate if word not in dictionary)
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
  dictionary = loadDict()
  padding = 5 + max(len(dispWord(word,dictionary)) for word in queries)

  print("Search results:")
  for word in queries:
    dword = dispWord(word,dictionary)
    msg = ": Not found" if word not in dictionary else ": Validated" if dictionary[word] else ": Present, not validated"
    print(dword + (padding - len(dword)) * " " + msg)

  # Prompt if user wants to add/validate all words.
  if any(word not in dictionary or not dictionary[word] for word in queries) and getResponse("Add/validate all words? (yes/no)", ["yes", "no"]) == "yes":
    updateWordlist(queries, set())
  return

def addWordScore(word, score, specialLetter):
  with open("scores.txt", "r+") as f:
    # First line of scores.txt holds the highest word score.
    highestWordScore = f.readline().strip().split(" ")
    if score > int(highestWordScore[2]):
      print(f"That's a new word high score!")
      f.seek(0)
      f.truncate()
      f.write(f"{word} {specialLetter} {score}\n")

def addGameScore(bank, score):
  scoreRecord = f"{str(bank).upper()} {score} {datetime.now().strftime('%Y-%m-%d')}"
  with open("scores.txt", "r+") as f:
    highestWordScore = f.readline().strip().split(" ")
    scores = [line.strip() for line in f.readlines()]
    # If bank is already in scores, update score instead of adding new record
    if any(scoreRecord.split(" ")[0] == score.split(" ")[0] for score in scores):
      for i, score in enumerate(scores):
        if scoreRecord.split(" ")[0] == score.split(" ")[0]:
          scores[i] = scoreRecord
          break
    else:
      scores.append(scoreRecord)
    scores.sort(key=lambda x: int(x.split(" ")[1]), reverse=True)
    rank = 1
    for i, score in enumerate(scores):
      if score == scoreRecord:
        rank = i + 1
        break
    print(f"{"New high score!" if rank == 1 else f"Rank: {rank}"}")
    f.seek(0)
    f.truncate()
    f.write(f"{highestWordScore[0]} {highestWordScore[1]} {highestWordScore[2]}\n")
    for score in scores:
      f.write(score + "\n")
  return

def showStats():
  dictionary = loadDict()
  print(f"Total words: {len(dictionary)}")
  print(f"Validated words: {sum(1 for word in dictionary if dictionary[word])}")
  longestWord = max((word for word in dictionary if dictionary[word]), key=len)
  print(f"Longest validated word: {dispWord(longestWord,dictionary)} ({len(longestWord)} letters)")
  with open("scores.txt", "r") as f:
    highestWordScore = f.readline().strip().split(" ")
    scores = [line.strip() for line in f.readlines()]
    scores.sort(key=lambda x: int(x.split(" ")[1]), reverse=True)
  print(f"Highest word score: {dispWord(highestWordScore[0],dictionary)} ({highestWordScore[1].upper()}), {highestWordScore[2]} points")
  print(f"Games played: {len(scores)}")
  print("Top scores:")
  for i in range(min(10, len(scores))):
    print(f"{i+1}. {scores[i].split(' ')[0]}: {scores[i].split(' ')[1]} points, {scores[i].split(' ')[2]}")

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
          bank = bk[0] + ''.join(sorted(list(bk)[1:]))
      tprint("Okay, let's play!")
    else:
      tprint(f"Bank: {bank.upper()}.")
      bank = bank[0] + ''.join(sorted(list(bank[1:])))
    dictionary = loadDict(bank)
    for i in range(12):
      specialLetter = bank[(i % 6) + 1] # Rotate through bank
      tprint(f"---\nRound {i+1}. Special letter: {specialLetter.upper()}.\n")
      ouch = False
      while True:
        word = blossomBetter(bank, dictionary, prevPlayed, i, score)
        prevPlayed.append(word)
        tprint(f"{"Okay, then instead " if ouch else ''}I play: {dispWord(word,dictionary)}{", a validated word!" if dictionary[word] else ''}")

        if dictionary[word]:
          break
        match getResponse("Is that valid? (yes/no)",["yes","no","quit"]):
          case "no":
            wordsToRemove.add(word)
            ouch = True
          case "yes":
            wordsToValidate.add(word)
            break
          case _:
            return
    
      wordScore = scoreWord(bank,specialLetter,word)
      addWordScore(word, wordScore, specialLetter)
      score += wordScore
      tprint(f"{"Great! " if not dictionary[word] else ''}We scored {wordScore} {"additional " if i != 0 else ''}points, for a total of {score} points.")
        
    tprint(f"\n🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸\n\nGame over! We scored {score} points.")
    addGameScore(bank, score)
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

  searchParser = subparsers.add_parser("stats", help="Show stats")

  args = parser.parse_args()

  if args.mode == "play":
    if not args.bank or sevenUniques(args.bank):
      playBlossom(fast=args.fast,bank=args.bank)
    else:
      print("Invalid bank. Please provide seven unique letters.")
      return
  elif args.mode == "stats":
    showStats()
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