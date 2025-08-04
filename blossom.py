import os
import subprocess
import sys,time
from datetime import datetime

# Aesthetics: color text, typewriter-style print.

def boldColorText(text, color):
  styles = {
      "reset": "\033[0m",
      "boldred": "\033[1;31m",
      "boldgreen": "\033[1;32m",
      "boldyellow": "\033[1;33m",
  }
  return f"{styles['bold' + color]}{text}{styles['reset']}"

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

tprint = _tprint  # Alias for convenience; toggle to ordinary print if needed.

# Every word comes with a validation status, a boolean indicating whether the word has been validated by a human player.

class Word(str):
    def __new__(cls, word, validated=False):
        # Create a new instance of Word, inheriting from str.
        instance = super().__new__(cls, word)
        instance.validated = validated
        return instance

    def __str__(self):
        # Validated words are rendered in bold green, others in bold yellow.
        if self.validated:
            return boldColorText(self.upper(), "green")
        else:
            return boldColorText(self.upper(), "yellow")
    
    def __repr__(self):
        # Return the plain string for debugging and logic
        return super().__str__()
    
    def validate(self):
        # Mark the word as validated.
        self.validated = True
        
def loadWordlist(bank=None):
  wordList = set()
  with open("wordlist.txt") as infile:
    for line in infile:
      word = line[0:-2]
      if not bank or (any(c == bank[0] for c in word) and all(c in bank for c in word)): # word is legal
        if line.endswith('!\n'):
          # Validated word.
          wordList.add(Word(word, True))
        else:
          # Not validated word.
          wordList.add(Word(word, False))
  return wordList

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

def blossomBetter(bank, legalWords, prevPlayed, round, score):
  chosenPlays = {i:[] for i in range(6)}
  # Determine how many words are still needed for each letter.
  stillNeeded = [int(round <= i) + int(round <= i+6) for i in range(6)]
  placedWords = []
  expectedScore = score
  plays = allPlays(legalWords, bank,prevPlayed)
  for (i,word,marginalScore) in plays:
    if len(chosenPlays[i]) <  stillNeeded[i] and word not in placedWords:
      chosenPlays[i].append(word)
      placedWords.append(word)
      expectedScore += marginalScore
      if len(chosenPlays.items()) == 12:
        break
  # Optional: print expected score.
  tprint(f"Expected score: {expectedScore} points.")

  # # Debug: print game forecast.
  # tprint(f"Plays: {chosenPlays}")
  # expectedScore = score
  # tprint(f"Forecast:")
  # for i in range(round, 12):
  #   toBePlayed = chosenPlays[i % 6][0] if i < 6 else chosenPlays[i % 6][-1].rstrip('.!')
  #   delta = scoreWord(bank,bank[i % 6 + 1],toBePlayed)
  #   expectedScore += delta
  #   tprint(f"Round {i+1}: {toBePlayed.upper()}, {delta} points. Total: {expectedScore} points.")

  return chosenPlays[round % 6][0]

# Helpers for getting player responses.

def getPlayerResponseBy(msg,cond,invalidMsg):
  while True:
    attempt = input(msg + "\n > ")
    return attempt if cond(attempt) else print(invalidMsg)
  
def getPlayerResponse(msg,valids):
  return getPlayerResponseBy(msg,lambda r: r in valids,f"Invalid response. Valid responses: {', '.join(valids)}.")

def updateWordlist(wordsToValidate, wordsToRemove):
  if wordsToValidate and getPlayerResponse(f"Ok to validate: {', '.join(wordsToValidate)}? (yes/no)",["yes","no"]) == "no":
    wordsToValidate = set()
  if wordsToRemove and getPlayerResponse(f"Ok to remove: {', '.join(wordsToRemove)}? (yes/no)",["yes","no"]) == "no":
    wordsToRemove = set()

  if not wordsToValidate and not wordsToRemove:
    print("No changes to wordlist.")
    return
  
  # Update wordlist.txt: mark validated words with "!", maintain alphabetical order.
  with open("wordlist.txt", "r") as infile:
    lines = infile.readlines()

  newLines = []
  existingWords = set()
  for line in lines:
    word = line.rstrip('!.\n')
    if word in wordsToRemove:
      continue
    if word in wordsToValidate:
      newLines.append(f"{word}!\n")
    else:
      # Preserve original status if not validated.
      newLines.append(line)
    existingWords.add(word)

  # Add any new validated words not already present.
  for word in wordsToValidate:
    if word not in existingWords:
      newLines.append(f"{word}!\n")

  # Sort all lines alphabetically by word.
  newLines.sort(key=lambda l: l.rstrip('!.\n'))

  with open("wordlist.txt", "w") as outfile:
    outfile.writelines(newLines)

  # Git add
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
  tprint(f"Done.")
  return

