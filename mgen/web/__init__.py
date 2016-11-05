"""
Web intefaces for MGEN.

It exposes module level make_app function for mgen.app module
"""
import os
import json
import logging

import tornado.web
import mgen.model
import mgen.error
import mgen.util
import sqlalchemy.orm.exc


log = logging.getLogger(__name__)


class BaseRequestHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        prn = self.get_secure_cookie("mgen-auth-principal")
        if prn:
            return json.loads(prn.decode('utf-8'))
        return None
        
    def get_profile(self):
        profile = self.get_secure_cookie("mgen-auth-profile")
        if profile:
            return json.loads(profile.decode('utf-8'))
        return None
    
    @property
    def current_profile(self):
        profile_info = self.get_profile()
        return mgen.model.session().query(mgen.model.Profile).filter_by(email=profile_info['email']).first()