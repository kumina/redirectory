from mod_python import apache
import sqlite3
import re


def handler(req):
    conn = sqlite3.connect('redirects.sql')
    #req.content_type = 'text/plain'
    #req.write("The request: %s\n" % req.the_request)
    #req.write("Host: %s\n" % req.hostname)
    #req.write("URI: %s\n" % req.uri)
    #req.write("Filename: %s\n" % req.filename)
    #req.write("Unparsed URI: %s\n" % req.unparsed_uri)
    host = req.hostname.lower()
    path = req.unparsed_uri
    mc_hash_key = "redirector_"+host+path
    print mc_hash_key

