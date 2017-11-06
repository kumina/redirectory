# Redirectory - redirect with ease

This is a simple script that allows Apache to read a database with a mod\_python script to determine where a certain
domain should redirect to. The database is a simple SQLite database.

This project consists of two parts, the Apache script and vhost config and the web.py application to ease the input
of data. Both can be run separately, but the SQLite database from the web.py script should then be copied over to the
Apache webserver. Using the web.py script is optional, if you prefer to manually enter data (or write your own app for
it) into SQLite, you're welcome, of course.

## Database schema

```
CREATE TABLE redirects (
	gid INTEGER PRIMARY KEY ASC,
	domain TEXT,
	ordering INTEGER,
	path TEXT,
	dest TEXT
);

CREATE INDEX domain_in_redirects ON redirects (domain);
```

 * `gid` is just a global id, should be MAX(gid)+1
 * `domain` is the domain for which this rule counts, something like `example.com`
 * `ordering` is an integer denoting the order in which the paths should be matched, first one that matches, wins
 * `path` is the URI to match on, should always start with a `/`
 * `dest` is the destination to which a client should be redirected

## Execution workflow

This should help in debugging:

 1. Open the sqlite database
 1. Get all records for the requested domain out of the database, sorted by the `ordering` column, ascending.
   * If the URL start with `www.`, that part is removed
   * If there are no records, redirect to the `default` entry
 1. If there's just one record, immediately redirect to that destination, without checking path, script ends here
 1. Interpret each path as a regex and match it to the requested path
   * If a match is found, redirect to the associated destination, script ends here
 1. On the last record, always redirect to the associated path, script ends here

## Things to keep in mind

 * It's never necessary to add both `example.com` and `www.example.com` in the database, the `www.` variant is
   automatically assumed as well. (The `www.` part is actually removed from the requested URL before checking.)
 * An entry with `domain` "default" should be entered which contains a default destination for unmatched domains.
 * The domains are case-insensitive, but the paths aren't. Also, there's currently no way to quickly make a check
   case-insensitive (as with the `i` option in normal regex), so if case is expected to be important, you need to
   use the `[aA][bB]` trick.
 * Redirects are always of the permanent kind (301).

## Notes

 * `ordering` is used because `order` is a reserved keyword in sqlite and I couldn't come up with anything better.