def searchWords(wordsToSearch=None):
  if wordsToSearch is None or not wordsToSearch:
    response = input("Enter words to search (comma or space separated):\n > ")
    wordsToSearch = [w.strip() for w in response.replace(',', ' ').split() if w.strip()]
  if not wordsToSearch:
    print("No words provided for search.")
    return
  wordsToSearch = set(wordsToSearch)

  # Calculate padding
  maxLength = max(len(word) for word in wordsToSearch)
  padding = maxLength + 2  # Add some space for formatting

  # Prepare set of words to validate if user so chooses
  wordsToValidate = set()

  print("Search results:")
  wordList = loadWordlist()
  for word in wordList:
    if word in wordsToSearch:
      if word.validated:
        print(f"{word}{(padding - len(word)) * ' '}: Validated")
      else:
        print(f"{word}{(padding - len(word)) * ' '}: Present, not validated")
        wordsToValidate.add(word)
      wordsToSearch.remove(word)  # Remove found word to avoid duplicates
  for word in wordsToSearch:
    print(f"{boldColorText(word.upper().ljust(padding), 'red')}: Not found")
    wordsToValidate.add(word) 

  # Prompt if user wants to add/validate all words.
  if wordsToValidate and getPlayerResponse("Add/validate all words? (yes/no)", ["yes", "no"]) == "yes":
    updateWordlist(wordsToValidate, set())
  return

def sevenUniques(s):
  return len(s) == 7 and len(set(s)) == 7 and s.isalpha()

# Time to play!

def playBlossom(bank=None):
  wordsToRemove = set()
  wordstoValidate = set()
  playAgain = "yes"
  while playAgain in ["yes"]:
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
    pendingWord = False
    if bank is None:
      response = getPlayerResponseBy("What's the bank? (Center letter first)",lambda b : sevenUniques(b) or b == "quit","Please enter seven unique letters, or \"quit\".").lower()
      if response in ["quit","q"]:
        return
      else: # Bank is valid.
        petals = sorted(list(response)[1:])
        bank = [response[0]] + petals
      tprint("Okay, let's play!")
    else:
      tprint(f"Bank: {bank.upper()}.")
      petals = sorted(list(bank[1:]))
      bank = bank[0] + ''.join(petals)
    legalWords = loadWordlist(bank)
    for i in range(12):
      specialLetter = petals[i % 6] # Rotate through petals
      # Get valid word.
      while True:
        if pendingWord:
          wordsToRemove.add(word)
        else:
          tprint(f"---\nRound {i+1}. Special letter: {specialLetter.upper()}.\n")
        
        word = blossomBetter(bank, legalWords, prevPlayed, i, score)
        prevPlayed.append(word)
        tprint(f"{"Okay, then instead " if pendingWord else ''}I play: {word}{", a validated word!" if word.validated else ''}")

        if not word.validated:
          response = getPlayerResponse("Is that valid? (yes/no)",["yes","no","quit"])
          if response == "quit":
            return
          elif response  == "no":
            pendingWord = True
            continue
          else:  # response == "yes"
            wordstoValidate.add(word)
        
        wordScore = scoreWord(bank,specialLetter,word)
        score += wordScore
        tprint(f"{"Great! " if not word.validated else ''}We scored {wordScore} {"additional " if i != 0 else ''}points, for a total of {score} points.")
        pendingWord = False
        break

    tprint(f"\n🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸\n\nGame over! We scored {score} points.")
    playAgain = getPlayerResponse("Play again? (yes/no)",["yes","no"])
    if playAgain == "yes":
      bank = None
  updateWordlist(wordstoValidate, wordsToRemove)
  return

# CLI functionality:
# blossom.py                            | no arguments, prompt for bank.
# blossom.py --help                     | print usage message. 
# blossom.py <bank>                     | use the given bank.
# blossom.py search                     | Open word search / add dialog
# blossom.py search <word1> <word2> ... | 

def main():
  if len(sys.argv) == 1:
    playBlossom()
  elif len(sys.argv) == 2 and sys.argv[1] in ["--help", "-h"]:
    print("Usage: blossom.py [bank] [search word1 word2 ...]")
    print("  bank: a string of seven unique letters, with the center letter first.")
    print("  search: search for words and validation statuses in the dictionary.")
    return
  elif len(sys.argv) >= 2 and sys.argv[1] == "search":
    # Search for words in the dictionary.
    wordsToSearch = sys.argv[2:]
    searchWords(wordsToSearch)
  else:
    # Assume the first argument is a bank.
    bank = sys.argv[1]
    if not sevenUniques(bank):
      print("Invalid bank. Please provide seven unique letters.")
      return
    playBlossom(bank)

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