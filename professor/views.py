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

from datetime import datetime, timedelta
import pymongo
from pymongo import ASCENDING, DESCENDING
import urllib

from flask import g
from flask import session
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.datastructures import MultiDict

from professor import app, db
from professor.util import *
from professor.forms import *
from professor.skeleton import *

@app.route('/db/new', methods=['GET'])
def new_database():
    form = DatabaseForm()
    return render_template(
        'simpleform.html',
        form=form,
    )

@app.route('/db/new', methods=['POST'])
def save_database():
    form = DatabaseForm(formdata=request.form)
    if form.validate():
        db.databases.save({
            'hostname': form.hostname.data,
            'dbname': form.database.data,
            'username': form.username.data,
            'password': form.password.data,
            'timestamp': None,
        })
        return redirect(url_for('database', hostname=form.hostname.data, dbname=form.database.data))

    return render_template(
        'simpleform.html',
        form=form,
    )

@app.route('/')
def index():
    databases = db.databases.find().sort([('hostname', ASCENDING), ('dbname', ASCENDING)])
    return render_template('index.html', databases=databases)

@app.route('/db/<hostname>')
def host(hostname):
    databases = db.databases.find({'hostname': hostname}).sort([('hostname', ASCENDING), ('dbname', ASCENDING)])
    return render_template('index.html', databases=databases, hostname=hostname)

def connect_to(database, should_raise=True):
    try:
        conn = pymongo.Connection(
            host=database['hostname'],
            port=27017,
            network_timeout=2,
        )
        conndb = conn[database['dbname']]
    except Exception, e:
        if should_raise:
            abort(500)
        else:
            return e

    return conndb

def connect_status(database):
    conndb = connect_to(database, should_raise=False)
    if conndb:
        connected = True
        profiling = conndb.command('profile', -1)
        level = profiling['was']
        if level == 0:
            status = 'connected, not profiling'
        elif level == 1:
            ms = profiling['slowms']
            status = 'connected, slowms: %d' % ms
        elif level == 2:
            status = 'connected, profiling, all ops'
    else:
        # conndb is an exception
        connected = False
        status = str(conndb)

    return conndb, connected, status

@app.route('/db/<hostname>/<dbname>/profile')
def profile(hostname, dbname):
    database = get_or_404(db.databases, hostname=hostname, dbname=dbname)

    now = datetime.utcnow()
    query = {'ts': {'$lt': now}}
    if database['timestamp']:
        query['ts']['$gte'] = database['timestamp']

    query['ns'] = {'$nin': ['%s.system.profile' % database['dbname'], '%s.system.indexes' % database['dbname']]}

    # TODO: support other things
    query['op'] = 'query'

    conndb = connect_to(database)
    profiles = conndb.system.profile.find(query)
    for entry in profiles:
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
        collection = entry['ns']
        collection = collection[len(database['dbname']) + 1:]

        profile = sanitize(entry)
        profile['skel'] = skeleton(query)
        profile['database'] = database['_id']
        profile['collection'] = collection
        db.profiles.insert(profile)

    database['timestamp'] = now
    db.databases.save(database)

    if request.referrer:
        return redirect(request.referrer)
    return redirect(url_for('database', hostname=database['hostname'], dbname=database['dbname']))

@app.route('/db/<hostname>/<dbname>')
def database(hostname, dbname):
    database = get_or_404(db.databases, hostname=hostname, dbname=dbname)

    count = db.profiles.find({'database': database['_id']}).count()

    allqueries = db.profiles.find({'database': database['_id'], 'op': 'query'})
    allqueries.sort([
        ('collection', ASCENDING),
        ('skel', ASCENDING),
    ])

    queries = []
    query = {}
    for entry in allqueries:
        skel = entry['skel']
        collection = entry['collection']

        if skel != query.get('skel') or collection != query.get('collection'):
            query = {'skel': skel, 'collection': collection, 'times': []}
            queries.append(query)
        query['times'].append(entry['millis'])

    for query in queries:
        times = query['times']
        info = {
            'total': sum(times),
            'min': min(times),
            'max': max(times),
            'avg': avg(times),
            'median': median(times),
            'stddev': stddev(times),
            'histogram': loghistogram(times),
        }
        query['count'] = len(times)
        query['times'] = info

    queries.sort(key=lambda x: x['times']['avg'], reverse=True)

    conndb, connected, status = connect_status(database)

    return render_template(
        'database.html',
        database=database,
        connected=connected,
        status=status,
        count=count,
        queries=queries,
    )

