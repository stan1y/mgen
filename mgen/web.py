"""
WSGI config for MGEN.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
os.environ.setdefault("MGEN_DEFINES", "mgen.defines")

import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()