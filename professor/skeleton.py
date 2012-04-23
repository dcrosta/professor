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

__all__ = ('skeleton', 'sanitize')

from bson.objectid import ObjectId
from bson.code import Code
from datetime import datetime
import re

BSON_TYPES = set([
    int,
    long,
    str,
    unicode,
    bool,
    float,
    datetime,
    ObjectId,
    type(re.compile('')),
    Code,
    type(None),
])



def skeleton(query_part):
    """
    >>> skeleton({u'acronym': u'AMSHAT'})
    u'{acronym}'
    >>> skeleton({u'_id': 1, u'locked': False})
    u'{_id,locked}'
    >>> skeleton({})
    u'{}'
    >>> skeleton({u'op': u'query'})
    u'{op}'
    >>> skeleton({u'op': None})
    u'{op}'
    """
    t = type(query_part)
    if t == list:
        out = []
        for element in query_part:
            sub = skeleton(element)
            if sub is not None:
                out.append(sub)
        return u'[%s]' % ','.join(out)
    elif t == dict:
        out = []
        for key in sorted(query_part.keys()):
            sub = skeleton(query_part[key])
            if sub is not None:
                out.append('%s:%s' % (key, sub))
            else:
                out.append(key)
        return u'{%s}' % ','.join(out)
    elif t not in BSON_TYPES:
        raise Exception(query_part)

def sanitize(value):
    # return a copy of the query with all
    # occurrences of "$" replaced by "_$_",
    # and ocurrences of "." replaced by
    # "_,_" in keys
    t = type(value)
    if t == list:
        return map(sanitize, value)
    elif t == dict:
        return dict((k.replace('$', '_$_').replace('.', '_,_'), sanitize(v))
                    for k, v in value.iteritems())
    elif t not in BSON_TYPES:
        raise Exception(value)
    else:
        return value

def desanitize(value):
    # perform the inverse of sanitize()
    t = type(value)
    if t == list:
        return map(desanitize, value)
    elif t == dict:
        return dict((k.replace('_$_', '$').replace('_,_', '.'), desanitize(v))
                    for k, v in value.iteritems())
    elif t not in BSON_TYPES:
        raise Exception(value)
    else:
        return value

