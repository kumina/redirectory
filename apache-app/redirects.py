from mod_python import util
import os
import random
import memcache
import sqlite3
import re
import base64

__dir__ = os.path.dirname(__file__)


# Copied from http://stackoverflow.com/a/1630350/1357013
def lookahead(iterable):
    """Pass through all values from the given iterable, augmented by the
    information if there are more values to come after the current one
    (True), or if it is the last value (False).
    """
    # Get an iterator and pull the first value.
    it = iter(iterable)
    last = next(it)
    # Run the iterator to exhaustion (starting from the second value).
    for val in it:
        # Report the *previous* value (more to come).
        yield last, True
        last = val
    # Report the last value.
    yield last, False


def handler(req):
    # Path to the redirects database
    db = os.path.join(__dir__, 'redirects.sql')
    # Memcache connection
    mc = memcache.Client(['127.0.0.1:11211'], debug=0)
    # Make sure we have a valid timestamp
    last_mtime = mc.get('redirector_last_mtime')
    if not last_mtime:
        db_stat = os.stat(db)
        last_mtime = db_stat.st_mtime
        mc.set('redirector_last_mtime', last_mtime)
    # In 1% of the time, we want to stat the db, to see if we need to
    # invalidate the current cache.
    x = random.randint(0, 100)
    if x < 1:
        db_stat = os.stat(db)
        if db_stat.st_mtime > last_mtime:
            last_mtime = db_stat.st_mtime
            # This will actually invalidate the cache, since we use the
            # last_mtime as part of the key. Memcache does not support removal
            # of namespaces, but it will phase out keys that are no longer
            # requested, so this is a semi-clean way to invalidate the cache.
            mc.set('redirector_last_mtime', last_mtime)
    # Get the actual URL requested, lowercase the domain as that always works.
    host = req.hostname.lower()
    path = req.unparsed_uri
    # Remove any 'www.' that's added in front of the host
    if host[:4] == 'www.':
        host = host[4:]
    # Encode this information.
    encoded_request = base64.b64encode(host + path)
    # Create the memcache key. The last_mtime is included so we can easily
    # switch to a new generation of redirects when the database has changed.
    mc_hash_key = "redirector_" + str(last_mtime) + "_" + encoded_request
    # Request the key from memcache.
    redirect = mc.get(mc_hash_key)
    # Check whether we got a result.
    if not redirect:
        # Alas, nothing in memcache yet.
        # Setup a database connection, this actually opens the file.
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        # Get all data concerning this domain.
        cur.execute(("SELECT * FROM redirects " +
                     "WHERE domain = '%s' " +
                     "ORDER BY ordering") % host)
        # Get the results (rowcount doesn't work with sqlite)
        result = cur.fetchall()
        if len(result) == 0:
            # Unknown domain got requested! Redirect to default. But what is
            # the default?
            cur.execute("SELECT dest FROM redirects " +
                        "WHERE domain = 'default'")
            result = cur.fetchone()
            redirect = result[0]
        elif len(result) == 1:
            # We got exactly one result, great! That makes the redirect easy.
            # Ignore the path and ordering, just redirect to dest.
            redirect = result[0]['dest']
        else:
            # Ok, we got multiple results. This makes things a little more
            # elaborate, but we can deal with that. Loop through the results.
            for res, more in lookahead(result):
                # Match the path in the result to the path in the request
                if more and re.match(res['path'], path):
                    redirect = res['dest']
                    break
                elif not more:
                    # This is the last iteration, always redirect to dest.
                    redirect = res['dest']
        # Cache the result!
        mc.set(mc_hash_key, redirect)
    # Actually perform the redirection.
    util.redirect(req, str(redirect), permanent=True)
