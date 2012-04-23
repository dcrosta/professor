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

__all__ = ('skeleton', 'sanitize')

from bson.binary import Binary
from bson.code import Code
from bson.dbref import DBRef
from bson.errors import InvalidDocument
from bson.objectid import ObjectId
from bson.son import SON
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
    Binary,
    DBRef,
    SON,
])


def skeleton(query_part):
    """
    Generate a "skeleton" of a document (or embedded document). A
    skeleton is a (unicode) string indicating the keys present in
    a document, but not the values, and is used to group queries
    together which have identical key patterns regardless of the
    particular values used. Keys in the skeleton are always sorted
    lexicographically.

    Raises :class:`~bson.errors.InvalidDocument` when the document
    cannot be converted into a skeleton (this usually indicates that
    the type of a key or value in the document is not known to
    Professor).

    For example:

        >>> skeleton({'hello': 'World'})
        u'{hello}'
        >>> skeleton({'title': 'My Blog Post', 'author': 'Dan Crosta'})
        u'{author,title}
        >>> skeleton({})
        u'{}'
    """
    t = type(query_part)
    if t == list:
        out = []
        for element in query_part:
            sub = skeleton(element)
            if sub is not None:
                out.append(sub)
        return u'[%s]' % ','.join(out)
    elif t in (dict, SON):
        out = []
        for key in sorted(query_part.keys()):
            sub = skeleton(query_part[key])
            if sub is not None:
                out.append('%s:%s' % (key, sub))
            else:
                out.append(key)
        return u'{%s}' % ','.join(out)
    elif t not in BSON_TYPES:
        raise InvalidDocument('unknown BSON type %r' % t)

def sanitize(value):
    """"Sanitize" a value (e.g. a document) for safe storage
    in MongoDB. Converts periods (``.``) and dollar signs
    (``$``) in key names to escaped versions. See
    :func:`~professor.skeleton.desanitize` for the inverse.
    """
    t = type(value)
    if t == list:
        return map(sanitize, value)
    elif t == dict:
        return dict((k.replace('$', '_$_').replace('.', '_,_'), sanitize(v))
                    for k, v in value.iteritems())
    elif t not in BSON_TYPES:
        raise InvalidDocument('unknown BSON type %r' % t)
    else:
        return value

def desanitize(value):
    """Does the inverse of :func:`~professor.skeleton.sanitize`.
    """
    t = type(value)
    if t == list:
        return map(desanitize, value)
    elif t == dict:
        return dict((k.replace('_$_', '$').replace('_,_', '.'), desanitize(v))
                    for k, v in value.iteritems())
    elif t not in BSON_TYPES:
        raise InvalidDocument('unknown BSON type %r' % t)
    else:
        return value

