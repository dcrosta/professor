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


### Set up your databases

Once Professor is installed and running, go to http://localhost:8080/ in
your browser, and click "New Database" in the upper-right corner. Enter the
hostname, database name, and optionally username and password (if you are
using database authentication), then click Submit.

This will take you to the main page for your database, but it won't yet have
any information to display. You must *update* Professor from time to time,
by clicking the "update now" link, or using the command-line tool
(preferred).


### Updating profiling data

The best way to update the profiling data is to ask the `profess` script to
periodically query for new profiling information from the target databases:

    profess -s 5 update localhost/example localhost/test

will update the "example" and "test" databases running on localhost every 5
seconds.


## How Professor Works

Professor is designed to have minimal impact on running systems. It connects
to target databases each time an update is issued (through the web or
command line), queries only for new data in `system.profile` since the last
update, and replicates that data to its own database for use from within the
Professor webapp. In instances where you do not wish to impact your running
databases any more than is absolutely necessary (i.e. production databases),
Professor should be configured to use its own instance of MongoDB running on
separate hardware.

While querying for profile information, Professor annotates the profile
entries with a few useful pieces of additional information:

* A query "skeleton," which is a string representation of the structure of
the query; that is, it shows which keys were present, but no values set for
those keys. This enables Professor to group queries with the same structure
together for reporting.
* A sort "skeleton," if the query included a `sort()`.

The skeleton is a simple transformation of a BSON document into a string as
follows:

* For (embedded) documents, order the keys and recurse; emit keys separated
by commas and surrounded by `{` and `}`; when recursion returns a
sub-skeleton, separate the key and value with a colon
* For arrays, iterate in order and recurse; emit recursed contents separated
by commans and surrounded by `[` and `]`
* For everything else, emit nothing

Thus a query such as:

    {username: "dcrosta", city: "New York", zip: {$in: [10010, 10011]}}

Has as its skeleton:

    "{city,username,zip:{$in:[]}}"

Note that, although the order of keys is not preserved, it is predictable
(since the keys of documents are sorted alphabetically).


## Professor at the command line

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

