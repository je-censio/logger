Overview
========

Stores all information in a Riak database, assumed to be at localhost.
In the real world we'd probably store the log information in something 
more appropriate (such as HDFS) because it's a little overkill for
each entry to have its own row but I erred on the side of simplicity
and opted not to create a sprawling mess for now.
I also wanted to try out Riak's CRDT counters, which make counting
events per user/device/url very simple.

The frontend is Flask (again for simplicity), although the database
stuff should all be safely concurrent (although it doesn't protect
some things such as a user registering multiple times).

Endpoints
---------
`/register-user/name/<name>/email/<email>/password/<password>`

`/register-device/name/<name>/device/<device>` (requires authentication)

`/store/name/<name>/device/<device>/method/<method>/url/<url>` (requires authentication)
`url` obviously must be urlencoded

`/list`
Return a JSON object of all log entries -- pretty dumb for lots of objects
but it gets the point across

`/summarize`
Returns the contents of all the counters (user counts, device counts, method/url counts)


Running
-------
Have a riak instance (2.0+) running locally. `db.sh` contains some setup: mostly just
creating buckets and such. `populate.sh` will populate with some dumb test data.

Example output of `/summarize` after running some data through it:

{
    "Device ID": {
        "dev-1": 6,
        "dev-2": 2,
        "dev-3": 2,
        "dev-4": 4
    },
    "Method/URL": {
        "get:http://google.com": 2,
        "get:http://google.com/index.html": 1,
        "get:http://google.com/stuff.html": 1,
        "get:http://what.com": 1,
        "put:http://google.com": 1,
        "put:http://what.com": 1
    },
    "Name": {
        "user-1": 6,
        "user-2": 2,
        "user-3": 2,
        "user-4": 4
    }
}
