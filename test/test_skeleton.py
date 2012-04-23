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

from bson.binary import Binary
from bson.code import Code
from bson.dbref import DBRef
from bson.errors import InvalidDocument
from bson.objectid import ObjectId
from bson.son import SON
from datetime import datetime
import re
import unittest

from professor import skeleton as s

class SkeletonTest(unittest.TestCase):

    def test_skeleton_simple(self):
        self.assertEqual(s.skeleton({'hello': 'world'}), '{hello}')
        self.assertEqual(s.skeleton({'hello': 'world', 'foo': 'bar'}), '{foo,hello}')
        self.assertEqual(s.skeleton({}), '{}')

    def test_skeleton_list(self):
        self.assertEqual(s.skeleton({'a': []}), '{a:[]}')
        self.assertEqual(s.skeleton({'a': [1,2,3]}), '{a:[]}')
        self.assertEqual(s.skeleton({'a': [{'b': 1}, {'b': 2}]}), '{a:[{b},{b}]}')
        self.assertEqual(s.skeleton({'a': [{'b': 1}, {'c': 2}]}), '{a:[{b},{c}]}')

        # TODO: this is weird, what should this do?
        self.assertEqual(s.skeleton({'a': [{'b': 1}, 2]}), '{a:[{b}]}')

    def test_skeleton_embedded_objects(self):
        self.assertEqual(s.skeleton({'a': {'b': 1}}), '{a:{b}}')
        self.assertEqual(s.skeleton({'a': {'b': 1}, 'c': 1}), '{a:{b},c}')
        self.assertEqual(s.skeleton({'a': {'b': 1, 'd': 2}, 'c': 1}), '{a:{b,d},c}')

        # make sure top-level SON objects work
        self.assertEqual(s.skeleton(SON([('a', 1)])), '{a}')

        # and embedded SON objects
        self.assertEqual(s.skeleton({'a': SON([('b', 1)])}), '{a:{b}}')
        self.assertEqual(s.skeleton({'a': SON([('b', 1)]), 'c': 1}), '{a:{b},c}')
        self.assertEqual(s.skeleton({'a': SON([('b', 1), ('d', 2)]), 'c': 1}), '{a:{b,d},c}')

    def test_skeleton_types(self):
        # ensure that all valid BSON types can be
        # skeleton'd; lists and subobjects are
        # tested in other functions and omitted here
        self.assertEqual(s.skeleton({'a': 1}), '{a}')
        self.assertEqual(s.skeleton({'a': 1L}), '{a}')
        self.assertEqual(s.skeleton({'a': 1.0}), '{a}')
        self.assertEqual(s.skeleton({'a': '1'}), '{a}')
        self.assertEqual(s.skeleton({'a': u'1'}), '{a}')
        self.assertEqual(s.skeleton({'a': True}), '{a}')
        self.assertEqual(s.skeleton({'a': datetime.now()}), '{a}')
        self.assertEqual(s.skeleton({'a': ObjectId('000000000000000000000000')}), '{a}')
        self.assertEqual(s.skeleton({'a': re.compile(r'^$')}), '{a}')
        self.assertEqual(s.skeleton({'a': Code('function(){}')}), '{a}')
        self.assertEqual(s.skeleton({'a': None}), '{a}')
        self.assertEqual(s.skeleton({'a': Binary('123456')}), '{a}')
        self.assertEqual(s.skeleton({'a': DBRef('coll', 123)}), '{a}')

    def test_error_message(self):
        class NonBsonType(object):
            def __init__(self, value):
                self.value = value
            def __repr__(self):
                return 'NonBsonType(%r)' % self.value

        self.assertRaises(InvalidDocument, s.skeleton, ({'a': NonBsonType(1)}, ))
        try:
            s.skeleton({'a': NonBsonType(1)})
        except InvalidDocument as e:
            msg = e.args[0]
            self.assertTrue(re.match(r'unknown BSON type <.*NonBsonType.*>', msg))

class SanitizerTest(unittest.TestCase):

    def test_sanitize(self):
        self.assertEqual(s.sanitize({'a': 'b'}), {'a': 'b'})
        self.assertEqual(s.sanitize({'a': [1, 2]}), {'a': [1, 2]})
        self.assertEqual(s.sanitize({'a.b': 'c'}), {'a_,_b': 'c'})
        self.assertEqual(s.sanitize({'a': {'b': 'c'}}), {'a': {'b': 'c'}})
        self.assertEqual(s.sanitize({'a': {'b.c': 'd'}}), {'a': {'b_,_c': 'd'}})

        self.assertEqual(s.sanitize({'a.$.b': 'c'}), {'a_,__$__,_b': 'c'})

    def test_desanitize(self):
        self.assertEqual(s.desanitize({'a': 'b'}), {'a': 'b'})
        self.assertEqual(s.desanitize({'a': [1, 2]}), {'a': [1, 2]})
        self.assertEqual(s.desanitize({'a_,_b': 'c'}), {'a.b': 'c'})
        self.assertEqual(s.desanitize({'a': {'b': 'c'}}), {'a': {'b': 'c'}})
        self.assertEqual(s.desanitize({'a': {'b_,_c': 'd'}}), {'a': {'b.c': 'd'}})

        self.assertEqual(s.desanitize({'a_,__$__,_b': 'c'}), {'a.$.b': 'c'})

    def test_error_message(self):
        class NonBsonType(object):
            def __init__(self, value):
                self.value = value
            def __repr__(self):
                return 'NonBsonType(%r)' % self.value

        self.assertRaises(InvalidDocument, s.sanitize, ({'a': NonBsonType(1)}, ))
        try:
            s.skeleton({'a': NonBsonType(1)})
        except InvalidDocument as e:
            msg = e.args[0]
            self.assertTrue(re.match(r'unknown BSON type <.*NonBsonType.*>', msg))

        self.assertRaises(InvalidDocument, s.desanitize, ({'a': NonBsonType(1)}, ))
        try:
            s.skeleton({'a': NonBsonType(1)})
        except InvalidDocument as e:
            msg = e.args[0]
            self.assertTrue(re.match(r'unknown BSON type <.*NonBsonType.*>', msg))

