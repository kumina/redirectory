import collections
import os
import re
import sqlite3


class RegexBasedRedirector:
    """HTTP redirect URL lookup that is backed by a SQLite database."""

    def __init__(self, db_path):
        self._db_path = db_path
        self._last_update_time = 0

    def _sync_from_database(self):
        """Discards the existing patterns and loads new ones from disk."""
        db = sqlite3.connect(self._db_path)
        cursor = db.cursor()
        self._patterns = collections.defaultdict(list)
        for domain, path, dest in cursor.execute('SELECT domain, path, dest '
                                                 'FROM redirects '
                                                 'ORDER BY ordering, gid'):
            self._patterns[domain].append((re.compile(path), str(dest)))

    def _sync_from_database_if_outdated(self):
        """Only does a sync if the database is newer than what we have."""
        db_mtime = os.stat(self._db_path).st_mtime
        if self._last_update_time < db_mtime:
            self._sync_from_database()
            # TODO(ed): Enable this when using Python >= 3.2.
            # self._lookup.cache_clear()
            self._last_update_time = db_mtime

    # TODO(ed): Enable this when using Python >= 3.2.
    # @functools.lru_cache(2048)
    def _lookup(self, domain, unparsed_uri):
        if domain[:4] == 'www.':
            domain = domain[4:]
        if domain not in self._patterns:
            domain = 'default'
        for path, dest in self._patterns[domain]:
            if path.match(unparsed_uri):
                return dest
            fallback_dest = dest
        return fallback_dest

    def get_target(self, domain, unparsed_uri):
        """Translate a URL to a new target URL."""
        self._sync_from_database_if_outdated()
        return self._lookup(domain, unparsed_uri)


redirector = RegexBasedRedirector(
    os.path.join(os.path.dirname(__file__), 'redirects.sql'))


def handler(req):
    from mod_python import util
    return util.redirect(
        req,
        redirector.get_target(req.hostname, req.unparsed_uri),
        permanent=True)
