"""
early testing. parser partially completed.

need to decide which rows are important

parsing cards.csv from the MTG repo. {provide link}
"""

from collections import defaultdict

import csv
import re
import sys

import pprint

sys.stdout.reconfigure(encoding='utf-8')


'''
keyword_records = [(card_uuid, kw.upper()) for kw in keywords]
'''

with open("cards.csv", mode="r", encoding="utf-8") as f:
    cards = []
    manas = []
    artists = []
    worked_on = []
    keywords = []

    # populate records
    reader = csv.DictReader(f)

    mana_any = 63
    mana_color_map = {
        'W': 0x01,
        'U': 0x02,
        'B': 0x04,
        'R': 0x08,
        'G': 0x10,
        'C': 0x20
    }

    for row in reader:

        cards.append((
            row['uuid'],
            row['name'],
            row['colorIdentity'],
            row['power'],
            row['toughness'],
            row['rarity'],
            row['producedMana'],
            str(row['isPromo']).lower() == 'true',
            row['setCode'],
            row['text']
        ))

        # for every artistID, remove trim the whitespace and split the string
        temp = [a.strip() for a in row['artistIds'].split(',') if a.strip()]
        for artist in temp:
            artists.append((artist, row['artist']))
            worked_on.append((row['uuid'], artist))

        # add keywords
        temp = [a.strip() for a in row['keywords'].split(',') if a.strip()]
        for keyword in temp:
            keywords.append((row['uuid'], keyword))

        mana_counts = defaultdict(int)
        temp = re.findall(r"\{([^}]+)\}", row['manaCost'])
        for mana in temp:
            if (mana.isdigit()):
                amount = int(symbol)
                if amount > 0: # {INTEGER}
                    mana_counts[mana_any] += amount
                else: # {CHAR}
                    mask = 0
                    for abbr in mana.upper():
                        if abbr in mana_color_map:
                            mask |= mana_color_map[abbr]
                    if mask == 0:
                        mask = mana_any

                    mana_counts[mask] += 1 # increment this mana cost
        for mask, amount in mana_counts.items(): # add all mana costs for this card
            manas.append((row['uuid'], mask, amount))

        pprint.pprint(row)
        print('----')

        print(f"UUID: {row['uuid']}")
        print(f"Title: {row['name']}")
        print(f"Artist: {row['artist']}")
        print(f"Color ID: {row['colorIdentity']}")
        print(f"Power: {row['power']}")
        print(f"Toughness: {row['toughness']}")
        print(f"Rarity: {row['rarity']}")
        print(f"Produced Mana: {row['producedMana']}")
        print(f"isPromo: {row['isPromo']}")
        print(f"Set Code: {row['setCode']}")
        print(f"Mana Cost: {row['manaCost']}")
        print(f"Keywords: {row['keywords']}")
        print(f"Text:\n{row['text']}")

        print('artistIDs')
        for artist in artists[:10]:
            print(";".join(str(val) for val in artists))

        break


    # use records to populate database
    q_insert__card = """
        INSERT INTO Card VALUES
            (   %s, %s, %s, %s, %s,
                (   SELECT pk_rarity
                    FROM Rarity
                    WHERE UPPER(rarity) = UPPER(%s)
                ),
                %s, %s, %s, %s, %s
            )
        ON CONFLICT (pk_card) DO UPDATE SET
            title = EXCLUDED.title,
            colorIdentity = EXCLUDED.colorIdentity,
            power = EXCLUDED.power,
            toughness = EXCLUDED.toughness,
            rarity = EXCLUDED.rarity,
            mana_production_type = EXCLUDED.mana_production_type,
            mana_production_amount = EXCLUDED.mana_production_amount,
            isPromo = EXCLUDED.isPromo,
            setCode = EXCLUDED.setCode,
            description = EXCLUDED.description
        ;
    """
    
    q_insert__artist = """
        INSERT INTO Artist VALUES
            (%s, %s)
        ON CONFLICT (pk_artist) DO UPDATE
        SET artist = EXCLUDED.artist
        WHERE artist LIKE '% & %'
    """

    q_insert__worked_on = """
        INSERT INTO Artist__Worked_On__Card VALUES
            (%s, %s)
        ON CONFLICT (card, artist) DO NOTHING
        ;
    """

    q_insert__mana_cost = """
        INSERT INTO Card_Mana_Cost (card, type) VALUES
            (%s, %s)
        ON CONFLICT (card, type) DO UPDATE SET
            amount = amount + 1
        ;
    """

    q_insert__keyword = """
        INSERT INTO Keyword VALUES
            (%s, %s)
        ON CONFLICT (card, word) DO NOTHING
        ;
    """

    with conn.cursor() as cur:
        if cards:
            cur.executemany(q_insert__card, cards)

        if artists:
            cur.executemany(q_insert__artist, artists)

        if worked_on:
            cur.executemany(q_insert__worked_on, worked_on)

        if manas:
            cur.executemany(q_insert__mana_cost, manas)

        if keywords:
            cur.executemany(q_insert__keyword, keywords)

    # commit
    conn.commit()
    #'''