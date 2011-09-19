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

__all__ = ('get_or_404', 'avg', 'stddev', 'median', 'loghistogram')

from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime
import pytz
import re

from flask import abort, request

from professor import app

def get_or_404(collection, **kwargs):
    if '_id' in kwargs:
        try:
            kwargs['_id'] = ObjectId(kwargs['_id'])
        except InvalidId:
            abort(404)
    obj = collection.find_one(kwargs)
    if obj is None:
        abort(404)
    return obj

def avg(values):
    return sum(map(float, values)) / len(values)

def stddev(values):
    mean = avg(values)
    return (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5

def median(values):
    return sorted(values)[len(values) / 2]

@app.template_filter('float')
def floatfmt(value):
    return re.sub('(0+)$', '0', ('%.2f' % value))

from professor.skeleton import desanitize as desanitize_query
@app.template_filter('desanitize')
def desanitize(value):
    def build_out(value):
        if isinstance(value, list):
            return '[%s]' % ', '.join(map(build_out, value))
        elif isinstance(value, dict):
            return '{%s}' % ', '.join(('%s: %s' % (k, build_out(v)) for k, v in value.iteritems()))
        else:
            if isinstance(value, unicode):
                try:
                    return "'%s'" % value
                except:
                    pass
            return repr(value)

    clean = desanitize_query(value)
    out = build_out(clean)
    return out

@app.template_filter('humansize')
def humansize(value):
    value = float(value)
    kb = 1024
    mb = 1024 * kb
    gb = 1024 * mb
    tb = 1024 * gb
    for threshold, label in ((tb, 'TB'), (gb, 'GB'), (mb, 'MB')):
        if value > threshold:
            return '%.2f %s' % (value / threshold, label)

    return '%.2f KB' % (value / kb)

@app.template_filter('strftime')
def strftime(value, fmt):
    if not isinstance(value, datetime):
        return value

    timezone = request.cookies.get('timezone', 'utc')
    timezone = pytz.timezone(timezone)
    if timezone == pytz.utc:
        return value

    value = value.replace(tzinfo=pytz.utc).astimezone(timezone)
    return value.strftime(fmt)


def loghistogram(values, base=2, buckets=8):
    # generate a histogram with logaritmic scale buckets
    # with default params, first bucket will be [0,1),
    # second will be [1,2), third will be [2,4), etc;
    # the last bucket will include up to infinity

    ranges = []
    last = -1
    for i in xrange(buckets):
        next = base ** i
        ranges.append((last + 1, next))
        last = next

    # make the last range include everything
    ranges[-1] = (ranges[-1][0], float('inf'))

    out = []
    for start, end in ranges:
        out.append(sum(1 for value in values if start <= value < end))

    return out

