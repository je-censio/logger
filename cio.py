from functools import wraps
from collections import defaultdict
import urllib
import json
import requests
import uuid
import hashlib

import riak
import riak.datatypes
from flask import Flask, request, Response
app = Flask(__name__)

def authed(f):
    """
    Very simple HTTP basic authentication. Not really proper for a live API
    but it's simple to implement and allows simple access with curl 
    (e.g., we don't need to go construct a hash of the query parameters or 
    whatever)
    """
    @wraps(f)
    def dec(*args, **kwargs):
        failed_auth = Response("Auth required", 401,
                               {'WWW-Authenticate': 'Basic realm="Login required"'})
        if not request.authorization:
            return failed_auth
        auth = request.authorization
        if not authenticate(auth.username, auth.password):
            return failed_auth
        return f(*args, authed_as=auth.username, **kwargs)
    return dec


def authenticate(user_id, password):
    """
    Do a simple lookup by user_id (name, really) and return True
    if the given password successfully salts and hashes.
    """
    api = '/buckets/Users/keys/%s' % user_id
    obj = riak_get(api)
    hashed = hashlib.sha1(obj['salt'] + password).hexdigest()
    if hashed == obj['hashed']:
        return True
    return False
    

def riak_post(path, body):
    """
    Do a simple POST to riak. Raises an exception on failure which will
    conveniently cause Flask to 500.
    """
    url = app.config['db'] + path
    resp = requests.post(url, data=body, headers={'Content-Type': 'application/json'})
    if resp.status_code > 299:
        raise IOError("Riak failed: %s" % resp.text)


def riak_get(path):
    """
    Do a simple GET to riak. Assumes the response is JSON.
    """
    url = app.config['db'] + path
    resp = requests.get(url, headers={'Accept': 'application/json'})
    if resp.status_code > 299:
        raise IOError("Riak failed: %s" % resp.text)
    return json.loads(resp.text)


@app.route('/register-user/name/<user_id>/email/<email>/password/<password>')
def register_user(user_id, email, password):
    """
    Stores a user in the database. Salts and hashes the password for sanity --
    a straightforward homegrown uuid + sha1 that we probably wouldn't actually
    use in production, but it gets the point across.
    """
    salt = uuid.uuid1().hex
    hashed = hashlib.sha1(salt + password).hexdigest()
    data = json.dumps(dict(user_id=user_id, email=email, hashed=hashed, salt=salt))
    api = '/buckets/Users/keys/%s' % user_id
    riak_post(api, data)
    return 'okay'


@app.route('/register-device/user/<user_id>/device/<device_id>')
@authed
def register_device(user_id, device_id, authed_as):
    """
    Simply add a row to the Devices bucket that maps the given device ID to the given user.
    Requires that the authed user be the same as the user claiming the device.
    """
    if user_id != authed_as:
        return Response("Unauthorized", 401)
    data = json.dumps(dict(user_id=user_id, device_id=device_id))
    api = '/buckets/Devices/keys/%s' % device_id
    riak_post(api, data)
    return 'okay'


@app.route('/store/user/<user_id>/device/<device_id>/method/<http_method>/url/<path:url>')
@authed
def store(user_id, device_id, http_method, url, authed_as):
    """
    Stores the event in the Logs bucket and also updates various counters.
    Requires that the HTTP call be authed to the referenced user.
    """
    if user_id != authed_as:
        return Response("Unauthorized", 401)
    to_increment = ['user_%s' % user_id, 'device_%s' % device_id,
                   'http_%s_%s' % (http_method, urllib.quote(url, safe=''))]
    for counter in to_increment:
        # increment each of the counters for users, devices, and http method/url pairs
        api = '/types/counters/buckets/counters/datatypes/%s' % counter
        riak_post(api, '1')
    data = json.dumps(dict(user_id=user_id, device_id=device_id,
                           http_method=http_method, url=url))
    # riak isn't a great choice for storing log-like data, but let's use
    # it just to keep this thing simple. Generate a random key and shove
    # the whole row in.
    key = uuid.uuid1().hex
    api = '/buckets/Logs/keys/%s' % (key)
    riak_post(api, data)
    return 'okay'


@app.route('/list')
def list():
    """
    Simply return a list of everything in the Logs bucket. This is obviously
    quick-n-dirty in the sense that returning one huge JSON object is very dumb
    and iterating buckets in Riak is pretty slow.
    """
    keys = riak_get('/buckets/Logs/keys?keys=true')
    lines = []
    for key in keys['keys']:
        api = '/buckets/Logs/keys/%s' % key
        item = riak_get(api)
        lines.append(item)
    return json.dumps(lines)


def deconvolve_counter_key(key):
    """
    Do some tom-foolery to retrieve the item type and specific item name
    that the counter key is storing. The maxsplit stuff is so URLs, names
    and devices can contain underscores.
    """
    if key.startswith('http'):
        method, url = key.split('_', 2)[1:]
        return ('Method/URL', "%s:%s" % (method, url))
    elif key.startswith('user'):
        return ('Name', key.split('_', 2)[1])
    elif key.startswith('device'):
        return ('Device ID', key.split('_', 2)[1])
    else:
        raise ValueError("Don't know how to handle key %s" % key)


@app.route('/summarize')
def summarize():
    """
    Look up all the counters and return a dict summarizing their contents.
    """
    keys = riak_get('/types/counters/buckets/counters/keys?keys=true')
    totals = defaultdict(dict)
    for key in keys['keys']:
        api = '/types/counters/buckets/counters/datatypes/%s' % urllib.quote(key, safe='')
        count = riak_get(api)['value']
        family, index = deconvolve_counter_key(key)
        totals[family][index] = count
    return json.dumps(totals)


if __name__ == '__main__':
    app.config.update(db='http://127.0.0.1:8098')
    app.run(debug=True, port=8080)

    
