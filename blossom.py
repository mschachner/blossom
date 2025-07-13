import os
import subprocess
from datetime import datetime

def isValid(bank, prevPlayed, word):
  return any(c == bank[0] for c in word) and all(c in bank for c in word) and len(word) >= 4 and word not in prevPlayed

def allValidWords(bank,prevPlayed):
  words = []
  with open("wordlist.txt") as infile:
    for line in infile:
      words.append(line[0:-1])
    return filter(lambda word: isValid(bank,prevPlayed,word),words)

def scoreWord(bank,specialLetter,word):
  baseScore = 2*len(word)-6 if len(word) < 7 else 3*len(word)-9
  specialLetterScore = 5 * word.count(specialLetter)
  pangramScore = 7 if all(c in word for c in bank) else 0
  return baseScore + specialLetterScore + pangramScore

def greedyScores(bank, specialLetter, prevPlayed):
  words = allValidWords(bank,prevPlayed)
  return sorted(words,key = lambda word: scoreWord(bank,specialLetter,word))[-20:-1]

def blossomGreedy(bank,specialLetter,petalCounts,prevPlayed):
  words = allValidWords(bank,prevPlayed)
  word = max(words,key = lambda word: scoreWord(bank,specialLetter,word))
  prevPlayed.append(word)
  return word

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
      print(f"Placed {wd} in {ch}")
      continue
  print(f"Plays: {plays}")
  word = plays[specialLetter][0]
  prevPlayed.append(word)
  return word

def getPlayerResponseBy(msg,cond,invalidMsg):
  while True:
    attempt = input(msg + "\n > ")
    if cond(attempt):
      return attempt
    print(invalidMsg)

def getPlayerResponse(msg,valids):
  return getPlayerResponseBy(msg,lambda r: r in valids,f"Invalid response. Valid responses: {', '.join(valids)}.")

def removeAndCommit(wordsToRemove):
  if not wordsToRemove or getPlayerResponse(f"Ok to remove: {', '.join(wordsToRemove)}? (yes/no)",["yes","no"]) == "no":
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
  body = "\n".join(sorted(wordsToRemove))

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

def sevenUniques(s):
  return len(s) == 7 and len(set(s)) == 7 and s.isalpha()

def playBlossom(engine):
  wordsToRemove = set()
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
    print("Okay, let's play!")
    print(f"Engine: {engine}")
    for i in range(12):
      # Get valid word.
      while True:
        if pendingWord:
          # We already tried a word and it failed.
          wordsToRemove.add(word)
          word = engine(bank,specialLetter,petalCounts,prevPlayed)
          print(f"Okay, then instead I play: {word.upper()}")

        else:
          specialLetter = petals[i % 6]
          word = engine(bank,specialLetter,petalCounts,prevPlayed)
          print(f"Round {i+1}. Special letter: {specialLetter.upper()}")
          print(f"I play: {word.upper()}")
          pendingWord = True

        response = getPlayerResponse("Is that valid? (yes/no)",["yes","no","quit"])
        if response in ["quit"]:
          return
        
        if response in ["no"]:
          continue

        else:
          # Score previous word.
          wordScore = scoreWord(bank,specialLetter,word)
          score += wordScore
          petalCounts[specialLetter] += 1
          print(f"Great! We scored {wordScore} additional points, for a total of {score} points.")
          pendingWord = False
          break

    print(f"\n🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸\n\nGame over! We scored {score} points.")
    playAgain = getPlayerResponse("Play again? (yes/no)",["yes","no"])
  removeAndCommit(wordsToRemove)
  print("Thanks for playing!")
  return

playBlossom(blossomBetter)

# Some high scores:
# 
# R EINOST : 579 points
# T EILNRS : 578 points
# N EIORST : 577 points
# T EINORS : 575 points
# R ENOSTU : 574 points
#
#