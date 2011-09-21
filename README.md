# Professor

Professor is a web application with corresponding command-line tool to read,
summarize, and interpret MongoDB profiler output (for MongoDB 2.0 and
later).


## Installing

Professor requires [MongoDB](http://www.mongodb.org/),
[Python](http://www.python.org/), [Flask](http://flask.pocoo.org/),
[WTForms](wtforms.simplecodes.com/), and
[PyTZ](http://pytz.sourceforge.net/). These can all be installed by running:

    python setup.py [install|develop]

This will install the required dependencies, as well as the `profess`
command-line script. You can then run Professor locally on port 8080 with:

    python server.py

If you want Professor to store its database in a MongoDB instance other than
on the default port on localhost, edit `professor.cfg` or create a new file
`private.cfg` and set the appropriate values in the `MONGODB_CONFIG`
variable.


## Set up your databases

Once Professor is installed and running, go to http://localhost:8080/ in
your browser, and click "New Database" in the upper-right corner. Enter the
hostname, database name, and optionally username and password (if you are
using database authentication), then click Submit.

This will take you to the main page for your database, but it won't yet have
any information to display. You must *update* Professor from time to time,
by clicking the "update now" link, or using the command-line tool
(preferred).


## Updating profiling data

The best way to update the profiling data is to ask the `profess` script to
periodically query for new profiling information from the target databases:

    profess -s 5 localhost/example localhost/test

will update the "example" and "test" databases running on localhost every 5
seconds.


## `profess`

The `profess` command line tool has a number of modes of operation:

* `list` will show you all the configured databsaes in your Professor
instance
* `update` will allow you to update Professor's cached copy of profiling
data for one or more databases
* `clean` will erase Professor's cached profiling data, but not reset the
timestamp (so that only new profiling data will be collected by `update`)
* `reset` will perform a `clean` and also reset the timestamp, so that the
next call to `update` will re-cache all existing profiling data
* `remove` will remove a database from your Professor instance

Full usage is available in the `profess` tool with `profess -h` or `profess
[command] -h` for any of the above commands.

## About

Professor is by [Dan Crosta](https://github.com/dcrosta). It is BSD-licensed,
and feedback and contributions are encouraged. I hope you find it useful!

