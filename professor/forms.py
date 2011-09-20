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

__all__ = ('LoginForm', 'DatabaseForm', 'PreferencesForm')

from wtforms import *
from wtforms.validators import *

from professor import app, db

from pytz import common_timezones
timezones = [(x, x) for x in common_timezones]

class LoginForm(Form):
    username = TextField(validators=[Required()])
    password = PasswordField(validators=[Required()])

class DatabaseForm(Form):
    hostname = TextField(label='Host:Port', validators=[Required()])
    dbname = TextField(label='Database', validators=[Required()])
    username = TextField()
    password = PasswordField()

    def validate(self):
        if not super(DatabaseForm, self).validate():
            return False
        return db.databases.find_one({
            'hostname': self.hostname.data,
            'dbname': self.database.data}) is None

class PreferencesForm(Form):
    referrer = HiddenField()
    timezone = SelectField(choices=timezones, default='UTC')

