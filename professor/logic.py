# Copyright (c) 2011, Daniel Crosta
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

__all__ = ('update', 'parse', 'aggregate')

from datetime import datetime
from pymongo import ASCENDING, DESCENDING

from professor import app, db
from professor.skeleton import skeleton, sanitize
from professor.util import *

PARSERS = {}
def parser(optype):
    def inner(func):
        PARSERS[optype] = func
        return func
    return inner

GROUPERS = {}
def grouper(optype):
    def inner(func):
        GROUPERS[optype] = func
        return func
    return inner

SUMMARIZERS = {}
def summarizer(optype):
    def inner(func):
        SUMMARIZERS[optype] = func
        return func
    return inner

@parser('query')
def parse_query(entry):
    # {'responseLength': 20,
    #  'millis': 40,
    #  'ts': datetime.datetime(2011, 9, 19, 15, 8, 1, 976000),
    #  'scanAndOrder': True,
    #  'client': '127.0.0.1',
    #  'user': '',
    #  'query': {'$orderby': {'date': 1},
    #            '$query': {'processing.status': 'new'}},
    #  'ns': 'www.formcapture',
    #  'nscanned': 12133,
    #  'op': 'query'}

    query = entry.get('query', {}).get('$query', None)
    if query is None:
        query = entry.get('query', {})

    orderby = entry.get('query', {}).get('$orderby', None)
    if orderby is None:
        orderby = {}

    entry['skel'] = skeleton(query)
    entry['sort'] = skeleton(orderby)
    return True

def parse(database, entry):
    collection = entry['ns']
    collection = collection[len(database['dbname']) + 1:]
    entry['collection'] = collection

    # skip certain namespaces
    if collection.startswith('system.') or \
       collection.startswith('tmp.mr.'):
        return False

    optype = entry.get('op')
    subparser = PARSERS.get(optype)
    if subparser:
        if not subparser(entry):
            return False

    entry = sanitize(entry)
    entry['database'] = database['_id']

    db.profiles.save(entry)
    return True

def update(database):
    now = datetime.utcnow()
    query = {'ts': {'$lt': now}}
    if database['timestamp']:
        query['ts']['$gte'] = database['timestamp']

    query['op'] = {'$in': PARSERS.keys()}

    conndb = connect_to(database)
    i = 0
    for entry in conndb.system.profile.find(query):
        if parse(database, entry):
            i += 1

    database['timestamp'] = now
    db.databases.save(database)

    return i

@grouper('query')
def group_by_skel(last_entry, entry):
    return last_entry.get('skel') is not None and \
           last_entry.get('skel') == entry.get('skel')

@summarizer('query')
def summarize_timings(entries):
    times = [e['millis'] for e in entries]
    info = {
        'total': sum(times),
        'min': min(times),
        'max': max(times),
        'avg': avg(times),
        'median': median(times),
        'stddev': stddev(times),
        'histogram': loghistogram(times),
    }
    out = entries[0]
    out['count'] = len(times)
    out['times'] = info
    return out

def aggregate(database, optype, collection=None):

    query = {'database': database['_id'], 'op': optype}
    if collection is not None:
        query['collection'] = collection

    entries = db.profiles.find(query).sort([
        ('collection', ASCENDING),
        ('op', ASCENDING),
        ('skel', ASCENDING),
    ])

    last_entry = None
    group = []
    for entry in entries:
        if last_entry is None:
            last_entry = entry
        if not GROUPERS[optype](last_entry, entry):
            if group:
                yield SUMMARIZERS[optype](group)
            group = []
        group.append(entry)
        last_entry = entry

    if group:
        yield SUMMARIZERS[optype](group)

