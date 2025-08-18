import os
import subprocess
from datetime import datetime

from .utils import _tprint, dispWord, getResponse, getResponseBy, sevenUniques
from .wordlist import loadDict, updateWordlist


def scoreWord(bank, specialLetter, word):
    baseScore = 2 * len(word) - 6 if len(word) < 7 else 3 * len(word) - 9
    specialLetterScore = 5 * word.count(specialLetter)
    pangramScore = 7 if all(c in word for c in bank) else 0
    return baseScore + specialLetterScore + pangramScore


def advanceSL(bank, specialLetter, lastWord=None):
    if not lastWord or specialLetter in lastWord:
        return bank[(bank.index(specialLetter) % 6) + 1]
    return specialLetter


def blossomBetter(bank, dictionary, prevPlayed, round, specialLetter, score):
    allPlays = []
    chosenPlays = {petal: [] for petal in bank[1:]}
    stillNeeded = {petal: 0 for petal in bank[1:]}
    petal = specialLetter
    for i in range(round, 12):
        stillNeeded[petal] += 1
        petal = advanceSL(bank, petal)
    for word in (w for w in dictionary if w not in prevPlayed):
        for petal in bank[1:]:
            allPlays.append((petal, word))

    allPlays.sort(key=lambda x: scoreWord(bank, x[0], x[1]), reverse=True)
    for (petal, word) in allPlays:
        if (
            len(chosenPlays[petal]) < stillNeeded[petal]
            and word not in [w for p in chosenPlays.values() for w in p]
        ):
            chosenPlays[petal].append(word)
        if sum(len(p) for p in chosenPlays.values()) == 12 - round:
            break
    expectedScore = score + sum(
        scoreWord(bank, petal, word) for petal in bank[1:] for word in chosenPlays[petal]
    )
    print(f"Expected score: {expectedScore} points.")
    return chosenPlays[specialLetter][0]


def addWordScore(word, score, specialLetter):
    with open("scores.txt", "r+") as f:
        highestWordScore = f.readline().strip().split(" ")
        if score > int(highestWordScore[2]):
            print("That's a new word high score!")
            f.seek(0)
            f.truncate()
            f.write(f"{word} {specialLetter} {score}\n")


def addGameScore(bank, score):
    scoreRecord = f"{str(bank).upper()} {score} {datetime.now().strftime('%Y-%m-%d')}"
    with open("scores.txt", "r+") as f:
        highestWordScore = f.readline().strip().split(" ")
        scores = [line.strip() for line in f.readlines()]
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
        print(f"{'New high score!' if rank == 1 else f'Rank: {rank}'}")
        f.seek(0)
        f.truncate()
        f.write(f"{highestWordScore[0]} {highestWordScore[1]} {highestWordScore[2]}\n")
        for score in scores:
            f.write(score + "\n")
    return


def showStats():
    with open("scores.txt", "r") as f:
        highestWordScore = f.readline().strip().split(" ")
        scores = [line.strip() for line in f.readlines()]
    dictionary = loadDict()
    longestWord = max((word for word in dictionary if dictionary[word]), key=len)
    totalWords = len(dictionary)
    validatedWords = sum(1 for word in dictionary if dictionary[word])
    totalPangrams = sum(1 for word in dictionary if len(set(word)) == 7)
    validatedPangrams = sum(1 for word in dictionary if dictionary[word] and len(set(word)) == 7)
    print(f"Total words: {totalWords}")
    print(f"Validated words: {validatedWords} ({validatedWords/totalWords*100:.2f}%)")
    print(f"Total pangrams: {totalPangrams}")
    print(f"Validated pangrams: {validatedPangrams} ({validatedPangrams/totalPangrams*100:.2f}%)")
    print(
        f"Longest validated word: {dispWord(longestWord, dictionary)} ({len(longestWord)} letters)"
    )
    print(
        f"Highest word score: {dispWord(highestWordScore[0], dictionary)} ({highestWordScore[1].upper()}), {highestWordScore[2]} points"
    )
    print(f"Banks played: {len(scores)}")
    print("Top scores:")
    for i in range(min(10, len(scores))):
        print(
            f"{i+1}.{'  ' if i < 9 else ' '}{scores[i].split(' ')[0]}: {scores[i].split(' ')[1].rjust(max(len(score.split(' ')[1]) for score in scores))} points, {scores[i].split(' ')[2]}"
        )


def updateScores():
    if getResponse("Update scores.txt? (yes/no)", ["yes", "no"]) == "no":
        return
    subprocess.run(
        ["git", "add", "scores.txt"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = f"auto: updated scores.txt at {timestamp}"
    subprocess.run(
        ["git", "commit", "-m", summary],
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
    print("Done.")
    return


def playBlossom(bank=None, fast=False):
    wordsToRemove = set()
    wordsToValidate = set()
    playAgain = True
    tprint = print if fast else _tprint
    while playAgain:
        os.system("clear")
        print(
            r"""
,-----.  ,--.
|  |) /_ |  | ,---.  ,---.  ,---.  ,---. ,--,--,--.
|  .-.  \|  || .-. |(  .-' (  .-' | .-. ||        |
|  '--' /|  |' '-' '.-'  `).-'  `)' '-' '|  |  |  |
`------' `--' `---' `----' `----'  `---' `--`--`--'
🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸
            """
        )
        prevPlayed = []
        score = 0
        if bank:
            tprint(f"Bank: {bank.upper()}.")
            bank = bank[0] + "".join(sorted(list(bank[1:])))
        else:
            match getResponseBy(
                "What's the bank? (Center letter first)",
                lambda b: sevenUniques(b) or b == "quit",
                "Please enter seven unique letters, or \"quit\".",
            ).lower():
                case "quit":
                    return
                case bk:
                    bank = bk[0] + "".join(sorted(list(bk)[1:]))
            tprint("Okay, let's play!")
        dictionary = loadDict(bank)
        specialLetter = bank[1]
        for i in range(12):
            if i > 0:
                specialLetter = advanceSL(bank, specialLetter, prevPlayed[-1])
            tprint(f"---\nRound {i+1}. Special letter: {specialLetter.upper()}.\n")
            ouch = False
            while True:
                word = blossomBetter(bank, dictionary, prevPlayed, i, specialLetter, score)
                prevPlayed.append(word)
                tprint(
                    f"{'Okay, then instead ' if ouch else ''}I play: {dispWord(word, dictionary)}{', a validated word!' if dictionary[word] else ''}"
                )
                if dictionary[word]:
                    break
                match getResponse("Is that valid? (yes/no)", ["yes", "no", "quit"]):
                    case "yes":
                        wordsToValidate.add(word)
                        break
                    case "no":
                        wordsToRemove.add(word)
                        ouch = True
                    case "quit":
                        return
            wordScore = scoreWord(bank, specialLetter, word)
            addWordScore(word, wordScore, specialLetter)
            score += wordScore
            tprint(
                f"{'Great! ' if not dictionary[word] else ''}We scored {wordScore} {'additional ' if i != 0 else ''}points{f', for a total of {score} points' if i != 0 else ''}."
            )
        tprint(
            f"\n🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸\n\nGame over! We scored {score} points."
        )
        addGameScore(bank, score)
        playAgain = getResponse("Play again? (yes/no)", ["yes", "no"]) == "yes"
        bank = None
    updateWordlist(wordsToValidate, wordsToRemove)
    updateScores()
    return
