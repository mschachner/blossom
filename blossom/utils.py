import sys
import time

STYLES = {
    "reset": "\033[0m",
    "boldred": "\033[1;31m",
    "boldgreen": "\033[1;32m",
    "boldyellow": "\033[1;33m",
}


def dispWord(word, dictionary):
    color = (
        "red" if word not in dictionary else "yellow" if not dictionary[word] else "green"
    )
    icon = (
        "❌ "
        if word not in dictionary
        else "🟡 "
        if not dictionary[word]
        else "🌸 "
        if len(set(word)) == 7
        else "✅ "
    )
    return icon + f"{STYLES['bold' + color]}{word.upper()}{STYLES['reset']}"


def _tprint(*objects, sep=" ", end="\n", file=sys.stdout, flush=False):
    text = sep.join(map(str, objects)) + end

    # If not an interactive terminal, print fast.
    if not getattr(file, "isatty", lambda: False)():
        file.write(text)
        if flush:
            file.flush()
        return

    # Tuned speeds
    cps = 150  # characters per second
    punct_pause = 0.10  # pause after . ! ?
    mid_pause = 0.10  # pause after , ; : – —
    base = 1.0 / cps

    for ch in text:
        file.write(ch)
        file.flush()
        if ch in ".!?":
            time.sleep(punct_pause)
        elif ch in ",;:–—":
            time.sleep(mid_pause)
        else:
            time.sleep(base)


def getResponseBy(msg, cond, invalidMsg):
    while True:
        attempt = input(msg + "\n > ")
        if cond(attempt):
            return attempt
        print(invalidMsg)


def getResponse(msg, valids):
    return getResponseBy(msg, lambda r: r in valids, f"Valid responses: {', '.join(valids)}.")


def sevenUniques(s):
    return len(s) == 7 and len(set(s)) == 7 and s.isalpha()

def condMsg(cond, msg):
    return msg if cond else ""

def plural(l):
    return condMsg(len(l) != 1, "s")