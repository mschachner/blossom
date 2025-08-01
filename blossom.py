import os
import subprocess
import sys,time
from datetime import datetime

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

# Helpers: determine if a word's valid, get all valid words, score words.

def isValid(bank, prevPlayed, word):
  return any(c == bank[0] for c in word) and all(c in bank for c in word) and len(word) >= 4 and word not in prevPlayed

def allValidWords(bank,prevPlayed):
  valids = []
  with open("wordlist.txt") as infile:
    for line in infile:
      wd = line[0:-2] # Remove trailing punctuation
      if isValid(bank, prevPlayed, wd):
        valids.append(wd + line[-2])
    return valids

def scoreWord(bank,specialLetter,word):
  baseScore = 2*len(word)-6 if len(word) < 7 else 3*len(word)-9
  specialLetterScore = 5 * word.count(specialLetter)
  pangramScore = 7 if all(c in word for c in bank) else 0
  return baseScore + specialLetterScore + pangramScore

# The blossomBetter agent plans ahead. I don't think it's optimal though.

def allScores(bank,prevPlayed):
  words = allValidWords(bank,prevPlayed)
  tuples = [(i, word) for word in words for i in range(6)]
  return sorted(tuples,key=lambda t: scoreWord(bank,bank[t[0]+1],t[1].rstrip('.!')),reverse=True)

def blossomBetter(bank,prevPlayed,round,score):
  plays = {i:[] for i in range(6)}
  # Determine how many words are still needed for each letter.
  wordsStillNeeded = [0] * 6
  for i in range(6):
    wordsStillNeeded[i] += int(round <= i) + int(round <= i + 6)
  placedWords = []
  tuples = allScores(bank,prevPlayed)
  for (i,wd) in tuples:
    if len(plays[i]) < wordsStillNeeded[i] and wd not in placedWords:
      plays[i].append(wd)
      placedWords.append(wd)
      if len(plays.items()) == 12:
        break
  # Optional: print expected score.
  expectedScore = score + sum(scoreWord(bank,bank[1:][i % 6],wd.rstrip('.!')) for i in plays for wd in plays[i])
  tprint(f"Expected score: {expectedScore} points.")

  # Debug: print game forecast.
  # tprint(f"Plays: {plays}")
  # expectedScore = score
  # tprint(f"Forecast:")
  # for i in range(round, 12):
  #   toBePlayed = plays[i % 6][0] if i < 6 else plays[i % 6][-1].rstrip('.!')
  #   delta = scoreWord(bank,bank[i % 6 + 1],toBePlayed)
  #   expectedScore += delta
  #   tprint(f"Round {i+1}: {toBePlayed.upper()}, {delta} points. Total: {expectedScore} points.")

  return plays[round % 6][0]

# Helpers for getting player responses.

def getPlayerResponseBy(msg,cond,invalidMsg):
  while True:
    attempt = input(msg + "\n > ")
    if cond(attempt):
      return attempt
    tprint(invalidMsg)

def getPlayerResponse(msg,valids):
  return getPlayerResponseBy(msg,lambda r: r in valids,f"Invalid response. Valid responses: {', '.join(valids)}.")

def updateWordlist(wordsToValidate, wordsToRemove):
  # Assumption: input is a set of words to validate with "!" and a set of words to remove.
  if not wordsToValidate and not wordsToRemove:
    return
  
  if wordsToValidate and getPlayerResponse(f"Ok to validate: {', '.join(wordsToValidate)}? (yes/no)",["yes","no"]) == "no":
    wordsToValidate = set()
  if wordsToRemove and getPlayerResponse(f"Ok to remove: {', '.join(wordsToRemove)}? (yes/no)",["yes","no"]) == "no":
    wordsToRemove = set()

  if not wordsToValidate and not wordsToRemove:
    return
  
  # Read current lines
  with open("wordlist.txt", "r") as f:
    lines = f.readlines()

  # Replace each word in wordsToValidate with its version ending in "!"
  # or add it with a "!" if it doesn't exist.
  new_lines = []
  for line in lines:
    word = line.rstrip('.!\n')
    if word in wordsToValidate:
      new_lines.append(word + '!\n')  # Add validated word with "!"
      wordsToValidate.remove(word)     # Remove from set to avoid duplicates
    else:
      new_lines.append(line)            # Keep the original line

  # Add any remaining words to validate that were not in the file (maintaining alphabetical order)
  for word in sorted(wordsToValidate):
    new_lines.append(word + '!\n')

  # Remove wordsToRemove
  new_lines = [line for line in new_lines if line.rstrip('.!') not in wordsToRemove]

  # Sort the new lines alphabetically
  new_lines.sort()

  # Write updated lines
  with open("wordlist.txt", "w") as f:
    f.writelines(new_lines)

  # If no words were validated or removed, skip git commit and push.
  if not wordsToValidate and not wordsToRemove:
    tprint("No changes to commit.")
    return

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
  body = f"Validated words:\n" + "\n".join(filtered_validated) + "\n\n" if filtered_validated else ""
  body += f"Removed words:\n" + "\n".join(filtered_removed) + "\n\n" if filtered_removed else ""

  subprocess.run(
      ["git", "commit", "-m", summary, "-m", body],
      check=True,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )

  # Get current branch
  result = subprocess.run(
      ["git", "rev-parse", "--abbrev-ref", "HEAD"],
      capture_output=True, text=True, check=True
  )
  branch = result.stdout.strip()

  subprocess.run(
      ["git", "push", "origin", branch],
      check=True,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )
  tprint(f"Done.")
  return
  subprocess.run(
      ["git", "push", "origin", branch],
      check=True,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )
  tprint(f"Done.")
  return

