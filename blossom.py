import os
import subprocess
import sys,time
from datetime import datetime

def tprint(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    """Typewriter-style print. Same signature as print()."""
    text = sep.join(map(str, objects)) + end

    # If not an interactive terminal, print fast.
    if not getattr(file, "isatty", lambda: False)():
        file.write(text)
        if flush:
            file.flush()
        return

    # Tuned speeds
    cps = 120                     # characters per second
    punct_pause = 0.20           # pause after . ! ?
    mid_pause = 0.12             # pause after , ; : – —
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

# Helpers: determine if a word's valid, get all valid words, score words.

def isValid(bank, prevPlayed, word):
  word = word[0:-1] # Remove trailing punctuation
  return any(c == bank[0] for c in word) and all(c in bank for c in word) and len(word) >= 4 and word not in prevPlayed

def allValidWords(bank,prevPlayed):
  words = []
  with open("wordlist.txt") as infile:
    for line in infile:
      words.append(line[0:-1])
    return filter(lambda word: isValid(bank,prevPlayed,word),words)

def scoreWord(bank,specialLetter,word):
  # Assumption: word ends with punctuation, which we remove for scoring.
  word = word[0:-1]  # Remove trailing punctuation
  baseScore = 2*len(word)-6 if len(word) < 7 else 3*len(word)-9
  specialLetterScore = 5 * word.count(specialLetter)
  pangramScore = 7 if all(c in word for c in bank) else 0
  return baseScore + specialLetterScore + pangramScore

# The blossomGreedy agent just always plays the highest-scoring word available.

def greedyScores(bank, specialLetter, prevPlayed):
  words = allValidWords(bank,prevPlayed)
  return sorted(words,key = lambda word: scoreWord(bank,specialLetter,word))[-20:-1]

def blossomGreedy(bank,specialLetter, _, prevPlayed):
  words = allValidWords(bank,prevPlayed)
  word = max(words,key = lambda word: scoreWord(bank,specialLetter,word))
  prevPlayed.append(word)
  return word

# The blossomBetter agent plans ahead. I don't think it's optimal though.

def allScores(bank,prevPlayed):
  words = allValidWords(bank,prevPlayed)
  tuples = [(c, word) for word in words for c in bank[1:]]
  return sorted(tuples,key=lambda t: scoreWord(bank,t[0],t[1]),reverse=True)

def blossomBetter(bank,specialLetter,petalCounts,prevPlayed):
  plays = {c:[] for c in bank[1:]}
  placedWords = []
  tuples = allScores(bank,prevPlayed)
  for (ch,wd) in tuples:
    count = petalCounts[ch]
    if len(plays[ch]) < (2-count) and wd not in placedWords:
      plays[ch].append(wd)
      placedWords.append(wd)
      continue
  word = plays[specialLetter][0]
  prevPlayed.append(word[0:-1])  # Remove trailing punctuation
  return word

# Helpers for getting player responses.

def getPlayerResponseBy(msg,cond,invalidMsg):
  while True:
    attempt = input(msg + "\n > ")
    if cond(attempt):
      return attempt
    tprint(invalidMsg)

def getPlayerResponse(msg,valids):
  return getPlayerResponseBy(msg,lambda r: r in valids,f"Invalid response. Valid responses: {', '.join(valids)}.")

# Wordlist management: remove words and commit to git.

def removeAndCommit(wordsToRemove):
  # Assumption: input is set of words to remove, WITH trailing punctuation.
  wordsToRemove_display = [w[0:-1] for w in wordsToRemove]  # Remove trailing punctuation
  if not wordsToRemove or getPlayerResponse(f"Ok to remove: {', '.join(wordsToRemove_display)}? (yes/no)",["yes","no"]) == "no":
    return
  
  # Read current lines
  with open("wordlist.txt", "r") as f:
      lines = f.readlines()

  # Filter out lines
  new_lines = [line for line in lines if line.strip() not in wordsToRemove]

  # Write updated lines
  with open("wordlist.txt", "w") as f:
      f.writelines(new_lines)

  # Git add
  subprocess.run(
    ["git", "add", "wordlist.txt"],
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )

  # Commit message and body
  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  summary = f"Removed {len(wordsToRemove)} words at {timestamp}"
  body = "\n".join(sorted(wordsToRemove_display))

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
  print(f"Removed.")
  return

# Wordlist management: validate words and commit to git.

def validateAndCommit(wordstoValidate):
  # Assumption: input is set of words to validate, without trailing punctuation.
  if not wordstoValidate or getPlayerResponse(f"Ok to validate: {', '.join(wordstoValidate)}? (yes/no)",["yes","no"]) == "no":
    return
  
  # Read current lines
  with open("wordlist.txt", "r") as f:
    lines = f.readlines()

  # Replace each word in wordstoValidate with its version ending in "!"
  wordstoValidate_set = set(wordstoValidate)
  new_lines = []
  for line in lines:
    word = line.rstrip(".!\n")
    if word in wordstoValidate_set:
      new_lines.append(f"{word}!\n")
    else:
      new_lines.append(line)
  with open("wordlist.txt", "w") as f:
    f.writelines(new_lines)

  subprocess.run(
    ["git", "add", "wordlist.txt"],
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )

  # Commit message and body
  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  summary = f"Validated {len(wordstoValidate)} words at {timestamp}"
  body = "\n".join(sorted(wordstoValidate))

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
  tprint(f"Validated.")
  return

def sevenUniques(s):
  return len(s) == 7 and len(set(s)) == 7 and s.isalpha()

# Time to play!

def playBlossom(engine):
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
    response = getPlayerResponseBy("What's the word bank? (Center letter first)",lambda b : sevenUniques(b) or b == "quit","Please enter seven unique letters, or \"quit\".").lower()
    if response in ["quit","q"]:
      return
    else:
      petals = sorted(list(response)[1:])
      bank = [response[0]] + petals
      specialLetter = petals[0]
      petalCounts = {c: 0 for c in petals}
    tprint("Okay, let's play!")
    tprint(f"Engine: {engine}")

    # Some string vars
    preMessage = "Okay, then instead "
    postMessage = ", a validated word!"

    for i in range(12):
      specialLetter = petals[i % 6] # Rotate through petals
      # Get valid word.
      while True:
        if pendingWord:
          wordsToRemove.add(word) # Added with punctuation.
        else:
          tprint(f"---\nRound {i+1}. Special letter: {specialLetter.upper()}.\n")
        
        word = engine(bank,specialLetter,petalCounts,prevPlayed)
        word_display = word[0:-1]  # Remove trailing punctuation
        message = f"{preMessage if pendingWord else ''}I play: {word_display.upper()}{postMessage if word[-1] == '!' else ''}"
        tprint(message)

        if word[-1] != '!':  # Word not validated.
          response = getPlayerResponse("Is that valid? (yes/no)",["yes","no","quit"])
          if response in ["quit"]:
            return
          elif response in ["no"]:
            pendingWord = True
            continue
          else:  # response == "yes"
            wordstoValidate.add(word_display)
        
        wordScore = scoreWord(bank,specialLetter,word)
        score += wordScore
        petalCounts[specialLetter] += 1
        tprint(f"{"Great! " if word[-1] != '!' else ''}We scored {wordScore} {"additional " if i != 0 else ''}points, for a total of {score} points.")
        pendingWord = False
        break

    tprint(f"\n🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸\n\nGame over! We scored {score} points.")
    playAgain = getPlayerResponse("Play again? (yes/no)",["yes","no"])
  validateAndCommit(wordstoValidate)
  removeAndCommit(wordsToRemove)
  tprint("Thanks for playing!")
  return

playBlossom(blossomBetter)

# Some high scores:
# 
# R ENOSTU : 617 points
# R EINOST : 599 points
# N EIORST : 580 points
# T EINORS : 585 points
# T EILNRS : 571 points
#
#
