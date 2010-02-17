# autocode.py
#
# Author(s): Christophe de Vienne <cdevienne@gmail.com>
#            Paul Johnson
#
# Based on autocode.py by Paul Johnson
# (http://www.sqlalchemy.org/trac/wiki/UsageRecipes/AutoCode)
#
# Improvements over the original autocode.py:
#   * Takes arguments on the command line to select the dburl and
#   the output destination
#   * Replace a bunch of database specific types by generic ones.
#   This is incomplete as it feats only my needs for a mysql to mssql
#   database conversion.
#   * Output the indexes and ForeignKeyConstraints (including multi-columns
#   ones) correctly
#
# The resulting script is directly usable (ie import and create/use the tables)
# with my testing database (a legacy mysql db with about 140+ tables, 140+
# foreign keys, 170+ indexes), after applying patches
# http://www.sqlalchemy.org/trac/ticket/662 and
# http://www.sqlalchemy.org/trac/ticket/663 on a 0.3.9 release.
#

from sqlalchemy import *
from sqlalchemy.databases import information_schema
import string
import sys

from optparse import OptionParser

parser = OptionParser("usage: %prog [options] dburl")
parser.add_option('--output', '-o', action='store', dest='output',
    metavar='FILE', default='stdout',
    help='Write the result into FILE (default "stdout")')

(options, args) = parser.parse_args()

if len(args) != 1:
    parser.error('Wrong number or arguments')

dburl = engine.url.make_url(args[0])
db = create_engine(dburl)
metadata = BoundMetaData(db)

if options.output == 'stdout':
    output = sys.stdout
else:
    output = open(options.output, 'w')

def textclause_repr(self):
    return 'text(%s)' % repr(self.text)

def table_repr(self):
    return "Table(%s)" % ",\n    ".join(
            [repr(self.name)] + [repr(self.metadata)] +
            [repr(x) for x in self.columns] +
            [repr(x) for x in self.constraints
                if not isinstance(x, PrimaryKeyConstraint)]
            )

def column_repr(self):
    kwarg = []
    if self.key != self.name:
        kwarg.append('key')
    if self._primary_key:
        kwarg.append('primary_key')
    if not self.nullable:
        kwarg.append('nullable')
    if self.onupdate:
        kwarg.append('onupdate')
    if self.default: 
        kwarg.append('default')
    return "Column(%s)" % ', '.join(
            [repr(self.name)] + [repr(self.type)] +
            [repr(x) for x in self.constraints] +
            ["%s=%s" % (k, repr(getattr(self, k))) for k in kwarg]
            )

def foreignkeyconstraint_repr(self):
    return "ForeignKeyConstraint(%s)" % ', '.join(
            [
            repr([x.parent.name for x in self.elements]),
            repr([x._get_colspec() for x in self.elements]),
            'name=' + repr(self.name)
            ]
        )

def repr_index(index, tvarname):
    return "Index(%s)" % ", ".join(
        [repr(index.name)] +
        ["%s.c.%s" % (tvarname, c.name) for c in index.columns] +
        ['unique=' + repr(index.unique)])
        
    
sql._TextClause.__repr__ = textclause_repr
schema.Table.__repr__ = table_repr
schema.Column.__repr__ = column_repr
schema.ForeignKeyConstraint.__repr__ = foreignkeyconstraint_repr

sql = select([information_schema.tables.c.table_name,
              information_schema.tables.c.table_schema],
              information_schema.tables.c.table_schema==dburl.database)

output.write("""from sqlalchemy import *
metadata = MetaData()

""")

tname_list = []

for tname,schema in db.execute(sql):
    if schema != dburl.database:
        continue
    tname_list.append(tname)
    tbl = Table(tname, metadata, schema=schema, autoload=True)
    code = repr(tbl)
    code = code.replace('BoundMetaData()', 'metadata')
    code = code.replace('MSChar', 'CHAR')
    code = code.replace('MSSmallInteger(length=1)', 'Boolean()')
    code = code.replace('MSSmallInteger', 'SmallInteger')
    code = code.replace('MSDateTime', 'DateTime')
    code = code.replace('MSMediumText', 'TEXT')
    code = code.replace('MSDouble', 'Numeric')
    code = code.replace('MSMediumText', 'TEXT')
    code = code.replace('MSLongBlob', 'TEXT')
    code = code.replace('MSString', 'String')
    code = code.replace('MSDate', 'Date')
    code = code.replace('MSTime', 'DateTime')
    code = code.replace('MSInteger', 'Integer')
    code = code.replace('MSDecimal', 'Numeric')
    code = code.replace('MSEnum', 'Integer')
    caps = string.capitalize(tname)

    indexes = "\n".join(
        [repr_index(index, tname) for index in tbl.indexes])

    output.write( """
%s = %s

%s

""" % (tname, code, indexes))

# vim: expandtab tabstop=4 shiftwidth=4:
