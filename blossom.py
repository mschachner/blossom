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
      continue
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
    specials = []
    score = 0
    invalidFlag = False
    pendingWord = False
    bank = getPlayerResponseBy("What's the word bank? (Center letter first)",lambda b : sevenUniques(b) or b == "quit","Please enter seven unique letters, or \"quit\".").lower()
    if bank in ["quit","q"]:
      return
    else:
      bank = list(bank)
      petals = bank[1:]
      petalCounts = {c: 0 for c in petals}
    print("Okay, let's play!")
    print(f"Engine: {engine}")
    for i in range(13):
      while True:
        if i >= 5 or invalidFlag: # We already know the special letter (or can reason it out), but we still need to know whether the last word was valid
          response = getPlayerResponse("Is that valid? (yes/no)",["yes","no","quit"])
        else:
          if not pendingWord: # We only need to get the special letter from the player.
            response = getPlayerResponse("Special letter?",petals + ["quit"])
          else: # We need to get both the special letter and whether the last word was invalid.
            response = getPlayerResponse("Special letter? (Or \"invalid\" if the last word was invalid.)",petals + ["invalid","quit"])


        if response in ["quit"]:
          return
        
        if response in ["no","invalid"]:
          # The last word was invalid.
          invalidFlag = True
          wordsToRemove.add(word)
          # play another word and head back to the top.
          word = engine(bank,specialLetter,petalCounts,prevPlayed)
          print(f"Okay, then instead I play: {word.upper()}")
          pendingWord = True
          continue

        else:
          # The last word (if any) was valid and the player has possibly specified a special letter
          if pendingWord:
            # There is a previous word to be scored
            wordScore = scoreWord(bank,specialLetter,word)
            score += wordScore
            petalCounts[specialLetter] += 1
            print(f"Okay, last word was valid. We scored {wordScore} additional points, for a total of {score} points.")
            pendingWord = False
          
          if i == 12:
            # The game is over!
            break

          if i == 5:
            # reason out the last special letter
            specialLetter = [c for c in bank[1:] if c not in specials][0]
            specials.append(specialLetter)


          if i >= 6:
            specialLetter = specials[i-6]
            print(f"Next special letter: {specialLetter.upper()}")

          if i >= 5:
            # play a word
            word = engine(bank,specialLetter,petalCounts,prevPlayed)
            print(f"I play: {word.upper()}")
            pendingWord = True
            break
          
          if response in ["yes"] and invalidFlag:
            invalidFlag = False
            continue

          elif not pendingWord:
            # player's response was the next special letter

            specialLetter = response
            specials.append(specialLetter)

            # play a word
            word = engine(bank,specialLetter,petalCounts,prevPlayed)
            print(f"I play: {word.upper()}")
            pendingWord = True
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