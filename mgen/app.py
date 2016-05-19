"""
MGEN: Command line interface and entry point
"""
import os
import optparse
import logging
import datetime

import tornado.ioloop
import tornado.web

import mgen.web

logging.basicConfig(level=mgen.web.MGEN_LOG_LEVEL)

log = logging.getLogger(__name__)

log.info("Starting new session on {0}".format(datetime.datetime.now().isoformat()))
app = mgen.web.make_app()
app.listen(port=mgen.web.MGEN_PORT, address=mgen.web.MGEN_ADDR)
tornado.ioloop.IOLoop.current().start()
log.info("Session stopped on {0}".format(datetime.datetime.now().isoformat()))