import re

input_path = "wordlist.txt"
output_path = "wordlist.txt"

ansi_pattern = re.compile(r'(\x1b\[[0-9;]*m)(.*?)(\x1b\[[0-9;]*m)([^\w]*)$')

def process_line(line):
    match = ansi_pattern.match(line.rstrip('\n'))
    if match:
        _, text, _, trailing = match.groups()
        return f"{text.lower()}{trailing}\n"
    else:
        # If no ANSI codes, just lowercase the word part
        parts = re.match(r'(\w+)([^\w]*)$', line.rstrip('\n'))
        if parts:
            word, trailing = parts.groups()
            return f"{word.lower()}{trailing}\n"
        return line

with open(input_path, "r") as infile:
    lines = infile.readlines()

with open(output_path, "w") as outfile:
    for line in lines:
        outfile.write(process_line(line))