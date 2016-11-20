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
import urllib.parse

import tornado.ioloop
import tornado.web

import mgen
import mgen.web.ui
import mgen.web.api
import mgen.web.auth

import mgen.model


log = logging.getLogger('mgen.app')


def webdir():
    return os.path.abspath(os.path.dirname(mgen.web.__file__))

def run():
    '''Run MGEN web insterface application'''
    
    parser = optparse.OptionParser()
    parser.add_option("--debug", action="store_true", default=False, help="Enable debug output.")
    parser.add_option("--logfile", default='mgenweb.log', help="Application log file path.")
    parser.add_option("--host", default="127.0.0.1", help = "IPAddress to listen on.")
    parser.add_option("--port", default=3000, type="int", help = "Local port to listen on.")
    parser.add_option("--cookie-secret", help="Cookie secret to use. Randomized by default")
    parser.add_option("--public-base-uri", default="http://127.0.0.1:3000", help="Public hostname to use for redirects.")
    parser.add_option("--dsn", help="Database full connection string.")
    
    (options, args) = parser.parse_args()
    mgen.configure_log(options.logfile,
                       debug=options.debug,
                       console=True)
    
    log.info("new session {0}:{1} on {2}".format(
        options.host,
        options.port,
        datetime.datetime.now().isoformat()))
        
    mgen.read_options()
    
    # setup debug database in memory
    if not options.dsn and options.debug:
        options.dsn = "sqlite:///mgen-debug.sqlite"
        
    # setup database connection        
    mgen.model.setup(options.dsn)
    
    # generate cookie secret
    if not options.cookie_secret and not options.debug:
        log.error("no cookie secret given. cannot run...")
        return 1
        
    if options.debug and not options.cookie_secret:
        options.cookie_secret = 'the-secret-for-cookies'
    
    # parse public base url
    public_base_uri = urllib.parse.urlsplit(options.public_base_uri)
    
    # setup tornado application
    app = tornado.web.Application(
    	[
    	    # Authentication endpoints
    	    
    	    (r"/login",                        mgen.web.auth.Login),
    	    (r"/logout",                       mgen.web.auth.Logout),
    		(r"/auth/google",                  mgen.web.auth.GoogleOAuth2Login),
    		
    		# API Endpoints
    		
    		(r"/api/profiles",                        mgen.web.api.Profiles),
    		(r"/api/projects",                        mgen.web.api.Projects),
    		(r"/api/projects/(?P<project_id>[0-9a-zA-Z]+)",  mgen.web.api.Projects),
    		(r"/api/templates",                       mgen.web.api.Templates),
    		(r"/api/templates/(?P<template_id>[0-9a-zA-Z]+)", mgen.web.api.Templates),
    		(r"/api/pages",                           mgen.web.api.Pages),
    		(r"/api/pages/(?P<page_id>[0-9a-zA-Z]+)",     mgen.web.api.Pages),
    		(r"/api/items",                           mgen.web.api.Items),
    		(r"/api/items/(?P<item_id>[0-9a-zA-Z]+)",     mgen.web.api.Items),
    		
    		# UI Endpoints
    		
    		(r"/",                                    mgen.web.ui.Overview),
    		
    		(r"/preview/template",                    mgen.web.ui.TemplatePreview),
    		
    		(r"/project/(?P<project_id>[0-9a-zA-Z]+)",       mgen.web.ui.Project),
    		(r"/template/(?P<template_id>[0-9a-zA-Z]+)",      mgen.web.ui.Template),
    		(r"/page/(?P<page_id>[0-9a-zA-Z]+)",          mgen.web.ui.Page),
    	],
    	
    	
    	# Google OAuth settings
    	google_oauth={
    	    "key": "664409134549-6eotcrte0qqhu4l9anaq57k5ua4a5a4n.apps.googleusercontent.com",
    	    "secret": "idwzGRRJjuGlv5W4G2tpicl4",
    	    "redirect_uri": public_base_uri._replace(path="/auth/google").geturl()
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
    log.debug("webdir: %s" % webdir())
    tornado.ioloop.IOLoop.current().start()
    log.info("session stopped on {0}".format(datetime.datetime.now().isoformat()))
    
    return 0
    
if __name__ == '__main__':
    sys.exit(run())