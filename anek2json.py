import sqlite3
import os
import json
import pathlib


def dumpa(folder, db):
    os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(database=db)
    cursor = conn.cursor()
    for anek in cursor.execute('select id, content, from_group from aneks').fetchall():
        data = {
            "id" : anek[0],
            "text" : anek[1],
            "from_group": anek[2]
        }
        filename = f'{anek[2]}_{anek[0]}.json'.replace("/", "-").replace("\\", "-")
        fname = pathlib.Path(folder, filename)
        json.dump(data, open(fname, 'w'))

def dumpq(folder, db):
    os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(database=db)
    cursor = conn.cursor()
    for quote in cursor.execute('select id, quote, author from quotes').fetchall():
        data = {
            "id" : quote[0],
            "text" : quote[1],
            "author": quote[2]
        }
        filename = f'{quote[0]}.json'.replace("/", "-").replace("\\", "-")
        fname = pathlib.Path(folder, filename)
        json.dump(data, open(fname, 'w'))

dumpq('e:/botable/quotes', 'quotes.db')
dumpa('e:/botable/aneks',  'quotes.db')