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

__all__ = ('SessionMixin', 'MongoSessionStore')

from datetime import datetime, timedelta

from werkzeug.contrib.sessions import SessionStore

class SessionMixin(object):
    __slots__ = ('session_store',)

    @property
    def session_key(self):
        return self.config.get('SESSION_COOKIE_NAME', '_plog_session')

    def open_session(self, request):
        sid = request.cookies.get(self.session_key, None)
        if sid is not None:
            return self.session_store.get(sid)
        return self.session_store.new()

    def save_session(self, session, response):
        if session.should_save:
            self.session_store.save(session)

            lifetime = self.config.get('PERMANENT_SESSION_LIFETIME', timedelta(minutes=30))
            response.set_cookie(
                self.session_key,
                session.sid,
                max_age=lifetime.seconds + lifetime.days * 24 * 3600,
                expires= datetime.utcnow() + lifetime,
                secure=self.config.get('SESSION_COOKIE_SECURE', False),
                httponly=self.config.get('SESSION_COOKIE_HTTPONLY', False),
                domain=self.config.get('SESSION_COOKIE_DOMAIN', None),
                path=self.config.get('SESSION_COOKIE_PATH', '/'),
            )
        return response

    def end_session(self, session):
        self.session_store.delete(session)

class MongoSessionStore(SessionStore):
    """Subclass of :class:`werkzeug.contrib.sessions.SessionStore`
    which stores sessions using MongoDB documents.
    """

    def __init__(self, collection):
        super(MongoSessionStore, self).__init__()
        self.collection = collection

    def save(self, session):
        self.collection.save({'_id': session.sid, 'data': dict(session)}, safe=True)

    def delete(self, session):
        self.collection.remove({'_id': session.sid}, safe=True)

    def get(self, sid):
        doc = self.collection.find_one({'_id': sid})
        if doc:
            return self.session_class(dict(doc['data']), sid, False)
        else:
            return self.session_class({}, sid, True)