@app.route('/db/<hostname>/<dbname>/<collection>')
def collection(hostname, dbname, collection):
    database = get_or_404(db.databases, hostname=hostname, dbname=dbname)

    count = db.profiles.find({'database': database['_id']}).count()

    allqueries = db.profiles.find({'database': database['_id'], 'collection': collection, 'op': 'query'})
    allqueries.sort([
        ('skel', ASCENDING),
    ])

    queries = []
    query = {}
    for entry in allqueries:
        skel = entry['skel']

        if skel != query.get('skel'):
            query = {'skel': skel, 'collection': collection, 'times': []}
            queries.append(query)
        query['times'].append(entry['millis'])

    for query in queries:
        times = query['times']
        info = {
            'total': sum(times),
            'min': min(times),
            'max': max(times),
            'avg': avg(times),
            'median': median(times),
            'stddev': stddev(times),
            'histogram': loghistogram(times),
        }
        query['count'] = len(times)
        query['times'] = info

    queries.sort(key=lambda x: x['times']['avg'], reverse=True)

    conndb, connected, status = connect_status(database)

    collstats = conndb.command("collstats", collection)
    indexes = []
    for name, info in  conndb[collection].index_information().iteritems():
        info['name'] = name
        indexes.append(info)
    indexes.sort(key=lambda x: x['name'])

    return render_template(
        'database.html',
        database=database,
        collection=collection,
        collstats=collstats,
        indexes=indexes,
        connected=connected,
        status=status,
        count=count,
        queries=queries,
    )

@app.route('/db/<hostname>/<dbname>/<collection>/<skel>')
def query(hostname, dbname, collection, skel):
    database = get_or_404(db.databases, hostname=hostname, dbname=dbname)

    count = db.profiles.find({'database': database['_id']}).count()

    queries = db.profiles.find({'database': database['_id'], 'collection': collection, 'skel': skel, 'op': 'query'})
    queries.sort([
        ('ts', DESCENDING),
    ])

    conndb, connected, status = connect_status(database)

    collstats = conndb.command("collstats", collection)
    indexes = []
    for name, info in  conndb[collection].index_information().iteritems():
        info['name'] = name
        indexes.append(info)
    indexes.sort(key=lambda x: x['name'])

    return render_template(
        'queries.html',
        skel=skel,
        count=count,
        database=database,
        collection=collection,
        queries=queries,
        connected=connected,
        status=status,
        collstats=collstats,
        indexes=indexes,
    )

class Preferences(object):
    def __getattr__(self, name):
        if name == 'referrer':
            return request.referrer
        elif name in request.cookies:
            return request.cookies[name]
        else:
            raise AttributeError(name)

@app.route('/preferences', methods=['GET'])
def preferences():
    form = PreferencesForm(obj=Preferences())
    return render_template('preferences.html', form=form)

@app.route('/preferences', methods=['POST'])
def setpreferences():
    form = PreferencesForm(request.form, obj=Preferences())
    if form.validate():
        lifetime = timedelta(days=365 * 20)
        if form.referrer.data:
            response = redirect(urllib.unquote(form.referrer.data))
        else:
            response = redirect(url_for('index'))
        for field in form:
            if field.name == 'referrer':
                continue
            response.set_cookie(
                field.name,
                field.data,
                max_age=lifetime.seconds + lifetime.days * 24 * 3600,
                expires=datetime.utcnow() + lifetime,
            )
        return response
    return render_template('preferences.html', form=form)

@app.errorhandler(404)
@app.errorhandler(500)
def not_found(error):
    return render_template(str(error.code) + '.html')

