"""
Web intefaces for MGEN.

It exposes module level make_app function for mgen.app module
"""
import os
import json
import logging
import functools

import tornado.web


log = logging.getLogger(__name__)


class BaseRequestHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        prn = self.get_secure_cookie("mgen-auth-principal")
        if prn:
            return json.loads(prn)
        return None
        
    def get_current_user_profile(self):
        profile = self.get_secure_cookie("mgen-auth-profile")
        if profile:
            return json.loads(profile)
        return None
    
    @property
    def current_profile(self):
        return self.get_current_user_profile()

def jsonify(method):
    """Decorate methods with this to output valid JSON data."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        answer = method(self, *args, **kwargs)
        if answer:
            if self._finished:
                log.warn('trying to write JSON on finished request.')
            else:
                self.set_header('Content-Type', 'application/json')
                #self.write(json.dumps(answer, cls=DecimalEncoder))
                self.write(json.dumps(answer))
    return wrapper