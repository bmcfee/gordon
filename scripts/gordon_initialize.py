#!/usr/bin/env python
"""Initializes Gordon database

Run this script to initialize all of the gordon database tables.  The
database configuration must be specified in config.py.
"""

import sqlalchemy

from gordon.db import model

nexceptions = 0
done = False
while not done:
    try: 
        model.metadata.create_all(model.engine)
        done = True
    except sqlalchemy.exceptions.ProgrammingError:
        nexceptions += 1

print ('Got %d ProgrammingErrors while trying to initialize the database'
       % nexceptions)
