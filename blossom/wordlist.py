import subprocess
from datetime import datetime

from .utils import condMsg, dispWord, getResponse, plural


def loadDict(bank=None):
    dictionary = {}
    with open("wordlist.txt") as infile:
        for line in infile:
            word = line[0:-2]
            if not bank or (
                any(c == bank[0] for c in word) and all(c in bank for c in word)
            ):
                dictionary[word] = line.endswith('!\n')
    return dictionary


def updateWordlist(wordsToValidate, wordsToRemove):
    if wordsToValidate and getResponse(
        f"Ok to validate: {', '.join(wordsToValidate)}? (yes/no)", ["yes", "no"]
    ) == "no":
        wordsToValidate = set()
    if wordsToRemove and getResponse(
        f"Ok to remove: {', '.join(wordsToRemove)}? (yes/no)", ["yes", "no"]
    ) == "no":
        wordsToRemove = set()

    if not wordsToRemove and not wordsToValidate:
        print("No changes to wordlist.")
        return

    dictionary = loadDict()
    newLines = list(
        word + ("!\n" if dictionary[word] or word in wordsToValidate else ".\n")
        for word in dictionary
        if word not in wordsToRemove
    )
    newLines.extend(
        word + "!\n" for word in wordsToValidate if word not in dictionary
    )
    newLines.sort(key=lambda l: l.rstrip("!.\n"))

    with open("wordlist.txt", "w") as outfile:
        outfile.writelines(newLines)

    subprocess.run(
        ["git", "add", "wordlist.txt"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msgs = [
        condMsg(wordsToValidate, f"validated {len(wordsToValidate)} word{plural(wordsToValidate)} at {timestamp}"),
        condMsg(wordsToRemove,   f"removed   {len(wordsToRemove)}   word{plural(wordsToRemove)}   at {timestamp}"),
        condMsg(wordsToValidate and wordsToRemove, "and")
    ]
    summary = "auto: updated wordlist.txt: " + " ".join(m for m in msgs if m)

    body =  condMsg(wordsToValidate, "Validated words:\n" + "\n".join(wordsToValidate) + "\n\n")
    body += condMsg(wordsToRemove,   "Removed words:\n"   + "\n".join(wordsToRemove)   + "\n\n")
    
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
    print("Done.")
    return


def searchWords(queries=None):
    if not queries:
        response = input("Enter words to search (comma or space separated):\n > ")
        queries = [w.strip() for w in response.replace(',', ' ').split() if w.strip()]
    queries = set(queries)
    dictionary = loadDict()
    padding = 5 + max(len(dispWord(word, dictionary)) for word in queries)

    print("Search results:")
    for word in queries:
        dword = dispWord(word, dictionary)
        msg = (
            ": Not found"
            if word not in dictionary
            else ": Validated"
            if dictionary[word]
            else ": Present, not validated"
        )
        print(dword + (padding - len(dword)) * " " + msg)

    if any(word not in dictionary or not dictionary[word] for word in queries) and getResponse(
        "Add/validate all words? (yes/no)", ["yes", "no"]
    ) == "yes":
        updateWordlist(queries, set())
    return
