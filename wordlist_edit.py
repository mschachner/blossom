from blossom.wordlist import loadDict, updateWordlist
from blossom.game import scoreWord

def maxPossibleScore(word):
    return max(scoreWord(word, letter, word) for letter in word)

def filterWeakWords():
    dictionary = loadDict()
    wordsToRemove = []
    for word in dictionary:
        if maxPossibleScore(word) < 15:
            wordsToRemove.append(word)
    updateWordlist([], wordsToRemove)

filterWeakWords()