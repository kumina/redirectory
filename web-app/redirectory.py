import sqlite3
import re
import web


urls = (
    '/', 'index'
)

class index:
    render = web.template.render('templates')
    db = sqlite3.connect('redirects.py')

    def GET(self):
        return "Hello, world!"

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
