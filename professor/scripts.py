# Copyright (c) 2011-2012, Daniel Crosta
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import argparse
from pymongo import ASCENDING, DESCENDING
import re
import time

from professor import db
from professor.logic import *

db_name = re.compile('(\S+)/(\S+)')

def do_list(parser, args):
    print 'Known Databases:'
    for d in db.databases.find().sort([('hostname', ASCENDING), ('dbname', ASCENDING)]):
        print "   %s/%s" % (d['hostname'], d['dbname'])

def get_database(parser, args):
    if not hasattr(args, 'databases'):
        args.databases = {}
    if args.database in args.databases:
        return args.databases[args.database]

    m = db_name.match(args.database)
    if not m:
        parser.error('"%s" is not a valid database' % args.database)

    hostname, dbname = m.groups()
    database = db.databases.find_one({'hostname': hostname, 'dbname': dbname})
    if not database:
        parser.error('"%s" is not a known database' % args.database)

    if args.database not in args.databases:
        args.databases[args.database] = database

    return database

def do_update(parser, args):
    database = get_database(parser, args)
    count = update(database)
    print "%s: updated %d entries" % (args.database, count)

def do_reset(parser, args):
    database = get_database(parser, args)
    db.profiles.remove({'database': database['_id']})
    db.databases.update({'_id': database['_id']}, {'$set': {'timestamp': None}})
    print "reset %s" % args.database

def do_clean(parser, args):
    database = get_database(parser, args)
    db.profiles.remove({'database': database['_id']})
    print "cleaned %s" % args.database

def do_remove(parser, args):
    database = get_database(parser, args)
    db.databases.remove({'_id': database['_id']})
    db.profiles.remove({'database': database['_id']})
    print "removed %s" % args.database



def profess():
    parser = argparse.ArgumentParser(description='Painless MongoDB Profiling')
    parser.add_argument('-s', '--seconds', dest='interval', metavar='N', type=int,
                        help='Repeat this command every N seconds', default=None)

    commands = parser.add_subparsers()

    list = commands.add_parser('list', help='List databases known to professor')
    list.set_defaults(cmd=do_list)

    reset = commands.add_parser('reset', help='Erase profiling information and reset last sync timestamp')
    reset.set_defaults(cmd=do_reset)
    reset.add_argument('database', help='Database to clean', nargs='+')

    update = commands.add_parser('update', help="Update a database's profiling information")
    update.set_defaults(cmd=do_update)
    update.add_argument('database', help='Database to update', nargs='+')

    clean = commands.add_parser('clean', help='Delete existing profiling information for database')
    clean.set_defaults(cmd=do_clean)
    clean.add_argument('database', help='Database to clean', nargs='+')

    remove = commands.add_parser('remove', help='Completely remove a database from professor')
    remove.set_defaults(cmd=do_remove)
    remove.add_argument('database', help='Database to remove', nargs='+')


    parser.set_defaults(databases={})
    parser.set_defaults(database=[])
    args = parser.parse_args()

    dbs = args.database
    def run_commands():
        if dbs:
            for database in dbs:
                args.database = database
                args.cmd(parser, args)
        else:
            args.cmd(parser, args)

    run_commands()
    while args.interval is not None:
        time.sleep(args.interval)
        run_commands()

if __name__ == '__main__':
    profess()