def searchWords(wordsToSearch):
  displayWords = {w: None for w in wordsToSearch} 
  statuses = {w: None for w in wordsToSearch}
  with open("wordlist.txt") as infile:
    lines = infile.readlines()
    for word in wordsToSearch:
      # Only return exact matches, ignoring trailing punctuation.
      found = [line for line in lines if line.startswith(word + '.') or line.startswith(word + '!')]
      if found:
        # If it ends with '!', it's validated and will be displayed in bold green;
        # otherwise, it's not validated and is displayed in bold yellow.
        # In either case we remove the trailing punctuation and store the display version of the word, as well as its validation status.
        for line in found:
          validated = line.endswith('!\n')
          word = line.rstrip('.!\n')
          displayWords[word] = boldColorText(word.upper(), 'green' if validated else 'yellow')
          statuses[word] = "Validated" if validated else "Present, not validated"
          break  # Only display the first match.
      else:
        # Word not found. Display in bold red.
        displayWords[word] = boldColorText(word.upper(), 'red')
        statuses[word] = "Not found"
        
  # Print results.
  # 1) map to plain uppercase
  plain = {w: w.upper() for w in wordsToSearch}

  # 2) compute max width on the plain strings
  maxWordLength = max(len(p) for p in plain.values())
  maxStatusLength = max(len(s) for s in statuses.values())

  print("Search results:")
  for w in wordsToSearch:
      padded = plain[w].ljust(maxWordLength)        # pad the visible text
      # now color that padded text
      color = 'green' if statuses[w]=='Validated' else \
              'yellow' if statuses[w].startswith('Present') else 'red'
      disp  = boldColorText(padded, color)
      stat  = statuses[w].ljust(maxStatusLength)   # pad status
      print(f"{disp} : {stat}")
  
  # Prompt if user wants to add/validate all words.
  if getPlayerResponse("Add/validate all words? (yes/no)", ["yes", "no"]) == "yes":
    wordsToValidate = {w for w in wordsToSearch if statuses[w] == "Present, not validated" or statuses[w] == "Not found"}
    wordsToRemove = set()
    updateWordlist(wordsToValidate, wordsToRemove)
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
    for i in range(12):
      specialLetter = petals[i % 6] # Rotate through petals
      # Get valid word.
      while True:
        if pendingWord:
          wordsToRemove.add(word)
        else:
          tprint(f"---\nRound {i+1}. Special letter: {specialLetter.upper()}.\n")
        
        word = blossomBetter(bank, prevPlayed, i, score)
        validated = word.endswith('!')
        word = word.rstrip('.!')
        prevPlayed.append(word)
        # Display version of word. Always bolded. If validated, in green; otherwise in yellow.
        if validated:
          display_word = f"\033[1;32m{word.upper()}\033[0m"  # Green bold
        else:
          display_word = f"\033[1;33m{word.upper()}\033[0m"  # Yellow bold
        tprint(f"{"Okay, then instead " if pendingWord else ''}I play: {display_word}{", a validated word!" if validated else ''}")

        if not validated:
          response = getPlayerResponse("Is that valid? (yes/no)",["yes","no","quit"])
          if response in ["quit"]:
            return
          elif response in ["no"]:
            pendingWord = True
            continue
          else:  # response == "yes"
            wordstoValidate.add(word)
        
        wordScore = scoreWord(bank,specialLetter,word)
        score += wordScore
        tprint(f"{"Great! " if not validated else ''}We scored {wordScore} {"additional " if i != 0 else ''}points, for a total of {score} points.")
        pendingWord = False
        break

    tprint(f"\n🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸\n\nGame over! We scored {score} points.")
    playAgain = getPlayerResponse("Play again? (yes/no)",["yes","no"])
    if playAgain == "yes":
      bank = None
  updateWordlist(wordstoValidate, wordsToRemove)
  return

# CLI functionality:
# blossom.py                        | no arguments, prompt for bank.
# blossom.py --help                 | print usage message. 
# blossom.py bank                   | use the given bank.
# blossom.py add    word1 word2 ... | add words to the dictionary, or validate them if they already exist.
# blossom.py search word1 word2 ... | search for words and validation statuses in the dictionary.

def main():
  if len(sys.argv) == 1:
    playBlossom()
  elif len(sys.argv) == 2 and sys.argv[1] in ["--help", "-h"]:
    print("Usage: blossom.py [bank] [add word1 word2 ...] [search word1 word2 ...]")
    print("  bank: a string of seven unique letters, with the center letter first.")
    print("  add: add words to the dictionary, or validate them if they already exist.")
    print("  search: search for words and validation statuses in the dictionary.")
    return
  elif len(sys.argv) >= 2 and sys.argv[1] == "add":
    if len(sys.argv) < 3:
      print("Usage: blossom.py add word1 word2 ...")
      return
    # Add words to the dictionary.
    wordsToValidate = set(sys.argv[2:])
    updateWordlist(wordsToValidate, set())
  elif len(sys.argv) >= 2 and sys.argv[1] == "search":
    if len(sys.argv) < 3:
      print("Usage: blossom.py search word1 word2 ...")
      return
    # Search for words in the dictionary.
    wordsToSearch = sys.argv[2:]
    searchWords(wordsToSearch)
  else:
    # Assume the first argument is a bank.
    bank = sys.argv[1]
    if len(bank) != 7 or not sevenUniques(bank):
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