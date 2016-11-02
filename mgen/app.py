"""
MGEN: Web application lancher
"""
import os
import sys
import optparse
import logging
import datetime
import random
import string

import tornado.ioloop
import tornado.web

import mgen.web.ui
import mgen.web.api
import mgen.web.auth

def webdir():
    return os.path.abspath(os.path.dirname(mgen.web.__file__))

def run():
    '''Run MGEN web insterface application'''
    
    parser = optparse.OptionParser()
    parser.add_option("--debug", action="store_true", default=False, help="Enable debug output.")
    parser.add_option("--host", default="127.0.0.1", help = "IPAddress to listen on.")
    parser.add_option("--port", default=3000, type="int", help = "Local port to listen on.")
    parser.add_option("--cookie-secret", help="Cookie secret to use. Randomized by default")
    parser.add_option("--public-base-uri", default="http://127.0.0.1:3000", help="Public hostname to use for redirects.")
    
    (options, args) = parser.parse_args()
    if options.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    log = logging.getLogger(__name__)
    
    # generate cookie secret
    if not options.cookie_secret and options.debug:
        options.cookie_secret = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        log.debug('generated cookie secret: %s' % options.cookie_secret)
    
    # setup tornado application
    app = tornado.web.Application(
    	[
    	    (r"/login",                 mgen.web.ui.LoginForm),
    		(r"/auth/google",           mgen.web.auth.GoogleOAuth2LoginHandler),
    		
    		(r"/",                      mgen.web.ui.Dashboard)
    	],
    	
    	
    	# Google OAuth settings
    	google_oauth={
    	    "key": "664409134549-6eotcrte0qqhu4l9anaq57k5ua4a5a4n.apps.googleusercontent.com",
    	    "secret": "idwzGRRJjuGlv5W4G2tpicl4",
    	    "redirect_uri": options.public_base_uri + "/auth/google",
    	},
    	
    	# Tornado Application Settings
	    debug=options.debug,
	    login_url="/login",
	    cookie_secret=options.cookie_secret,
	    #autoescape=True,
	    template_path=os.path.join(webdir(), "templates"),
	    
	    # Static files
	    static_hash_cache=False if options.debug else True,
	    static_path=os.path.join(webdir(), "static")
	    
	    )
    
    app.listen(options.port)
    
    # launch app
    log.info("new session {0}:{1} on {2}".format(
        options.host,
        options.port,
        datetime.datetime.now().isoformat()))
    log.debug("webdir=%s" % webdir())
    tornado.ioloop.IOLoop.current().start()
    log.info("session stopped on {0}".format(datetime.datetime.now().isoformat()))
    
    return 0
    
if __name__ == '__main__':
    sys.exit(run())