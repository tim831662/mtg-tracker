"""
early testing. parser partially completed.

need to decide which rows are important

parsing cards.csv from the MTG repo. {provide link}
"""

import csv

with open("cards.csv", mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(f"Name: {row['name']}")
        print(f"Mana Cost: {row['manaCost']}")
        print(f"Artist: {row['artist']}")
        print(f"Color ID: {row['colorIdentity']}")
        print(f"Text:\n{row['text']}")

        break  # Just looking at the first card